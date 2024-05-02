#!.venv/bin/python3
import binascii
import json
import logging
import os
import argparse
import queue
import subprocess
import sys
import mailbox
import base64
import threading
from Crypto.PublicKey import RSA

sys.path.insert(0, "dkimpy")
import dkimpy.dkim as dkim
from dataclasses import dataclass

# https://russell.ballestrini.net/quickstart-to-dkim-sign-email-with-python/


def decode_dkim_header_field(dkimData: str):
    # decode a DKIM-Signature header field such as "v=1; a=rsa-sha256; d=example.net; s=brisbane;"
    # to a dictionary such as {'v': '1', 'a': 'rsa-sha256', 'd': 'example.net', 's': 'brisbane'}
    tagValuePairStrings = list(map(lambda x: x.strip(), dkimData.split(';')))
    res: dict[str, str] = {}
    for s in tagValuePairStrings:
        if not s:
            continue
        key, value = s.split('=', 1)
        key = key.strip()
        value = value.strip()
        res[key] = value
    return res


@dataclass(frozen=True)
class Dsp:
    domain: str
    selector: str


@dataclass
class MsgInfo:
    signedData: bytes
    signature: bytes


dsp_queue: "queue.Queue[tuple[Dsp, MsgInfo, MsgInfo]]" = queue.Queue()


def call_solver_and_process_result(dsp: Dsp, msg1: MsgInfo, msg2: MsgInfo, loglevel: int, output_format: str):
    logging.info(f'processing {dsp}')
    cmd = [
        "docker",
        "run",
        "--rm",
        "--mount",
        f"type=bind,source={os.getcwd()},target=/app",
        "--workdir=/app",
        "sagemath:latest",
        "sage",
        "sigs2rsa.py",
        "--loglevel",
        str(loglevel),
    ]
    data_parameters = [
        base64.b64encode(msg1.signedData).decode('utf-8'),
        base64.b64encode(msg1.signature).decode('utf-8'),
        base64.b64encode(msg2.signedData).decode('utf-8'),
        base64.b64encode(msg2.signature).decode('utf-8'),
    ]
    logging.debug(f'+ {" ".join(cmd)} (...data...)')

    output = subprocess.check_output(cmd + data_parameters)
    data = json.loads(output)
    n = int(data['n_hex'], 16)
    e = int(data['e_hex'], 16)
    if (n < 2):
        logging.info(f'no large GCD found for {dsp}')
        return
    try:
        logging.info(f'found large GCD for {dsp}')
        rsa_key = RSA.construct((n, e))
        if output_format == 'PEM':
            keyPEM = rsa_key.exportKey(format='PEM')
            print('PEM:', keyPEM.decode('utf-8'))
        else:
            keyDER = rsa_key.exportKey(format='DER')
            keyDER_base64 = binascii.b2a_base64(keyDER, newline=False).decode('utf-8')
            print('DER:', keyDER_base64)
        sys.stdout.flush()
    except ValueError as e:
        logging.error(f'ValueError: {e}')
        return


def read_and_resolve_worker(loglevel: int):
    while True:
        dsp, msg1, msg2 = dsp_queue.get()
        call_solver_and_process_result(dsp, msg1, msg2, loglevel, 'DER')
        dsp_queue.task_done()


def solve_msg_pairs(results: dict[Dsp, list[MsgInfo]], threads: int, loglevel: int):
    results = {dsp: msg_infos for dsp, msg_infos in results.items() if len(msg_infos) >= 2}
    logging.info(f'solving {len(results.items())} message pairs')
    for [dsp, msg_infos] in results.items():
        if len(msg_infos) > 1:
            msg1 = msg_infos[0]
            msg2 = msg_infos[1]
            dsp_queue.put((dsp, msg1, msg2))
    logging.debug(f'starting {threads} threads')
    for _i in range(threads):
        t_in = threading.Thread(target=read_and_resolve_worker, daemon=True, args=(loglevel, ))
        t_in.start()
    dsp_queue.join()


class ProgramArgs(argparse.Namespace):
    mbox_file: str
    loglevel: int
    threads: int


def main():
    parser = argparse.ArgumentParser(description='extract domains and selectors from the DKIM-Signature header fields in an mbox file and output them in TSV format')
    parser.add_argument('mbox_file')
    parser.add_argument('--debug', action="store_const", dest="loglevel", const=logging.DEBUG, default=logging.INFO)
    parser.add_argument('--threads', type=int, default=1)
    args = parser.parse_args(namespace=ProgramArgs)

    logging.root.name = os.path.basename(__file__)
    logging.basicConfig(level=args.loglevel, format='%(name)s: %(levelname)s: %(message)s')

    logging.info(f'processing {args.mbox_file}')
    results: dict[Dsp, list[MsgInfo]] = {}
    message_counter = 0
    mb = mailbox.mbox(args.mbox_file, create=False)
    logging.info(f'loaded {args.mbox_file}')
    for message in mb:
        message_counter += 1
        logging.info(f'processing message {message_counter}')
        dkimSignatureFields = message.get_all('DKIM-Signature')
        if not dkimSignatureFields:
            logging.info('INFO: no DKIM-Signature header field found, skipping')
            continue
        for field in dkimSignatureFields:
            tags = decode_dkim_header_field(field)
            domain = tags['d']
            selector = tags['s']
            signAlgo = tags['a']
            if signAlgo != 'rsa-sha256' and signAlgo != 'rsa-sha1':
                logging.warning(f'skip signAlgo that is not rsa-sha256 or rsa-sha1: {signAlgo}')
                continue
            bodyHash = tags.get('bh', None)
            if not bodyHash:
                logging.warning('body hash tag (bh) not found, skipping')
                continue
            bodyLen = tags.get('l', None)
            if bodyLen:
                logging.warning('body length tag (l) not supported yet, skipping')
                continue
            signature_tag = tags.get('b', None)
            if not signature_tag:
                logging.warning('signature tag (b) not found, skipping')
                continue
            signature_base64 = ''.join(list(map(lambda x: x.strip(), signature_tag.splitlines())))
            signature = base64.b64decode(signature_base64)

            infoOut: dict[str, bytes] = {}
            try:
                d = dkim.DKIM(str(message).encode(), debug_content=True)
            except UnicodeEncodeError as e:
                logging.warning(f'UnicodeEncodeError: {e}')
                continue

            try:
                d.verify(0, infoOut=infoOut)  # type: ignore
            except dkim.ValidationError as e:
                logging.warning(f'ValidationError: {e}')
                continue
            body_hash_mismatch = infoOut.get('body_hash_mismatch', False)
            if body_hash_mismatch:
                logging.info('body hash mismatch')

            try:
                signed_data = infoOut['signed_data']
            except KeyError:
                logging.error(f'signed_data not found, infoOut: {infoOut}')
                sys.exit(1)

            dsp = Dsp(domain, selector)
            logging.info(f'register message info for {dsp}')
            msg_info = MsgInfo(signed_data, signature)
            if not dsp in results:
                results[dsp] = []
            results[dsp].append(msg_info)

    solve_msg_pairs(results, args.threads, args.loglevel)


if __name__ == '__main__':
    main()
