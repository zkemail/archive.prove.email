import logging
import os
import argparse
import pickle
import sys
import mailbox
import base64
from common import Dsp, MsgInfo
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


@dataclass
class Statistics:
    total: int = 0
    missing_dkim_signature: int = 0
    non_rsa_sign_algo: int = 0
    missing_body_hash: int = 0
    body_hash_mismatch: int = 0
    missing_signature_tag: int = 0
    unicode_error: int = 0
    validation_error: int = 0


def parse_mbox_file(filepath: str) -> dict[Dsp, list[MsgInfo]]:
    results: dict[Dsp, list[MsgInfo]] = {}
    filename = os.path.basename(filepath)
    logging.info(f'loading {filepath}')
    mb = mailbox.mbox(filepath, create=False)
    number_of_messages = len(mb)
    progressReporter = ProgressReporter(number_of_messages, 0)
    statistics = Statistics()
    logging.info(f'processing {len(mb)} messages')
    for message_index, message in enumerate(mb):
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
            msg_date = message.get('Date', 'unknown')
            msg_info = MsgInfo(signed_data, signature, f'{filename}:{message_index}', msg_date)
            if not dsp in results:
                results[dsp] = []
            results[dsp].append(msg_info)
            statistics.total += 1
    logging.info(f'processed {len(mb)} messages')
    logging.info(f'statistics: {statistics}')
    return results


class ProgramArgs(argparse.Namespace):
    mbox_files: list[str]
    loglevel: int


def main():
    parser = argparse.ArgumentParser(description='extract message data together with signatures from the DKIM-Signature header field of each message in an mbox file,\
            and try to find the RSA public key from pairs of messages signed with the same key',
                                     allow_abbrev=False)
    parser.add_argument('--mbox-files', help='load data from mbox files and save to corresponding .mbox.datasig', type=str, nargs='+', required=True)
    parser.add_argument('--debug', action="store_const", dest="loglevel", const=logging.DEBUG, default=logging.INFO, help='enable debug logging')
    args = parser.parse_args(namespace=ProgramArgs)

    logging.root.name = os.path.basename(__file__)
    logging.basicConfig(level=args.loglevel, format='%(name)s: %(levelname)s: %(message)s')

    for mbox_file in args.mbox_files:
        results = parse_mbox_file(mbox_file)
        pickle.dump(results, open(f'{mbox_file}.datasig', 'wb'))
        logging.info(f'results saved to {mbox_file}.datasig')


if __name__ == '__main__':
    main()
