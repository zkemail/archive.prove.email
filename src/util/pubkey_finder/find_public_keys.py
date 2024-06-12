import base64
import binascii
import hashlib
import json
import logging
import os
import argparse
import queue
import subprocess
import sys
import threading
from Crypto.PublicKey import RSA
from common import Dsp, MsgInfo, load_signed_data

dsp_queue: "queue.Queue[tuple[int, Dsp, list[tuple[MsgInfo, MsgInfo]]]]" = queue.Queue()


def hexdigest(data: bytes, hashfn: str):
	if hashfn == 'sha256':
		return hashlib.sha256(data).hexdigest()
	if hashfn == 'sha512':
		return hashlib.sha512(data).hexdigest()
	raise ValueError(f'unsupported hashfn={hashfn}')


def call_solver_and_process_result(dsp: Dsp, msg1: MsgInfo, msg2: MsgInfo, loglevel: int) -> str:
	logging.info(f'searching for public key for {dsp}')
	cmd = [
	    "python3",
	    "gcd_solver.py",
	    "--loglevel",
	    str(loglevel),
	]
	hashfn = 'sha256'
	data_parameters = [
	    hexdigest(msg1.signedData, hashfn),
	    base64.b64encode(msg1.signature).decode('utf-8'),
	    hexdigest(msg2.signedData, hashfn),
	    base64.b64encode(msg2.signature).decode('utf-8'),
	    hashfn,
	]
	logging.debug(" ".join(cmd) + ' [... data parameters ...]')

	output = subprocess.check_output(cmd + data_parameters)
	data = json.loads(output)
	n = int(data['n_hex'], 16)
	e = int(data['e_hex'], 16)
	if (n < 2):
		logging.info(f'no public key found for {dsp}')
		return '-'
	try:
		logging.info(f'found public key for {dsp}')
		rsa_key = RSA.construct((n, e))
		keyDER = rsa_key.exportKey(format='DER')
		keyDER_base64 = binascii.b2a_base64(keyDER, newline=False).decode('utf-8')
		return f'k=rsa; p={keyDER_base64}'
	except ValueError as e:
		logging.error(f'ValueError: {e}')
		return f'ValueError: {e}'


def read_and_resolve_worker(loglevel: int):
	while True:
		logging.info(f'DSPs left: {dsp_queue.qsize()}')
		dsp_index, dsp, msg_pairs = dsp_queue.get()
		for msg1, msg2 in msg_pairs:
			key_result = call_solver_and_process_result(dsp, msg1, msg2, loglevel)
			row_values = [str(dsp_index).zfill(4), dsp.domain, dsp.selector, key_result, msg1.source, msg2.source, msg1.date, msg2.date]
			print("\t".join(row_values))
			sys.stdout.flush()
		dsp_queue.task_done()


def include_dsp(dsp: Dsp) -> bool:
	if dsp.domain == 'mail.messari.io' and dsp.selector == 's1':
		# 2048 bits
		return True

	return True


def solve_msg_pairs(signed_messages: dict[Dsp, list[MsgInfo]], threads: int, loglevel: int, sparse_nth: int):
	msg_list = list(signed_messages.items())
	if sparse_nth > 1:
		msg_list = msg_list[::sparse_nth]
	logging.info(f'searching for public key for {len(msg_list)} message pairs')
	for i, (dsp, msg_infos) in enumerate(msg_list):
		if len(msg_infos) == 2:
			dsp_queue.put((i, dsp, [(msg_infos[0], msg_infos[1])]))
		elif len(msg_infos) == 3:
			dsp_queue.put((i, dsp, [(msg_infos[0], msg_infos[1]), (msg_infos[1], msg_infos[2])]))
		elif len(msg_infos) >= 4:
			dsp_queue.put((i, dsp, [(msg_infos[0], msg_infos[1]), (msg_infos[2], msg_infos[3])]))
	logging.info(f'starting {threads} threads')
	for _i in range(threads):
		t_in = threading.Thread(target=read_and_resolve_worker, daemon=True, args=(loglevel, ))
		t_in.start()
	dsp_queue.join()


class ProgramArgs(argparse.Namespace):
	datasig_files: list[str]
	list_dsps: bool
	filter_domain: str
	loglevel: int
	threads: int
	sparse_nth: int
	display_signed_text: bool


def main():
	parser = argparse.ArgumentParser(description='extract message data together with signatures from the DKIM-Signature header field of each message in an mbox file,\
            and try to find the RSA public key from pairs of messages signed with the same key',
	                                 allow_abbrev=False)
	parser.add_argument('--datasig-files', help='find public keys from the data in one or many .datasig files', type=str, nargs='+', required=True)
	parser.add_argument('--sparse-nth', type=int, help='use together with --datasig-files to only process every Nth domain', default=1)
	parser.add_argument('--list-dsps', help='use together with --datasig-files to list the domains and selectors in the datasig files and exit', action='store_true')
	parser.add_argument('--display-signed-text', action='store_true', help='use together with --datasig-files to display the signed text of each message')

	parser.add_argument('--filter-domain', help='only process messages with this domain', type=str)
	parser.add_argument('--debug', action="store_const", dest="loglevel", const=logging.DEBUG, default=logging.INFO, help='enable debug logging')
	parser.add_argument('--threads', type=int, default=1, help='number of threads to use for solving')
	args = parser.parse_args(namespace=ProgramArgs)

	logging.root.name = os.path.basename(__file__)
	logging.basicConfig(level=args.loglevel, format='%(name)s: %(levelname)s: %(message)s')

	signed_data = load_signed_data(args.datasig_files)
	signed_data = {dsp: msg_infos for dsp, msg_infos in signed_data.items() if len(msg_infos) >= 2}
	if args.filter_domain:
		signed_data = {dsp: msg_infos for dsp, msg_infos in signed_data.items() if dsp.domain == args.filter_domain}

	if args.list_dsps:
		for dsp in signed_data.keys():
			print(f'{dsp.domain}\t{dsp.selector}')
		return
	if args.display_signed_text:
		for dsp, msg_infos in signed_data.items():
			for i, msg_info in enumerate(msg_infos):
				print(f'signed text for domain: {dsp.domain}, selector: {dsp.selector}, message {i}:')
				print(msg_info.signedData.decode('utf-8'))
				print()
		return
	solve_msg_pairs(signed_data, args.threads, args.loglevel, args.sparse_nth)


if __name__ == '__main__':
	main()
