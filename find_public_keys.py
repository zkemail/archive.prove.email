#!.venv/bin/python3
import binascii
import json
import logging
import os
import argparse
import pickle
import queue
import subprocess
import sys
import mailbox
import base64
import threading
from Crypto.PublicKey import RSA
from lib.util import ProgressReporter
from dataclasses import dataclass

sys.path.insert(0, "dkimpy")
import dkimpy.dkim as dkim

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


def call_solver_and_process_result(dsp: Dsp, msg1: MsgInfo, msg2: MsgInfo, loglevel: int):
    logging.info(f'searching for public key for {dsp}')
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
    logging.debug(" ".join(cmd) + ' [... data parameters ...]')

    output = subprocess.check_output(cmd + data_parameters)
    data = json.loads(output)
    n = int(data['n_hex'], 16)
    e = int(data['e_hex'], 16)
    if (n < 2):
        logging.info(f'no public key found for {dsp}')
        return
    try:
        logging.info(f'found public key for {dsp}')
        rsa_key = RSA.construct((n, e))
        keyDER = rsa_key.exportKey(format='DER')
        keyDER_base64 = binascii.b2a_base64(keyDER, newline=False).decode('utf-8')
        print(f'{dsp.domain}\t{dsp.selector}\tk=rsa; p={keyDER_base64}')
        sys.stdout.flush()
    except ValueError as e:
        logging.error(f'ValueError: {e}')
        return


def read_and_resolve_worker(loglevel: int):
    while True:
        logging.info(f'message pairs left: {dsp_queue.qsize()}')
        dsp, msg1, msg2 = dsp_queue.get()
        call_solver_and_process_result(dsp, msg1, msg2, loglevel)
        dsp_queue.task_done()


def solve_msg_pairs(signed_messages: dict[Dsp, list[MsgInfo]], filter_domain: str, threads: int, loglevel: int):
    signed_messages = {dsp: msg_infos for dsp, msg_infos in signed_messages.items() if len(msg_infos) >= 2}
    signed_messages = {dsp: msg_infos for dsp, msg_infos in signed_messages.items() if not filter_domain or dsp.domain == filter_domain}

    logging.info(f'searching for public key for {len(signed_messages.items())} message pairs')
    for [dsp, msg_infos] in signed_messages.items():
        if len(msg_infos) > 1:
            msg1 = msg_infos[0]
            msg2 = msg_infos[1]
            dsp_queue.put((dsp, msg1, msg2))
    logging.info(f'starting {threads} threads')
    for _i in range(threads):
        t_in = threading.Thread(target=read_and_resolve_worker, daemon=True, args=(loglevel, ))
        t_in.start()
    dsp_queue.join()


@dataclass
class Statistics:
    total: int = 0
    missing_dkim_signature: int = 0
    non_rsa_sign_algo: int = 0
    missing_body_hash: int = 0
    body_hash_mismatch: int = 0
    body_length_tag_not_supported: int = 0
    missing_signature_tag: int = 0
    unicode_error: int = 0
    validation_error: int = 0


