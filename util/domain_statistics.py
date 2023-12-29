#!/usr/bin/env python

# load an .mbox file and collect various statistics about domains

import mailbox
import sys
import email.utils
from common import decode_dkim_header_field


def main():
	totalMsgCount = 0
	fromAndDkimDomainSameCount = 0
	fromAndDkimDomainDifferentCount = 0
	totalWithDkimSigCount = 0
	if len(sys.argv) != 2:
		print('usage: domain_statistics.py file.mbox', file=sys.stderr)
		sys.exit(1)
	mboxFile = sys.argv[1]
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
		dkimRecord = decode_dkim_header_field(dkimSignature)
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


if __name__ == '__main__':
	main()
