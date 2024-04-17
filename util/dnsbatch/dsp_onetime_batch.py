#!.venv/bin/python
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

import argparse
import datetime
import sys
import time
import modal
import threading
import queue

stub = modal.Stub("dsp-onetime-batch")
dns_image = (modal.Image.debian_slim(python_version="3.10").pip_install("dnspython"))


def parse_tags(txtData: str) -> dict[str, str]:
	dkimData: dict[str, str] = {}
	for tag in txtData.split(';'):
		tag = tag.strip()
		if not tag:
			continue
		try:
			key, value = tag.split('=', maxsplit=1)
			dkimData[key] = value
		except ValueError:
			#print(f'warning: invalid tag: {tag}, {txtData}')
			continue
		dkimData[key] = value
	return dkimData


def resolve_qname(domain: str, selector: str, local: bool):
	import dns.exception
	import dns.resolver
	import dns.rdatatype

	qname = f"{selector}._domainkey.{domain}"

	try:
		response = dns.resolver.resolve(qname, dns.rdatatype.TXT)
		if len(response) == 0:
			#print(f'warning: no records found for {qname}')
			return
		txtData = ""
		for i in range(len(response)):
			txtData += b''.join(response[i].strings).decode()  # type: ignore
			txtData += ";"
		tags = parse_tags(txtData)
		if 'p' not in tags:
			#print(f'warning: no p= tag found for {qname}, {txtData}')
			return
		if tags['p'] == "":
			#print(f'warning: empty p= tag found for {qname}, {txtData}')
			return
		if tags['p'] in ["reject", "none"]:
			#print(f'info: p=reject found for {qname}, {txtData}')
			return
		if len(tags['p']) < 10:
			print(f'# short p= tag found for {qname}, {txtData}\n')
			return
		if local:
			print(f'{domain}\t{selector}')
		else:
			tsv_row = f'DNS_BATCH_RESULT,{domain},{selector},{txtData}\n'  # extra newline at the end as a workaround for that the stdout from modal.com somtimes has merged lines if there is just one newline
			print(tsv_row)
		sys.stdout.flush()
	except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers, dns.exception.Timeout) as _e:
		#print(f'warning: dns resolver error: {e}')
		pass


q: "queue.Queue[tuple[str, str]]" = queue.Queue(maxsize=20)


def worker():
	while True:
		qname = q.get()
		resolve_qname(qname[0], qname[1], local=True)
		q.task_done()


def process_domain_threaded(domain: str, selectors: list[str]):
	for selector in selectors:
		q.put((domain, selector))
	return len(selectors)


@stub.function(image=dns_image)  # type: ignore
def process_domain_modal(domain: str, selectors: list[str]):
	for selector in selectors:
		resolve_qname(domain, selector, local=False)


def run_batch_job(domains_filename: str, selectors_filename: str, *, local: bool = False, sparse: bool = False, start_line: int):
	with open(selectors_filename) as f:
		selectors = f.read().splitlines()
	with open(domains_filename) as f:
		domains = f.read().splitlines()
	if sparse:
		domains = domains[0::1000]
	start_time = time.time()

	if local:
		for _i in range(20):
			t = threading.Thread(target=worker, daemon=True)
			t.start()

	start_index = start_line - 1
	print(f"started at {datetime.datetime.fromtimestamp(start_time).isoformat(' ', timespec='seconds')}", file=sys.stderr)
	for index in range(start_index, len(domains)):
		domain = domains[index]
		elapsed_hrs = (time.time() - start_time) / 3600
		time_left_hrs = ((len(domains) - index) * elapsed_hrs / (index - start_index)) if index > start_index else 0
		print(f"processing domain {index}, elapsed: {elapsed_hrs:.2f}, time left: {time_left_hrs:.2f} hours, {domain}", file=sys.stderr)
		if local:
			process_domain_threaded(domain, selectors)
		else:
			process_domain_modal.spawn(domain, selectors)
	q.join()


# remote entrypoint
@stub.local_entrypoint()  # type: ignore
def main(domains_filename: str, selectors_filename: str, sparse: bool):
	run_batch_job(domains_filename, selectors_filename, sparse=sparse, start_line=1)


# local entrypoint
if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument('--domains-filename', type=str)
	parser.add_argument('--selectors-filename', type=str)
	parser.add_argument('--start-line', type=int, default=0)
	args = parser.parse_args()
	run_batch_job(args.domains_filename, args.selectors_filename, local=True, start_line=args.start_line)
