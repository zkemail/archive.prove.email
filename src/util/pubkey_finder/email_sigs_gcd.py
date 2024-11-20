import asyncio
import binascii
import json
import logging
import os
import subprocess
import random
from datetime import datetime
from prisma import Prisma
from prisma.models import EmailSignature
from prisma.enums import KeyType
from Cryptodome.PublicKey import RSA
from common import Dsp, get_date_interval
import sys
from tqdm import tqdm


DspToSigs = dict[Dsp, list[EmailSignature]]


def find_key(dsp: Dsp, sig0: EmailSignature, sig1: EmailSignature, loglevel: int) -> str | None:
	assert sys.executable.endswith('python3.10'), f"Expected python3.10, but got {sys.executable}"
	cmd = [sys.executable, "src/util/pubkey_finder/gcd_solver.py", "--loglevel", str(loglevel)]
	hashfn = 'sha256'
	data_parameters = [sig0.headerHash, sig0.dkimSignature, sig1.headerHash, sig1.dkimSignature, hashfn]
	logging.debug(" ".join(cmd) + ' [... data parameters ...]')

	output = subprocess.check_output(cmd + data_parameters)
	data = json.loads(output)
	n = int(data['n_hex'], 16)
	e = int(data['e_hex'], 16)
	if (n < 2):
		return None
	rsa_key = RSA.construct((n, e))
	keyDER = rsa_key.exportKey(format='DER')
	keyDER_base64 = binascii.b2a_base64(keyDER, newline=False).decode('utf-8')
	return keyDER_base64


async def has_known_keys(prisma: Prisma, dsp: Dsp, dspsWithKnownKeys: set[Dsp]) -> bool:
	if dsp in dspsWithKnownKeys:
		return True
	dnsRecord = await prisma.domainselectorpair.find_first(where={'domain': dsp.domain, 'selector': dsp.selector})
	if dnsRecord:
		dspsWithKnownKeys.add(dsp)
		return True
	return False


async def find_key_for_signature_pair(dsp: Dsp, sig1: EmailSignature, sig2: EmailSignature, prisma: Prisma):
	info = f'dsp {dsp} and signatures {sig1.id} and {sig2.id}'
	logging.info(f'run gcd solver for {info}')
	p = find_key(dsp, sig1, sig2, logging.INFO)
	if p:
		logging.info(f'found public key for {info}')
		dsp_record = await prisma.domainselectorpair.find_first(where={'domain': dsp.domain, 'selector': dsp.selector})
		if dsp_record is None:
			dsp_record = await prisma.domainselectorpair.create(data={'domain': dsp.domain, 'selector': dsp.selector, 'sourceIdentifier': 'public_key_gcd_batch'})
			logging.info(f'created domain/selector pair: {dsp.domain} / {dsp.selector}')
		dkimrecord = await prisma.dkimrecord.find_first(where={'domainSelectorPairId': dsp_record.id, 'keyData': p})
		if dkimrecord is None:
			date1 = sig1.timestamp
			date2 = sig2.timestamp
			oldest_date, newest_date = get_date_interval(date1, date2)
			dkimrecord = await prisma.dkimrecord.create(
			    data={
			        'domainSelectorPairId': dsp_record.id,
			        'firstSeenAt': oldest_date or datetime.now(),
			        'lastSeenAt': newest_date or datetime.now(),
			        'value': f'k=rsa; p={p}',
			        'keyType': KeyType.RSA,
			        'keyData': p,
			        'source': 'public_key_gcd_batch',
			    })
			logging.info(f'created dkim record: {dkimrecord}')
		await prisma.emailpairgcdresult.create(data={
		    'emailSignatureA_id': sig1.id,
		    'emailSignatureB_id': sig2.id,
		    'dkimRecordId': dkimrecord.id,
		    'foundGcd': True,
		    'timestamp': datetime.now(),
		})
	else:
		logging.info(f'no public key found for {info}')
		await prisma.emailpairgcdresult.create(data={
		    'emailSignatureA_id': sig1.id,
		    'emailSignatureB_id': sig2.id,
		    'dkimRecordId': None,
		    'foundGcd': False,
		    'timestamp': datetime.now(),
		})


async def main():
	logging.root.name = os.path.basename(__file__)
	logging.getLogger("httpx").setLevel(logging.WARNING)
	logging.basicConfig(level=logging.INFO, format='%(name)s: %(levelname)s: %(message)s')
	prisma = Prisma()
	await prisma.connect()
	email_signatures = await prisma.emailsignature.find_many()
	dspToSigs: DspToSigs = {}
	dspsWithKnownKeys: set[Dsp] = set()
	logging.info(f"filtering out email signatures for which we already have keys")
	for s in email_signatures:
		dsp = Dsp(domain=s.domain, selector=s.selector)
		if dspToSigs.get(dsp) is None:
			dspToSigs[dsp] = []
		dspToSigs[dsp].append(s)

	with tqdm(total=len(dspToSigs), desc="Searching for public keys") as pbar:
		for dsp, sigs in dspToSigs.items():
			if await has_known_keys(prisma, dsp, dspsWithKnownKeys):
				pbar.set_postfix_str(f"Keys known for {dsp.domain} {dsp.selector}")
			else:
				pbar.set_postfix_str(f"Searching {dsp.domain} {dsp.selector}")
			pbar.update(1)
			if len(sigs) >= 2:
				sig1, sig2 = random.sample(sigs, 2)
				pairGcdResult = await prisma.emailpairgcdresult.find_first(
						where={'OR': [
								{
										'emailSignatureA_id': sig1.id,
										'emailSignatureB_id': sig2.id
								},
								{
										'emailSignatureA_id': sig2.id,
										'emailSignatureB_id': sig1.id
								},
						]})
				if pairGcdResult:
					logging.info(f"EmailPairGcdResult already exists for signatures {sig1.id} and {sig2.id}")
					continue
				await find_key_for_signature_pair(dsp, sig1, sig2, prisma)
			else:
				logging.info(f"less than 2 signatures found for {dsp}")


if __name__ == '__main__':
	asyncio.run(main())
