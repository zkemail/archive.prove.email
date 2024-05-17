#!.venv/bin/python
# post-processing tool for the log output of dsp_onetime_batch.py

import argparse
from typing import TextIO


def post_process(logfiles: list[TextIO], tsv_output: TextIO, print_selectors_per_domain: bool, print_selector_count: bool):
	selector_count: dict[str, int] = {}
	selectors_per_domain: dict[str, set[str]] = {}
	dsp_list: list[tuple[str, str]] = []
	for f in logfiles:
		for line in f:
			line = line.strip()
			if not line.startswith("DNS_BATCH_RESULT,"):
				continue
			_, domain, selector, _ = line.strip().split(",", maxsplit=3)
			dsp_list.append((domain, selector))

			if selector in selector_count:
				selector_count[selector] += 1
			else:
				selector_count[selector] = 1

			if domain in selectors_per_domain:
				selectors_per_domain[domain].add(selector)
			else:
				selectors_per_domain[domain] = {selector}
	filtered_domains: set[str] = set()

	selectors_per_domain = dict(sorted(selectors_per_domain.items(), key=lambda item: len(item[1]), reverse=True))
	for domain, selectors in selectors_per_domain.items():
		if print_selectors_per_domain:
			print(f"{domain} {len(selectors)}")

		# Some domains repond to every call to <selector>._domainkey.example.com,
		# regardless of the selector value, which results in 1000s of results per domain.
		# The current statistics show that the domains with the most "real" selectors
		# have about 30 selectors, so we filter out domains with more than 100 selectors:
		if len(selectors) > 100:
			filtered_domains.add(domain)

	selectors_per_domain = {k: v for k, v in selectors_per_domain.items() if k not in filtered_domains}

	# remove filtered domains from dsp_list
	dsp_list = [(domain, selector) for domain, selector in dsp_list if domain not in filtered_domains]

	# calculate average number of selectors per domain
	average_selectors_per_domain = sum(len(selectors) for selectors in selectors_per_domain.values()) / len(selectors_per_domain)
	print(f"Average number of selectors per domain: {average_selectors_per_domain}")

	if print_selector_count:
		# print the selector count in descending order
		selector_count = dict(sorted(selector_count.items(), key=lambda item: item[1], reverse=True))
		for selector, count in selector_count.items():
			print(f"{selector} {count}")
			pass

	if tsv_output:
		for domain, selector in dsp_list:
			print(f"{domain}\t{selector}", file=tsv_output)


# local entrypoint
if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument('logfiles', type=argparse.FileType('r'), nargs='+')
	parser.add_argument('--tsv-output', type=argparse.FileType('w'))
	parser.add_argument('--print-selectors-per-domain', action='store_true')
	parser.add_argument('--print-selector-count', action='store_true')
	args = parser.parse_args()
	post_process(args.logfiles, args.tsv_output, args.print_selectors_per_domain, args.print_selector_count)
