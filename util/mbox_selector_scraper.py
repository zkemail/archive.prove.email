#!/usr/bin/env python

# extracts DKIM domains and selectors from mbox files and outputs them as TSV
# usage: mbox_selector_scraper.py file1.mbox [file2.mbox ...] > output.tsv

import sys
import mailbox

from common import decode_dkim_header_field

def add_to_dict(dct: dict[str, list[str]], domain: str, selector: str):
	if (not selector) or (not domain):
		return
	if domain not in dct:
		dct[domain] = []
	if selector not in dct[domain]:
		dct[domain].append(selector)


def get_domain_selectors(outputDict: dict[str, list[str]], mboxFile: str):
	for message in mailbox.mbox(mboxFile):
		dkimSignature = message['DKIM-Signature']
		if not dkimSignature:
			continue
		dkimRecord = decode_dkim_header_field(dkimSignature)
		domain = dkimRecord['d']
		selector = dkimRecord['s']
		add_to_dict(outputDict, domain, selector)


def main():
	domainSelectorsDict: dict[str, list[str]] = {}
	mboxFiles = sys.argv[1:]
	if len(mboxFiles) == 0:
		print('usage: mbox_selector_scraper.py file1.mbox [file2.mbox ...] > output.tsv')
		sys.exit(1)
	for f in mboxFiles:
		print(f'processing {f}', file=sys.stderr)
		get_domain_selectors(domainSelectorsDict, f)
	domainSelectorsDict = dict(sorted(domainSelectorsDict.items()))
	for domain, selectors in domainSelectorsDict.items():
		if '\t' in domain:
			print(f'warning: domain {domain} includes a tab character, skipping', file=sys.stderr)
			continue
		for selector in selectors:
			if '\t' in selector:
				print(f'warning: selector {selector} includes a tab character, skipping', file=sys.stderr)
				continue
			print(f'{domain}\t{selector}')


if __name__ == '__main__':
	main()
