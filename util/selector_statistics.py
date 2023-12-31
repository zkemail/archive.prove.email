#!/usr/bin/env python

# load a .tsv file with two columns (domain and selector),
# group by selector and show the number of domains covered

import sys
import collections


def main():
	domainSelectorDict: dict[str, list[str]] = collections.defaultdict(list)
	if len(sys.argv) != 2:
		print('usage: selector_statistics.py file.tsv')
		sys.exit(1)
	tsvFile = sys.argv[1]
	# read .tsv file
	with open(tsvFile, 'r') as f:
		for line in f:
			line = line.rstrip('\n')
			domain, selector = line.split('\t')
			domainSelectorDict[selector].append(domain)

	# sort by number of domains
	domainSelectorDict = dict(sorted(domainSelectorDict.items(), key=lambda x: len(x[1]), reverse=True))

	print('Selectors and corresponding domains:')
	for selector, domains in domainSelectorDict.items():
		print(selector)
		print(f'\t{", ".join(domains)}')

	print()
	print('Selectors, number and percentage of domains for each selector, and accumulated percentage of domains covered when using the N most common selectors:')
	totalDomains = sum(len(domains) for domains in domainSelectorDict.values())
	accumulatedDomains = 0
	for index, (selector, domains) in enumerate(domainSelectorDict.items()):
		if len(domains) <= 1:
			break
		oneBasedIndex = index + 1
		domainsPercentage = len(domains) / totalDomains * 100
		accumulatedDomains += len(domains)
		accumulatedDomainsPercentage = accumulatedDomains / totalDomains * 100
		print(f'{oneBasedIndex}: {selector}, {len(domains)} domains ({domainsPercentage:.1f}%), accumulated: {accumulatedDomainsPercentage:.1f}%')


if __name__ == '__main__':
	main()
