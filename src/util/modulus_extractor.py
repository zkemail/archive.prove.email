import argparse
import asyncio
import base64
import binascii
import logging
import multiprocessing
import queue
import re
import subprocess
import threading
from typing import Optional, TextIO
from prisma import Prisma
from prisma.models import DkimRecord
from prisma.types import DkimRecordWhereUniqueInput
from tqdm import tqdm
from dkim_util import decode_dkim_tag_value_list


class CommandException(Exception):
	def __init__(self, stderr: str, stdout: str, command: list[str], returncode: int):
		self.stderr = stderr
		self.stdout = stdout
		self.command = command
		super().__init__(f'{self.__class__.__name__}: STDERR: {stderr.strip()}, STDOUT: {stdout.strip()}, COMMAND: {" ".join(command)}')


tsv_queue: "queue.Queue[tuple[int, str]]" = queue.Queue(maxsize=10)
out_queue: "queue.Queue[tuple[int, str]]" = queue.Queue(maxsize=10)
stop_event = threading.Event()


def run_command(command: list[str], input: bytes) -> str:
	res = subprocess.run(command, input=input, capture_output=True)
	if res.returncode != 0:
		stderr = res.stderr.decode('utf-8')
		stdout = res.stdout.decode('utf-8')
		raise CommandException(stderr, stdout, command, res.returncode)
	return res.stdout.decode('utf-8')


def get_p_binary(tvl: str) -> bytes | None:
	values = decode_dkim_tag_value_list(tvl)
	try:
		p_base64 = values['p']
	except KeyError:
		return None
	if p_base64.strip() == '':
		return None
	try:
		p_binary = base64.b64decode(p_base64)
	except binascii.Error as e:
		raise Exception(f'Error decoding base64: {e}')
	return p_binary


def get_rsa_modulus(tvl: str) -> str | None:
	p_binary = get_p_binary(tvl)
	if p_binary is None:
		return None

	openssl_output = run_command(['openssl', 'rsa', '-pubin', '-inform', 'DER', '-modulus', '-noout'], p_binary)
	regex = r'^Modulus=([0-9a-fA-F]+)$'
	match = re.match(regex, openssl_output)
	if not match:
		raise Exception(f'unexpected output from openssl: {openssl_output}')
	return match.group(1)


def read_and_resolve_worker():
	while not stop_event.is_set():
		try:
			db_id, dkim_tvl = tsv_queue.get(block=True, timeout=0.2)
			try:
				rsa_modulus = get_rsa_modulus(dkim_tvl)
				if rsa_modulus is not None:
					out_queue.put((db_id, rsa_modulus))
			except Exception as e:
				errstr = f'{e}'.replace('\n', '\\n')
				logging.debug(f'{db_id}\t{e.__class__.__name__}: {errstr}')
			tsv_queue.task_done()
		except queue.Empty:
			pass


def write_worker():
	unique_moduli: set[str] = set()
	duplicates = 0
	while not stop_event.is_set():
		try:
			db_id, rsa_modulus = out_queue.get(block=True, timeout=0.2)
			if rsa_modulus not in unique_moduli:
				unique_moduli.add(rsa_modulus)
				print(f'{db_id},{rsa_modulus}')
			else:
				duplicates += 1
			out_queue.task_done()
		except queue.Empty:
			pass
	logging.info(f'unique moduli: {len(unique_moduli)}')
	logging.info(f'duplicates: {duplicates}')


async def post_process(csvFile: TextIO, prisma: Prisma):
	logging.info('post processing')
	ids: list[int] = []
	for line in csvFile:
		parts = line.strip().split(',')
		db_id = int(parts[0])
		factor_p = int(parts[1])
		factor_q = int(parts[2])
		ids.append(db_id)
		record = await prisma.dkimrecord.find_unique(where={'id': db_id}, include={'domainSelectorPair': True})
		if record is None:
			print(f'record {db_id} not found')
			continue
		print(f'DkimRecord database id: {record.id}')
		if record.domainSelectorPair is not None:
			print(f'domain: {record.domainSelectorPair.domain}, selector: {record.domainSelectorPair.selector}')

		dkim_tvl = record.value
		modulus_hex = get_rsa_modulus(dkim_tvl)
		if modulus_hex is None:
			print(f'no modulus for record {db_id}')
			continue
		modulus_int = int(modulus_hex, 16)
		print(f'modulus: {modulus_int}')
		print(f'solved factor p: {factor_p}')
		print(f'solved factor q: {factor_q}')
		if modulus_int % (factor_p * factor_q) == 0:
			print(f'factors are correct, p*q divides modulus')
		else:
			print(f'factors are incorrect, p*q does not divide modulus')
		print()


async def extract_moduli(prisma: Prisma):
	logging.info('fetching records')
	cursor: Optional[DkimRecordWhereUniqueInput] = None
	records: list[DkimRecord] = []
	while True:
		skip = 0 if cursor is None else 1
		new_records = await prisma.dkimrecord.find_many(take=50000, include={'domainSelectorPair': True}, cursor=cursor, skip=skip)
		logging.info(f'fetched {len(records)} records')
		if len(new_records) == 0:
			break
		records.extend(new_records)
		cursor = {'id': new_records[-1].id}

	await prisma.disconnect()

	num_threads = multiprocessing.cpu_count()
	logging.info(f'starting {num_threads} threads')
	for _ in range(num_threads):
		t_in = threading.Thread(target=read_and_resolve_worker)
		t_in.start()

	t_out = threading.Thread(target=write_worker)
	t_out.start()
	for record in tqdm(records, total=len(records), bar_format='{desc}: {percentage:3.0f}% {r_bar}\r', unit='records'):
		dkim_tvl = record.value
		tsv_queue.put((record.id, dkim_tvl))
	tsv_queue.join()
	out_queue.join()
	stop_event.set()


async def main():
	logging.basicConfig(level=logging.INFO)
	argparser = argparse.ArgumentParser(
	    description=
	    'Extract RSA moduli from DKIM records and output them as CSV with columns: id, modulus. Alternatively, post process a CSV file with columns: id, factor_p, factor_q and check if the factors are correct for the modulus in the database.'
	)
	argparser.add_argument('--extract-moduli', action='store_true', help='extract RSA moduli from DKIM records and output them to standard output as CSV with columns: id, modulus')
	argparser.add_argument('--post-process', type=argparse.FileType('r'), help='post process a CSV file with columns: id, factor_p, factor_q')
	args = argparser.parse_args()

	prisma = Prisma()
	await prisma.connect()

	if args.post_process:
		await post_process(args.post_process, prisma)
	elif args.extract_moduli:
		await extract_moduli(prisma)
	else:
		raise ValueError('either --extract-moduli or --post-process must be specified')


if __name__ == '__main__':
	asyncio.run(main())