def parse_mbox_file(mbox_file: str) -> dict[Dsp, list[MsgInfo]]:
    results: dict[Dsp, list[MsgInfo]] = {}
    message_index = 0
    logging.info(f'loading {mbox_file}')
    mb = mailbox.mbox(mbox_file, create=False)
    number_of_messages = len(mb)
    progressReporter = ProgressReporter(number_of_messages, 0)
    statistics = Statistics()
    logging.info(f'processing {len(mb)} messages')
    for message in mb:
        message_index += 1
        progressReporter.increment()
        dkimSignatureFields = message.get_all('DKIM-Signature')
        if not dkimSignatureFields:
            statistics.missing_dkim_signature += 1
            continue
        for field in dkimSignatureFields:
            tags = decode_dkim_header_field(field)
            domain = tags['d']
            selector = tags['s']
            signAlgo = tags['a']
            if signAlgo != 'rsa-sha256' and signAlgo != 'rsa-sha1':
                statistics.non_rsa_sign_algo += 1
                continue
            bodyHash = tags.get('bh', None)
            if not bodyHash:
                statistics.missing_body_hash += 1
                continue
            bodyLen = tags.get('l', None)
            if bodyLen:
                statistics.body_length_tag_not_supported += 1
                continue
            signature_tag = tags.get('b', None)
            if not signature_tag:
                statistics.missing_signature_tag += 1
                continue
            signature_base64 = ''.join(list(map(lambda x: x.strip(), signature_tag.splitlines())))
            signature = base64.b64decode(signature_base64)

            infoOut: dict[str, bytes] = {}
            try:
                d = dkim.DKIM(str(message).encode(), debug_content=True)
            except UnicodeEncodeError as e:
                logging.error(f'message {message_index}: UnicodeEncodeError: {e}')
                statistics.unicode_error += 1
                continue

            try:
                d.verify(0, infoOut=infoOut)  # type: ignore
            except dkim.ValidationError as e:
                logging.error(f'message {message_index}: ValidationError: {e}')
                statistics.validation_error += 1
                continue
            body_hash_mismatch = infoOut.get('body_hash_mismatch', False)
            if body_hash_mismatch:
                statistics.body_hash_mismatch += 1

            try:
                signed_data = infoOut['signed_data']
            except KeyError:
                logging.error(f'signed_data not found, infoOut: {infoOut}')
                sys.exit(1)

            dsp = Dsp(domain, selector)
            msg_info = MsgInfo(signed_data, signature)
            if not dsp in results:
                results[dsp] = []
            results[dsp].append(msg_info)
            statistics.total += 1
    logging.info(f'processed {message_index} messages')
    logging.info(f'statistics: {statistics}')
    return results


def load_signed_data(datasig_files: list[str]):
    result: dict[Dsp, list[MsgInfo]] = {}
    for f in datasig_files:
        file_load_result = pickle.load(open(f, 'rb'))
        for dsp, msg_infos in file_load_result.items():
            if not dsp in result:
                result[dsp] = []
            result[dsp].extend(msg_infos)
    return result


class ProgramArgs(argparse.Namespace):
    load_mbox: bool
    mbox_files: list[str] | None
    datasig_files: list[str] | None
    filter_domain: str
    loglevel: int
    threads: int


def main():
    parser = argparse.ArgumentParser(description='extract message data together with signatures from the DKIM-Signature header field of each message in an mbox file,\
            and try to find the RSA public key from pairs of messages signed with the same key',
                                     allow_abbrev=False)
    parser.add_argument('--mbox-files', help='load data from mbox files and save to corresponding .mbox.datasig', type=str, nargs='*')
    parser.add_argument('--datasig-files', help='find public keys from the data in one or many .datasig files', type=str, nargs='*')
    parser.add_argument('--filter-domain', help='only process messages with this domain', type=str)
    parser.add_argument('--debug', action="store_const", dest="loglevel", const=logging.DEBUG, default=logging.INFO, help='enable debug logging')
    parser.add_argument('--threads', type=int, default=1, help='number of threads to use for solving')
    args = parser.parse_args(namespace=ProgramArgs)

    logging.root.name = os.path.basename(__file__)
    logging.basicConfig(level=args.loglevel, format='%(name)s: %(levelname)s: %(message)s')

    if args.mbox_files:
        for mbox_file in args.mbox_files:
            results = parse_mbox_file(mbox_file)
            pickle.dump(results, open(f'{mbox_file}.datasig', 'wb'))
            logging.info(f'results saved to {mbox_file}.datasig')
    elif args.datasig_files:
        signed_data = load_signed_data(args.datasig_files)
        solve_msg_pairs(signed_data, args.filter_domain, args.threads, args.loglevel)
    else:
        parser.error('no action specified')


if __name__ == '__main__':
    main()
