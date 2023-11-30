#!/usr/bin/env python

# read domains and selectors from a TSV file and publish them to a PostgreSQL database

import os
import sys
import psycopg2
import dns.exception
import dns.resolver
import dns.rdatatype
from datetime import datetime
from typing import NamedTuple
from dotenv import load_dotenv


class DkimRecord(NamedTuple):
	domain: str
	selector: str
	value: str
	timestamp: datetime


def get_os_env(key: str):
	value = os.getenv(key)
	if not value:
		raise Exception(f'environment variable {key} not found')
	return value


def load_domains_and_selectors_from_tsv(outputDict, filename):
	with open(filename, 'r') as f:
		for i, line in enumerate(f):
			line = line.rstrip('\r\n')
			parts = line.split('\t')
			if len(parts) != 2:
				print(f'warning: skipping line {i+1} in {filename}, expected 2 tab-separated columns, got {len(parts)}')
				continue
			domain, selector = parts
			if (not selector) or (not domain):
				print(f'warning: skipping line {i+1} in {filename}, selector or domain is empty')
				continue
			if domain not in outputDict:
				outputDict[domain] = []
			if selector not in outputDict[domain]:
				outputDict[domain].append(selector)

def fetch_dkim_records_from_dns(domainSelectorsDict):
	res = []
	for domain in domainSelectorsDict:
		for selector in domainSelectorsDict[domain]:
			print(f'fetching {selector}._domainkey.{domain}')
			qname = f'{selector}._domainkey.{domain}'
			try:
				response = dns.resolver.resolve(qname, dns.rdatatype.TXT)
			except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers, dns.exception.Timeout) as e:
				print(f'warning: dns resolver error: {e}')
				continue
			if len(response) == 0:
				print(f'warning: no records found for {qname}')
				continue
			if len(response) > 1:
				print(f'warning: > 1 record found for {qname}, using first one')
			dkimData = b''.join(response[0].strings).decode()
			dkimRecord = DkimRecord(
				selector=selector, domain=domain, value=dkimData, timestamp=datetime.now())
			res.append(dkimRecord)
	return res


def add_records_to_db(records: list[DkimRecord]):
	""" Connect to the PostgreSQL database server """
	conn = None
	try:
		conn = psycopg2.connect(
			host=get_os_env('POSTGRESQL_HOST'),
			database=get_os_env('POSTGRESQL_DATABASE'),
			user=get_os_env('POSTGRESQL_USER'),
			password=get_os_env('POSTGRESQL_PASSWORD'))
		cur = conn.cursor()
		cur.execute('SELECT version()')
		print(cur.fetchone())
		for record in records:
			cur.execute('SELECT * FROM "DkimRecord" WHERE "dkimDomain" = %s AND "dkimSelector" = %s AND "value" = %s',
						(record.domain, record.selector, record.value))
			if cur.fetchone():
				print(f'key for: {record.domain}, {record.selector} found in database, skipping')
				continue
			print(f'adding {record.domain}, {record.selector} to database')
			cur.execute('INSERT INTO "DkimRecord" ("dkimDomain", "dkimSelector", "fetchedAt", "value") VALUES (%s, %s, %s, %s)',
						(record.domain, record.selector, record.timestamp, record.value))
			conn.commit()
		cur.close()
	except (psycopg2.DatabaseError) as error:
		print(error)
	finally:
		if conn is not None:
			conn.close()


def main():
	load_dotenv()
	tsvFiles = sys.argv[1:]
	if len(tsvFiles) < 1:
		print('usage: publish_records.py file1.tsv [file2.tsv ...]')
		sys.exit(1)
	print('loading domains and selectors')
	domainSelectorsDict = {}
	for f in tsvFiles:
		print(f'loading domains and selectors from {f}')
		load_domains_and_selectors_from_tsv(domainSelectorsDict, f)

	print('fetching dkim records from dns')
	records = fetch_dkim_records_from_dns(domainSelectorsDict)
	print('adding records to database')
	add_records_to_db(records)


if __name__ == '__main__':
	main()
