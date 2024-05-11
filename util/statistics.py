#!/usr/bin/env python

# load an .mbox file and collect various statistics about domains

import collections
import mailbox
import sys
import email.utils
import argparse
from common import decode_dkim_tag_value_list


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
			print(f'warning: invalid From header {fromAddress}', file=sys.stderr)
			continue
		fromAddress = email.utils.parseaddr(fromAddress)[1]
		if not fromAddress:
			print(f'warning: invalid From header {fromAddress}', file=sys.stderr)
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
	argparser = argparse.ArgumentParser(description='Collect various statistics about domains, selectors, and DKIM signatures')
	argparser.add_argument('--mboxFile', help='Show statistics about DKIM sigatures and domains for an .mbox file')
	tsvHelp = 'For a .tsv file with two columns(domain, selector), show a list of selectors, with percentage of domains convered for each selector. Also print accumulated percentage of domains covered when using the N most common selectors'
	argparser.add_argument('--tsvFile', help=tsvHelp)
	args = argparser.parse_args()

	if (not args.mboxFile and not args.tsvFile):
		argparser.print_help()
		sys.exit(1)

	if args.mboxFile:
		domain_statistics(args.mboxFile)
	if args.tsvFile:
		selector_statistics(args.tsvFile)
