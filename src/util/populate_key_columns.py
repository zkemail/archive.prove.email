#!/usr/bin/env python3
import subprocess
import asyncio
import logging
import base64
import binascii
from typing import Optional
from dataclasses import dataclass
from prisma import Prisma
from prisma.enums import KeyType
from prisma.models import DkimRecord
from prisma.types import DkimRecordWhereUniqueInput
from prisma.types import DkimRecordWhereInput
from tqdm import tqdm
from dkim_util import DecodeTvlException, decode_dkim_tag_value_list


class Asn1ParseException(Exception):
	def __init__(self, stderr: str, stdout: str, command: list[str], returncode: int):
		self.stderr = stderr
		self.stdout = stdout
		self.command = command
		super().__init__(f'{self.__class__.__name__}: STDERR: {stderr.strip()}, STDOUT: {stdout.strip()}, COMMAND: {" ".join(command)}')


class TagsNotPresentException(Exception):
	pass


class Base64DecodeException(Exception):
	pass


@dataclass
class KeyInfo:
	key_type: KeyType
	key_data_base64: str | None


def run_command(command: list[str], input: bytes) -> bytes:
	res = subprocess.run(command, input=input, capture_output=True)
	if res.returncode != 0:
		stderr = res.stderr.decode('utf-8')
		stdout = res.stdout.decode('utf-8')
		raise Asn1ParseException(stderr, stdout, command, res.returncode)
	return res.stdout


def encode_asn1_base64(der_binary: bytes) -> str:
	openssl_output = run_command(['openssl', 'rsa', '-pubin', '-inform', 'DER', '-outform', 'DER'], der_binary)
	return base64.b64encode(openssl_output).decode('utf-8')


def str_to_key_type(key_type_str: str | None) -> KeyType:
	if key_type_str is None:
		# if k is not specified, RSA is implied, see https://datatracker.ietf.org/doc/html/rfc6376#section-3.6.1
		return KeyType.RSA
	if key_type_str.lower() == 'rsa':
		return KeyType.RSA
	if key_type_str.lower() == 'ed25519':
		return KeyType.Ed25519
	else:
		raise ValueError(f'Unknown key type: "{key_type_str}"')


# return a KeyInfo if the key is valid, othwerwise raise an exception
def verify_dkim_tvl(tvl: str) -> KeyInfo:
	values = decode_dkim_tag_value_list(tvl)

	key_type = str_to_key_type(values.get('k'))

	try:
		p_base64 = values['p'].strip()
	except KeyError:
		raise TagsNotPresentException(f'No p= tag in DKIM tag-value-list: {tvl}')

	if p_base64 == '':
		# an empty p= tag is allowed and means that the key is revoked, see https://datatracker.ietf.org/doc/html/rfc6376#section-3.6.1
		return KeyInfo(key_type, '')

	try:
		p_binary = base64.b64decode(p_base64)
	except binascii.Error as e:
		raise Base64DecodeException(f'Error decoding base64: {e}')
	if key_type == KeyType.RSA:
		run_command(['openssl', 'asn1parse', '-inform', 'DER'], p_binary)
		p_base64_normalized = base64.b64encode(p_binary).decode('utf-8')  # normalize base64 encoding
		reencoded_base64 = encode_asn1_base64(p_binary)
		if reencoded_base64 != p_base64_normalized:
			#raise Exception('reencoded base64 does not match original base64')
			logging.warning('reencoded base64 does not match original base64')
			logging.warning(f'original:  {p_base64}')
			logging.warning(f'reencoded: {reencoded_base64}')
		return KeyInfo(key_type, p_base64_normalized)
	else:
		return KeyInfo(key_type, None)


async def process_record(record: DkimRecord, prisma: Prisma):
	if record.keyType is not None and record.keyData is not None:
		logging.debug(f'skipping record {record.id} because it already has a key')
		return
	try:
		rsa_key = verify_dkim_tvl(record.value)
		if rsa_key.key_data_base64 is not None:
			await prisma.dkimrecord.update(where={'id': record.id}, data={'keyType': rsa_key.key_type, 'keyData': rsa_key.key_data_base64})
	except Exception as e:
		if isinstance(e, TagsNotPresentException) or isinstance(e, Asn1ParseException) or isinstance(e, Base64DecodeException) or isinstance(e, DecodeTvlException):
			await prisma.dkimrecord.update(where={'id': record.id}, data={'keyData': '-'})
		errstr = f'{e}'.replace('\n', '\\n')
		logging.debug(f'record id {record.id}: {e.__class__.__name__}: {errstr}')


async def download_worker(q: asyncio.Queue[DkimRecord], prisma: Prisma):
	while True:
		record = await q.get()
		await process_record(record, prisma)
		q.task_done()


async def main(loop: asyncio.AbstractEventLoop):
	prisma = Prisma()
	await prisma.connect()
	q: asyncio.Queue[DkimRecord] = asyncio.Queue(maxsize=20)
	workers = [loop.create_task(download_worker(q, prisma)) for _ in range(20)]
	logging.basicConfig(level=logging.INFO)
	logging.getLogger("httpx").setLevel(logging.WARNING)

	cursor: Optional[DkimRecordWhereUniqueInput] = None

	qb_query: DkimRecordWhereInput = {'keyData': None, 'keyType': None}  # type: ignore
	num_records = await prisma.dkimrecord.count(where=qb_query)
	with tqdm(total=num_records, bar_format='{l_bar}{r_bar}') as pbar:
		while True:
			skip = 0 if cursor is None else 1
			records = await prisma.dkimrecord.find_many(take=5000, cursor=cursor, skip=skip, where=qb_query)
			logging.debug(f'fetched {len(records)} records')
			if len(records) == 0:
				break
			for record in records:
				pbar.update(1)
				pbar.set_description(f'last db id: {record.id}', refresh=False)
				await q.put(record)
			cursor = {'id': records[-1].id}
	await q.join()
	for worker in workers:
		worker.cancel()
	await asyncio.gather(*workers, return_exceptions=True)

	await prisma.disconnect()


if __name__ == '__main__':
	loop = asyncio.get_event_loop()
	try:
		loop.run_until_complete(main(loop))
	finally:
		loop.close()
