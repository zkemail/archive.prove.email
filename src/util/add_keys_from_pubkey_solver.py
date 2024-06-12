import argparse
import asyncio
from datetime import datetime, timezone
from email.headerregistry import DateHeader
import sys
from typing import Any
from prisma import Prisma
from prisma.enums import KeyType

from dkim_util import decode_dkim_tag_value_list
from pubkey_finder.common import get_date_interval


def parse_email_header_date(date_str: str) -> datetime | None:
	kwds: dict[str, Any] = {}
	try:
		DateHeader.parse(date_str, kwds)
	except ValueError as e:
		print(f'Error parsing date: {e}')
		return None
	date = kwds.get('datetime')
	if date.tzinfo is None:
		# fix for that some emails have timezone= "-0000" (unspecified timezone)
		print(f'unknown timezone for {date_str}, setting to UTC')
		date = date.replace(tzinfo=timezone.utc)

	return date


async def add_records(filename: str, prisma: Prisma):
	with open(filename, 'r') as f:
		for index, line in enumerate(f):
			print()
			print(f'line {index + 1}')
			parts = line.strip().split('\t')
			domain = parts[1]
			selector = parts[2]
			dkim_tvl = parts[3]
			#src1 = parts[4]
			#src2 = parts[5]
			date1 = parse_email_header_date(parts[6])
			date2 = parse_email_header_date(parts[7])
			oldest_date, newest_date = get_date_interval(date1, date2)

			print(f'domain: {domain}, selector: {selector}, oldest_date: {oldest_date}, newest_date: {newest_date}')
			if dkim_tvl == '-':
				print(f'skipping record for {domain} / {selector} with dkim_tvl="-"')
				continue
			dsp = await prisma.domainselectorpair.find_first(where={'domain': domain, 'selector': selector})
			if dsp is None:
				dsp = await prisma.domainselectorpair.create(data={'domain': domain, 'selector': selector, 'sourceIdentifier': 'public_key_gcd_batch'})
				print(f'created domain/selector pair: {domain} / {selector}')

			p = decode_dkim_tag_value_list(dkim_tvl).get('p')
			dkimrecord = await prisma.dkimrecord.find_first(where={'domainSelectorPairId': dsp.id, 'keyData': p})
			if not dkimrecord:
				await prisma.dkimrecord.create(
				    data={
				        'domainSelectorPairId': dsp.id,
				        'firstSeenAt': oldest_date or datetime.now(),
				        'lastSeenAt': newest_date or datetime.now(),
				        'value': dkim_tvl,
						'keyType': KeyType.RSA,
						'keyData': p,
				        'source': 'public_key_gcd_batch',
				    })
				print(f'created record for {domain} / {selector}')
			else:
				print(f'record already exists for {domain} / {selector}')
				print(f'oldest_date: {oldest_date}, newest_date: {newest_date}')
				print(f'firstSeenAt: {dkimrecord.firstSeenAt}, lastSeenAt: {dkimrecord.lastSeenAt}')
				if oldest_date and oldest_date < dkimrecord.firstSeenAt:
					print(f'updating firstSeenAt from {dkimrecord.firstSeenAt} to {oldest_date}')
					dkimrecord.firstSeenAt = oldest_date
				if newest_date and (dkimrecord.lastSeenAt is None or newest_date > dkimrecord.lastSeenAt):
					print(f'updating lastSeenAt from {dkimrecord.lastSeenAt} to {newest_date}')
					dkimrecord.lastSeenAt = newest_date
				await prisma.dkimrecord.update(where={'id': dkimrecord.id}, data={'firstSeenAt': dkimrecord.firstSeenAt, 'lastSeenAt': dkimrecord.lastSeenAt})
			sys.stdout.flush()


async def main():
	argparser = argparse.ArgumentParser()
	argparser.add_argument('filename', type=str, help='TSV file containing DKIM records: id, domain, selector, dkim_tvl, src1, src2, date1, date2')
	args = argparser.parse_args()
	prisma = Prisma()
	await prisma.connect()
	await add_records(args.filename, prisma)


if __name__ == '__main__':
	asyncio.run(main())
