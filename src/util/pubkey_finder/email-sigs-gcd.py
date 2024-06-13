import asyncio
import binascii
import json
import logging
import os
import subprocess
import random
from datetime import datetime
from tqdm import tqdm
from prisma import Prisma
from prisma.models import EmailSignature
from prisma.enums import KeyType
from Crypto.PublicKey import RSA
from common import Dsp, get_date_interval

DspToSigs = dict[Dsp, list[EmailSignature]]


def find_key(dsp: Dsp, sig0: EmailSignature, sig1: EmailSignature, loglevel: int) -> str | None:
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
		return None
	logging.info(f'found public key for {dsp}')
	rsa_key = RSA.construct((n, e))
	keyDER = rsa_key.exportKey(format='DER')
	keyDER_base64 = binascii.b2a_base64(keyDER, newline=False).decode('utf-8')
	return keyDER_base64


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
	for s in tqdm(email_signatures):
		dsp = Dsp(domain=s.domain, selector=s.selector)
		if dsp in dspsWithKnownKeys:
			continue
		dnsRecord = await prisma.domainselectorpair.find_first(where={'domain': s.domain, 'selector': s.selector})
		if dnsRecord:
			logging.debug(f"keys already known for {s.domain} {s.selector}")
			dspsWithKnownKeys.add(Dsp(domain=s.domain, selector=s.selector))
			continue
		if dspToSigs.get(dsp) is None:
			dspToSigs[dsp] = []
		dspToSigs[dsp].append(s)

	for dsp, sigs in dspToSigs.items():
		if len(sigs) > 1:
			sig1, sig2 = random.sample(sigs, 2)
			date1 = sig1.timestamp
			date2 = sig2.timestamp
			oldest_date, newest_date = get_date_interval(date1, date2)
			p = find_key(dsp, sig1, sig2, logging.INFO)
			if p:
				dsp_record = await prisma.domainselectorpair.find_first(where={'domain': dsp.domain, 'selector': dsp.selector})
				if dsp_record is None:
					dsp_record = await prisma.domainselectorpair.create(data={'domain': dsp.domain, 'selector': dsp.selector, 'sourceIdentifier': 'public_key_gcd_batch'})
					logging.info(f'created domain/selector pair: {dsp.domain} / {dsp.selector}')
				dkimrecord = await prisma.dkimrecord.find_first(where={'domainSelectorPairId': dsp_record.id, 'keyData': p})
				if dkimrecord is None:
					res = await prisma.dkimrecord.create(
					    data={
					        'domainSelectorPairId': dsp_record.id,
					        'firstSeenAt': oldest_date or datetime.now(),
					        'lastSeenAt': newest_date or datetime.now(),
					        'value': f'k=rsa; p={p}',
					        'keyType': KeyType.RSA,
					        'keyData': p,
					        'source': 'public_key_gcd_batch',
					    })
					logging.info(f'created dkim record: {res}')
		else:
			logging.info(f"only one signature found for {dsp}")


if __name__ == '__main__':
	asyncio.run(main())
