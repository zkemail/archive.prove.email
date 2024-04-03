# this tool searches for DKIM DNS records for each combination of domains and selectors in the provided input files

# prerequisites: install the Modal Python package, see https://modal.com/docs/guide
#
# pip install modal
# pip install dnspython
#
# example remote run:
# modal run dsp_onetime_batch.py --domains-filename domains.txt --selectors-filename selectors.txt --no-sparse > output.txt
#
# example local run:
# python dsp_onetime_batch.py --domains-filename domains.txt --selectors-filename selectors.txt > output.txt
#
# example of post-processing the result to count the number of each selector:
# python dsp_onetime_batch.py --analyze-results output.txt


import argparse
import datetime
import sys
import time
import modal

stub = modal.Stub("dsp-onetime-batch")
dns_image = (modal.Image.debian_slim(python_version="3.10").pip_install("dnspython"))


def find_dkim_field(txtRecords: list[str]) -> str | None:
	for record in txtRecords:
		version = record.split(';', maxsplit=1)[0].strip()
		if version == 'v=DKIM1':
			return record
	return None


def resolve_qname(qname: str):
	import dns.exception
	import dns.resolver
	import dns.rdatatype

	try:
		response = dns.resolver.resolve(qname, dns.rdatatype.TXT)
		if len(response) == 0:
			#print(f'warning: no records found for {qname}')
			return
		txtRecords: list[str] = []
		for i in range(len(response)):
			txtRecords.append(b''.join(response[i].strings).decode())  # type: ignore
		dkimData = find_dkim_field(txtRecords)
		if dkimData is None:
			#print(f'no DKIM1 record found for {qname}')
			return
		for tag in dkimData.split(';'):
			if tag.strip() == "p=":
				# empty p= tag
				return
		tsv_row = f'{qname} {dkimData}\n'  # extra newline at the end as a workaround for that the stdout from modal.com somtimes has merged lines if there is just one newline
		print(tsv_row)
	except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers, dns.exception.Timeout) as _e:
		#print(f'warning: dns resolver error: {e}')
		pass


def process_domain(domain: str, selectors: list[str]):
	for selector in selectors:
		resolve_qname(f"{selector}._domainkey.{domain}")


@stub.function(image=dns_image)  # type: ignore
def process_domain_wrapper(domain: str, selectors: list[str]):
	process_domain(domain, selectors)


def run_batch_job(domains_filename: str, selectors_filename: str, *, local: bool = False, sparse: bool = False):
	with open(selectors_filename) as f:
		selectors = f.read().splitlines()
	with open(domains_filename) as f:
		domains = f.read().splitlines()
	if sparse:
		domains = domains[0::1000]
	start_time = time.time()
	print(f"started at {datetime.datetime.fromtimestamp(start_time).isoformat(' ', timespec='seconds')}", file=sys.stderr)
	for index, domain in enumerate(domains):
		elapsed_hrs = (time.time() - start_time) / 3600
		time_left_hrs = ((len(domains) - index) * elapsed_hrs / index) if index > 0 else 0
		print(f"processing domain {index}, elapsed: {elapsed_hrs:.2f}, time left: {time_left_hrs:.2f} hours, {domain}", file=sys.stderr)
		if local:
			process_domain(domain, selectors)
		else:
			process_domain_wrapper.spawn(domain, selectors)


# remote entrypoint
@stub.local_entrypoint()  # type: ignore
def main(domains_filename: str, selectors_filename: str, sparse: bool):
	run_batch_job(domains_filename, selectors_filename, sparse=sparse)


def analyze_results(results_file: str):
	with open(results_file) as f:
		batch_run_result = f.read()
	lines = batch_run_result.splitlines()

	# count the number of each selector
	selector_count: dict[str, int] = {}
	for line in lines:
		line = line.strip()
		if not "DKIM1" in line:
			continue
		qname, _ = line.split(" ", maxsplit=1)
		selector = qname.split("._domainkey.", maxsplit=1)[0]
		if selector in selector_count:
			selector_count[selector] += 1
		else:
			selector_count[selector] = 1

	# print the selector count in descending order
	selector_count = dict(sorted(selector_count.items(), key=lambda item: item[1], reverse=True))
	for selector, count in selector_count.items():
		print(f"{selector} {count}")


# local entrypoint
if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument('--domains-filename', type=str)
	parser.add_argument('--selectors-filename', type=str)
	parser.add_argument('--analyze-results', type=str, dest='results_file')
	args = parser.parse_args()
	if args.results_file:
		analyze_results(args.results_file)
	else:
		run_batch_job(args.domains_filename, args.selectors_filename, local=True)
