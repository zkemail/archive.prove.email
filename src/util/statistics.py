#!/usr/bin/env python

import collections
from dataclasses import dataclass, field
from datetime import datetime
from itertools import chain
import logging
import mailbox
import re
import sys
import email.utils
import argparse
from typing import TextIO
from tqdm import tqdm
from dkim_util import DecodeTvlException, decode_dkim_tag_value_list
import dns.exception
import dns.resolver
import dns.rdatatype


def domain_statistics(mboxFile: str):
	totalMsgCount = 0
	fromAndDkimDomainSameCount = 0
	fromAndDkimDomainDifferentCount = 0
	totalWithDkimSigCount = 0
	dkimDomains: set[str] = set()
	fromDomains: set[str] = set()
	for message in mailbox.mbox(mboxFile):
		totalMsgCount += 1
		dkimSignature = message['DKIM-Signature']
		if not dkimSignature:
			continue
		totalWithDkimSigCount += 1
		fromAddress = message['From']
		if (type(fromAddress) != str):
			logging.debug(f'warning: invalid From header {fromAddress}')
			continue
		fromAddress = email.utils.parseaddr(fromAddress)[1]
		if not fromAddress:
			logging.debug(f'warning: invalid From header {fromAddress}')
			continue
		fromDomain = fromAddress.rpartition('@')[2]
		dkimRecord = decode_dkim_tag_value_list(dkimSignature)
		dkimDomain = dkimRecord['d']
		dkimDomains.add(dkimDomain)
		fromDomains.add(fromDomain)
		if fromDomain != dkimDomain:
			fromAndDkimDomainDifferentCount += 1
		else:
			fromAndDkimDomainSameCount += 1

	print(f'total messages: {totalMsgCount}')
	print(f'total messages with dkim signature: {totalWithDkimSigCount}')
	print(f'from domain and dkim domain are the same: {fromAndDkimDomainSameCount} ({fromAndDkimDomainSameCount / totalWithDkimSigCount * 100:.2f}%)')
	print(f'from domain and dkim domain are different: {fromAndDkimDomainDifferentCount} ({fromAndDkimDomainDifferentCount / totalWithDkimSigCount * 100:.2f}%)')
	print()
	print(f'dkim domains: {len(dkimDomains)}')
	for dkimDomain in sorted(dkimDomains):
		print(dkimDomain)
	print()
	print(f'from domains: {len(fromDomains)}')
	for fromDomain in sorted(fromDomains):
		print(fromDomain)


def dsp_exists_on_dns(qname: str) -> bool:
	try:
		response = dns.resolver.resolve(qname, dns.rdatatype.TXT)
		if len(response) == 0:
			logging.debug(f'no records found for {qname}')
			return False
		txtData = ""
		for i in range(len(response)):
			txtData += b''.join(response[i].strings).decode()  # type: ignore
			txtData += ";"
		try:
			tags = decode_dkim_tag_value_list(txtData)
		except DecodeTvlException as e:
			logging.debug(f'error decoding DKIM tag-value pair: {e}')
			return False
		if 'p' not in tags:
			logging.debug(f'no p= tag found for {qname}, {txtData}')
			return False
		p = tags['p']
		if not p:
			logging.debug(f'empty p= tag found for {qname}, {txtData}')
			return False
		return True
	except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers, dns.exception.Timeout) as e:
		logging.debug(f'dns resolver error: {e}')
		return False


def date_to_time_slot(date: datetime) -> str:
	q = 'Q1Q2' if date.month < 7 else 'Q3Q4'
	return f'{date.year}_{q}'


@dataclass
class QnameBucket:
	qnames: set[str] = field(default_factory=set)
	active_qnames: set[str] = field(default_factory=set)


# probabilistically classify whether a selector, based on its name, is likely bound to a specific public key (the key will not change for the same selector name)
# examples: 2008, dk20170101, s2017-01, 201701, zj3gqqrotrgjg2t237hfixaqkmvmvwwi
def is_keybound_selector_name(s: str):
	m = re.match(r".*20(\d\d).*", s)
	if m:
		yy = int(m.group(1))
		if yy >= 5 and yy <= datetime.now().year + 1 % 100:
			return True
	if re.match(r"scph\d\d\d\d", s):
		return True
	if (len(s) == 32 and s.isalnum()):
		return True
	return False


def test_keybound_selector_classifier(selectorList: TextIO):
	keybound_selectors: set[str] = set()
	non_keybound_selectors: set[str] = set()
	for line in selectorList:
		selector = line.strip()
		if is_keybound_selector_name(selector):
			keybound_selectors.add(selector)
		else:
			non_keybound_selectors.add(selector)
	with open('tmp/keybound_selectors.txt', 'w') as f:
		for selector in sorted(keybound_selectors):
			f.write(f'{selector}\n')
	logging.info(f'wrote {len(keybound_selectors)} keybound selectors to tmp/keybound_selectors.txt')
	with open('tmp/non_keybound_selectors.txt', 'w') as f:
		for selector in sorted(non_keybound_selectors):
			f.write(f'{selector}\n')
	logging.info(f'wrote {len(non_keybound_selectors)} non-keybound selectors to tmp/non_keybound_selectors.txt')


