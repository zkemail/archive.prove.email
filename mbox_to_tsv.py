#!/usr/bin/env python

# extracts DKIM domains and selectors from mbox files and output them as TSV
# usage: mbox_to_tsv.py file1.mbox [file2.mbox ...] > output.tsv

import sys
import mailbox


def decode_dkim_header_field(dkimData):
	# decode a DKIM-Signature header field such as "v=1; a=rsa-sha256; d=example.net; s=brisbane;"
	# to a dictionary such as {'v': '1', 'a': 'rsa-sha256', 'd': 'example.net', 's': 'brisbane'}
	tagValuePairStrings = list(map(lambda x: x.strip(), dkimData.split(';')))
	res = {}
	for s in tagValuePairStrings:
		if not s:
			continue
		key, value = s.split('=', 1)
		res[key] = value
	return res


def add_to_dict(dict, domain, selector):
	if (not selector) or (not domain):
		return
	if domain not in dict:
		dict[domain] = []
	if selector not in dict[domain]:
		dict[domain].append(selector)


def get_domain_selectors(outputDict, mboxFile):
	for message in mailbox.mbox(mboxFile):
		dkimSignature = message['DKIM-Signature']
		if not dkimSignature:
			continue
		dkimRecord = decode_dkim_header_field(dkimSignature)
		domain = dkimRecord['d']
		selector = dkimRecord['s']
		add_to_dict(outputDict, domain, selector)


def main():
	domainSelectorsDict = {}
	mboxFiles = sys.argv[1:]
	if len(mboxFiles) == 0:
		print('usage: mbox_to_tsv.py file1.mbox [file2.mbox ...] > output.tsv')
		sys.exit(1)
	for f in mboxFiles:
		print(f'processing {f}', file=sys.stderr)
		get_domain_selectors(domainSelectorsDict, f)
	domainSelectorsDict = dict(sorted(domainSelectorsDict.items()))
	for domain, selectors in domainSelectorsDict.items():
		for selector in selectors:
			print(f'{domain}\t{selector}')


if __name__ == '__main__':
	main()
