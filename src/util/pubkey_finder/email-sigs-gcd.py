import asyncio
import binascii
import json
import logging
import os
import subprocess
from prisma import Prisma
from prisma.models import EmailSignature
from prisma.types import DkimRecordWhereInput
from Crypto.PublicKey import RSA
from common import Dsp
import random

DspToSigs = dict[Dsp, list[EmailSignature]]


def call_solver_and_process_result(dsp: Dsp, sig0: EmailSignature, sig1: EmailSignature, loglevel: int) -> str:
	logging.info(f'searching for public key for {dsp}')
	cmd = ["python3", "src/util/pubkey_finder/gcd_solver.py", "--loglevel", str(loglevel)]
	hashfn = 'sha256'
	data_parameters = [sig0.headerHash, sig0.dkimSignature, sig1.headerHash, sig1.dkimSignature, hashfn]
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
		return keyDER_base64
	except ValueError as e:
		logging.error(f'ValueError: {e}')
		return f'ValueError: {e}'


def run_solver(dspToSigs: DspToSigs):
	for dsp, sigs in dspToSigs.items():
		if len(sigs) > 1:
			sig0, sig1 = random.sample(sigs, 2)
			call_solver_and_process_result(dsp, sig0, sig1, logging.INFO)
		else:
			print(f"only one signature found for {dsp}")


async def main():
	logging.root.name = os.path.basename(__file__)
	logging.getLogger("httpx").setLevel(logging.WARNING)
	logging.basicConfig(level=logging.INFO, format='%(name)s: %(levelname)s: %(message)s')
	prisma = Prisma()
	await prisma.connect()
	email_signatures = await prisma.emailsignature.find_many()
	dspToSigs: DspToSigs = {}
	for s in email_signatures:
		whereQuery: DkimRecordWhereInput = {'domainSelectorPair': {'is': {'domain': s.domain, 'selector': s.selector}}}
		dkimRecord = await prisma.dkimrecord.find_first(include={'domainSelectorPair': True}, where=whereQuery)
		if dkimRecord:
			print(f"key already known for {s.domain} {s.selector}")
			continue
		dsp = Dsp(domain=s.domain, selector=s.selector)
		if dspToSigs.get(dsp) is None:
			dspToSigs[dsp] = []
		dspToSigs[dsp].append(s)
	run_solver(dspToSigs)


if __name__ == '__main__':
	asyncio.run(main())
