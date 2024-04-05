#!.venv/bin/python
# post-processing tool for the log output of dsp_onetime_batch.py

import argparse
from typing import TextIO


def post_process(logfiles: list[TextIO], tsv_output: TextIO, print_selectors_per_domain: bool, print_selector_count: bool):
	selector_count: dict[str, int] = {}
	selectors_per_domain: dict[str, set[str]] = {}
	for f in logfiles:
		for line in f:
			line = line.strip()
			if not line.startswith("DNS_BATCH_RESULT,"):
				continue
			_, domain, selector, _ = line.strip().split(",", maxsplit=3)
			print(f"{domain}\t{selector}", file=tsv_output)

			if selector in selector_count:
				selector_count[selector] += 1
			else:
				selector_count[selector] = 1

			if domain in selectors_per_domain:
				selectors_per_domain[domain].add(selector)
			else:
				selectors_per_domain[domain] = {selector}

	if print_selectors_per_domain:
		# print the selectors per domain, sorted by number of selectors
		selectors_per_domain = dict(sorted(selectors_per_domain.items(), key=lambda item: len(item[1]), reverse=True))
		for domain, selectors in selectors_per_domain.items():
			print(f"{domain} {selectors}")

	if print_selector_count:
		# print the selector count in descending order
		selector_count = dict(sorted(selector_count.items(), key=lambda item: item[1], reverse=True))
		for selector, count in selector_count.items():
			print(f"{selector} {count}")
			pass


# local entrypoint
if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument('logfiles', type=argparse.FileType('r'), nargs='+')
	parser.add_argument('--tsv-output', type=argparse.FileType('w'))
	parser.add_argument('--print-selectors-per-domain', action='store_true')
	parser.add_argument('--print-selector-count', action='store_true')
	args = parser.parse_args()
	post_process(args.logfiles, args.tsv_output, args.print_selectors_per_domain, args.print_selector_count)