def dkim_dns_statistics(mboxFiles: list[str], includeOnlyKeyboundSelectors: bool):
	buckets: dict[str, QnameBucket] = collections.defaultdict(QnameBucket)
	loaded_mbox_files: list[mailbox.mbox] = []
	for mboxFile in mboxFiles:
		logging.info(f'loading {mboxFile}')
		mb = mailbox.mbox(mboxFile)
		len(mb)  # preload all messages
		loaded_mbox_files.append(mb)

	for message in tqdm(chain(*loaded_mbox_files), total=sum(len(mbox) for mbox in loaded_mbox_files)):
		msgDate = message['Date']
		if (type(msgDate) != str):
			logging.debug(f'invalid Date header {msgDate}')
			continue
		try:
			msgDate = email.utils.parsedate_to_datetime(msgDate)
		except ValueError as e:
			logging.debug(f'invalid Date header {msgDate}: {e}')
			continue
		dkimSignature = message['DKIM-Signature']
		if not dkimSignature:
			continue
		dkimRecord = decode_dkim_tag_value_list(dkimSignature)
		dkimDomain = dkimRecord['d']
		dkimSelector = dkimRecord['s']
		if includeOnlyKeyboundSelectors and not is_keybound_selector_name(dkimSelector):
			continue

		time_slot_key = date_to_time_slot(msgDate)
		bucket = buckets[time_slot_key]
		bucket.qnames.add(f"{dkimSelector}._domainkey.{dkimDomain}")

	logging.info('checking DNS for domainkeys')
	for bucket in buckets.values():
		for qname in bucket.qnames:
			if dsp_exists_on_dns(qname):
				bucket.active_qnames.add(qname)

	for key, bucket in sorted(buckets.items()):
		active = len(bucket.active_qnames)
		total = len(bucket.qnames)
		print(f'{key}: {active} active domainkeys of total {total} ({active / total * 100:.2f}%)')


def selector_statistics(tsvFile: str):
	domainSelectorDict: dict[str, list[str]] = collections.defaultdict(list)
	# read .tsv file
	with open(tsvFile, 'r') as f:
		for line in f:
			line = line.rstrip('\n')
			domain, selector = line.split('\t')
			domainSelectorDict[selector].append(domain)

	# sort by number of domains
	domainSelectorDict = dict(sorted(domainSelectorDict.items(), key=lambda x: len(x[1]), reverse=True))

	totalDomains = sum(len(domains) for domains in domainSelectorDict.values())
	accumulatedDomains = 0
	for selector, domains in domainSelectorDict.items():
		if len(domains) <= 1:
			break
		domainsPercentage = len(domains) / totalDomains * 100
		accumulatedDomains += len(domains)
		accumulatedDomainsPercentage = accumulatedDomains / totalDomains * 100
		print(f'{selector}\t{len(domains)} domains ({domainsPercentage:.1f}%), accumulated: {accumulatedDomainsPercentage:.1f}%')


if __name__ == '__main__':
	logging.basicConfig(level=logging.INFO)
	argparser = argparse.ArgumentParser(description='Collect various statistics about domains, selectors, and DKIM signatures')
	argparser.add_argument('--dkimDspStatsMbox', help='Show statistics about DKIM sigatures and domains for an .mbox file')

	argparser.add_argument('--dkimDnsStatsMbox', help='Show statistics about the DNS lookup status of domains/selectors for a set of .mbox files', type=str, nargs='+')
	argparser.add_argument('--includeOnlyKeyboundSelectors',
	                       help='Use together with --dkimDnsStatsMbox to exclude "generic" selectors (such as "s1", "default", etc)',
	                       action='store_true')

	argparser.add_argument('--testKeyboundSelectorClassifier', help='Test the selector classifier with a file with a list of selectors', type=argparse.FileType('r'))

	tsvHelp = 'For a .tsv file with two columns(domain, selector), show a list of selectors, with percentage of domains convered for each selector. Also print accumulated percentage of domains covered when using the N most common selectors'
	argparser.add_argument('--tsvFile', help=tsvHelp)
	args = argparser.parse_args()

	if (not args.dkimDspStatsMbox and not args.dkimDnsStatsMbox and not args.tsvFile and not args.testKeyboundSelectorClassifier):
		argparser.print_help(file=sys.stderr)
		sys.exit(1)

	if args.dkimDspStatsMbox:
		domain_statistics(args.dkimDspStatsMbox)
	if args.tsvFile:
		selector_statistics(args.tsvFile)
	if args.dkimDnsStatsMbox:
		dkim_dns_statistics(args.dkimDnsStatsMbox, args.includeOnlyKeyboundSelectors)
	if args.testKeyboundSelectorClassifier:
		filename: TextIO = args.testKeyboundSelectorClassifier
		test_keybound_selector_classifier(filename)
