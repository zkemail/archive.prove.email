#!/usr/bin/env python

import collections
from dataclasses import dataclass, field
from datetime import datetime, timezone
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
from db_util import load_dkim_records_with_dsps
import dkim  # type: ignore
from dkim.dnsplug import get_txt_dnspython  # type: ignore
import pickle
import xml.etree.ElementTree as ET


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


def load_mbox_files(mboxFiles: list[str]) -> list[mailbox.mbox]:
	loaded_mbox_files: list[mailbox.mbox] = []
	for mboxFile in mboxFiles:
		logging.info(f'loading {mboxFile}')
		mb = mailbox.mbox(mboxFile)
		len(mb)  # preload all messages
		loaded_mbox_files.append(mb)
	return loaded_mbox_files


@dataclass
class MsgInfo:
	date: datetime
	dkimDomain: str
	dkimSelector: str
	messageData: str | None = None


def extract_mbox_msg_info(message: mailbox.mboxMessage, include_RFC822_text: bool = False) -> MsgInfo | None:
	date = message['Date']
	if (type(date) != str):
		logging.debug(f'invalid Date header {date}')
		return None
	try:
		date = email.utils.parsedate_to_datetime(date)
	except ValueError as e:
		logging.warning(f'invalid Date header {date}: {e}')
		return None
	if date.tzinfo is None:
		# fix for that some emails have timezone= "-0000" (unspecified timezone), which generates "TypeError: can't compare offset-naive and offset-aware datetimes" on comparison
		logging.warning(f'unknown timezone for {date}, setting to UTC')
		date = date.replace(tzinfo=timezone.utc)

	dkimSignature = message['DKIM-Signature']
	if not dkimSignature:
		return None
	dkimRecord = decode_dkim_tag_value_list(dkimSignature)
	dkimDomain = dkimRecord['d']
	dkimSelector = dkimRecord['s']
	try:
		data = str(message) if include_RFC822_text else None
	except UnicodeEncodeError as e:
		logging.warning(f'UnicodeEncodeError: {e}')
		return None
	return MsgInfo(date, dkimDomain, dkimSelector, data)


def dkim_dns_statistics(mboxFiles: list[str], includeOnlyKeyboundSelectors: bool):
	buckets: dict[str, QnameBucket] = collections.defaultdict(QnameBucket)
	loaded_mbox_files = load_mbox_files(mboxFiles)

	logging.info('processing messages')
	for mboxMsg in tqdm(chain(*loaded_mbox_files), total=sum(len(mbox) for mbox in loaded_mbox_files)):
		mi = extract_mbox_msg_info(mboxMsg, include_RFC822_text=False)
		if not mi:
			continue
		if includeOnlyKeyboundSelectors and not is_keybound_selector_name(mi.dkimSelector):
			continue

		time_slot_key = date_to_time_slot(mi.date)
		bucket = buckets[time_slot_key]
		bucket.qnames.add(f"{mi.dkimSelector}._domainkey.{mi.dkimDomain}")

	for key, bucket in sorted(buckets.items()):
		logging.info(f'checking {len(bucket.qnames)} qnames for {key}')
		for qname in tqdm(bucket.qnames):
			if dsp_exists_on_dns(qname):
				bucket.active_qnames.add(qname)

	for key, bucket in sorted(buckets.items()):
		active = len(bucket.active_qnames)
		total = len(bucket.qnames)
		print(f'{key}: {active} active domainkeys of total {total} ({active / total * 100:.2f}%)')


class CachedDnsResolver:
	results: dict[str, bytes | None] = {}

	def __init__(self):
		self.resolver = dns.resolver.Resolver()
		self.resolver.timeout = 5
		self.resolver.lifetime = 5

	def resolve(self, qname: bytes, timeout: int = 5) -> bytes | None:
		qnameStr = qname.decode()
		try:
			return self.results[qnameStr]
		except KeyError:
			result = get_txt_dnspython(qnameStr, timeout)
			self.results[qnameStr] = result
			return result


@dataclass
class VerificationResult:
	msgInfo: MsgInfo
	verified: bool
	errors: list[str]


def verify_message(mi: MsgInfo, dnsResolver: CachedDnsResolver) -> VerificationResult:
	try:
		verified = dkim.verify(str(mi.messageData).encode(), dnsfunc=dnsResolver.resolve)  # type: ignore
		return VerificationResult(mi, verified, [])
	except (dkim.MessageFormatError, UnicodeEncodeError, UnboundLocalError) as e:
		return VerificationResult(mi, False, [str(e)])


def dkim_key_rotation(mboxFiles: list[str], excludeKeyboundSelectors: bool):
	loaded_mbox_files = load_mbox_files(mboxFiles)
	dsp_verification_results: dict[str, list[VerificationResult]] = collections.defaultdict(list)

	logging.info('processing messages')
	dnsResolver = CachedDnsResolver()
	for mboxMsg in tqdm(chain(*loaded_mbox_files), total=sum(len(mbox) for mbox in loaded_mbox_files)):
		mi = extract_mbox_msg_info(mboxMsg, include_RFC822_text=True)
		if not mi:
			continue
		if excludeKeyboundSelectors and is_keybound_selector_name(mi.dkimSelector):
			print(f'skipping keybound selector {mi.dkimSelector}')
			continue
		qname = f"{mi.dkimSelector}._domainkey.{mi.dkimDomain}"
		verification_result = verify_message(mi, dnsResolver)
		dsp_verification_results[qname].append(verification_result)
	return dsp_verification_results


def verification_results_to_svg(data: dict[str, list[VerificationResult]], output_file: str):
	xres = 800
	yres = 800
	start_date = datetime(2010, 1, 1).timestamp()
	end_date = datetime.now().timestamp()
	row_height_px = 10
	empty_rows = 2
	rows = yres // row_height_px - empty_rows

	def date_to_x(date: datetime) -> float:
		return (date.timestamp() - start_date) / (end_date - start_date) * xres

	def add_year_labels():
		for year in range(2010, 2025):
			x = date_to_x(datetime(year, 1, 1))
			label = ET.SubElement(root, "text", x=str(x + 3), y=str(row_height_px), fill="black")
			label.text = str(year)
			label.set("font-size", "10")
			ET.SubElement(root, "line", x1=str(x), y1="0", x2=str(x), y2=str(yres), stroke="black")

	def add_msg_rect(parent: ET.Element, row: int, date: datetime, duration: float, verified: bool):
		y = (row + empty_rows) * row_height_px
		color = 'green' if verified else 'red'
		x = date_to_x(date)
		width = duration / (end_date - start_date) * xres
		mid_y = y + row_height_px / 2
		ET.SubElement(root, "line", x1=str(x), y1=str(mid_y), x2=str(x + width), y2=str(mid_y), stroke=color)
		ET.SubElement(parent, "line", x1=str(x), y1=str(y), x2=str(x), y2=str(y + row_height_px), stroke=color)

	root = ET.Element("svg", width=str(xres), height=str(yres), xmlns="http://www.w3.org/2000/svg")
	ET.SubElement(root, "rect", x="0", y="0", width="100%", height="100%", fill="white")

	bars_group = ET.SubElement(root, "g")
	for row, (_label, results) in enumerate(data.items()):
		if row >= rows:
			break
		now = datetime.now()
		for i, r in enumerate(results):
			r = results[i]
			date1 = r.msgInfo.date
			date2 = results[i + 1].msgInfo.date if i + 1 < len(results) else now
			duration = date2.timestamp() - date1.timestamp()
			add_msg_rect(bars_group, row, date1, duration, r.verified)
	add_year_labels()
	tree = ET.ElementTree(root)
	ET.indent(root)
	tree.write(output_file)


def dkim_key_rotation_display_results(results_per_dsp: dict[str, list[VerificationResult]]):
	results_per_dsp = dict(sorted(results_per_dsp.items(), key=lambda x: len(x[1]), reverse=True))  # sort by number of messages
	for _qname, results in results_per_dsp.items():
		results.sort(key=lambda x: x.msgInfo.date)
	verification_results_to_svg(results_per_dsp, "output.svg")


def selector_statistics(tsvFile: str):
	domainSelectorDict: dict[str, list[str]] = collections.defaultdict(list)
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


async def dkim_key_reuse_statistics():
	from prisma import Prisma
	prisma = Prisma()
	await prisma.connect()
	records = await load_dkim_records_with_dsps(prisma)
	dkimKeyMap: dict[str, dict[str, set[str]]] = collections.defaultdict(lambda: collections.defaultdict(set))
	for record in records:
		if not record.keyData or not record.domainSelectorPair:
			continue
		dkimKeyMap[record.keyData][record.domainSelectorPair.selector].add(record.domainSelectorPair.domain)
	sorted_dkimKeyMap = dict(sorted(dkimKeyMap.items(), key=lambda x: sum(len(domains) for domains in x[1].values()), reverse=True))
	for dkim_key_index, (dkimKey, selectors_with_domains) in enumerate(sorted_dkimKeyMap.items()):
		number_of_dsps = sum(len(domains) for domains in selectors_with_domains.values())
		max_displayed_dkim_keys = 100
		if dkim_key_index >= max_displayed_dkim_keys:
			print(f'...and {len(sorted_dkimKeyMap) - max_displayed_dkim_keys} more DKIM keys')
			break
		print(f'dkim key: {dkimKey}')
		print(f'\t{number_of_dsps} domain/selector pairs')
		selectors_with_domains = dict(sorted(selectors_with_domains.items(), key=lambda x: len(x[1]), reverse=True))
		print(f'\t{len(selectors_with_domains)} selectors, breakdown:')
		for selector_index, (selector, domains) in enumerate(selectors_with_domains.items()):
			max_displayed_selectors = 5
			if selector_index >= max_displayed_selectors:
				print(f'\t\t...and {len(selectors_with_domains) - max_displayed_selectors} more selectors')
				break
			print(f'\t\t{selector}: {len(domains)} domains')
		print()


if __name__ == '__main__':
	logging.basicConfig(level=logging.INFO)
	logging.getLogger("httpx").setLevel(logging.WARNING)
	argparser = argparse.ArgumentParser(description='Collect various statistics about domains, selectors, and DKIM signatures')
	argparser.add_argument('--dkimDspStatsMbox', help='Show statistics about DKIM sigatures and domains for an .mbox file')

	argparser.add_argument('--dkimDnsStatsMbox', help='Show statistics about the DNS lookup status of domains/selectors for a set of .mbox files', type=str, nargs='+')
	argparser.add_argument(
	    '--includeOnlyKeyboundSelectors',
	    help='Use together with --dkimDnsStatsMbox to include only probably "keybound" selectors, such as "202306", and exclude "generic" selectors (such as "s1", "default", etc)',
	    action='store_true')

	argparser.add_argument('--testKeyboundSelectorClassifier', help='Test the selector classifier with a file with a list of selectors', type=argparse.FileType('r'))

	argparser.add_argument('--dkimKeyReuse', help='Show statistics about DKIM key reuse from the database', action='store_true')

	dkimKeyRotationHelp = 'For a set of .mbox files, try to DKIM verify each email back in time (against current DNS record) and see if there is a pattern that older emails before a certain date cannot be verified, while newer emails can. Data will be saved to verification_results.pickle. Use --dkimKeyRotationAnalyzeResults to analyze the data.'
	argparser.add_argument('--dkimKeyRotation', help=dkimKeyRotationHelp, type=str, nargs='+')
	argparser.add_argument('--excludeKeyboundSelectors', help='Use together with --dkimKeyRotation to exclude "keybound" selectors (such as "202306", etc)', action='store_true')
	tsvHelp = 'For a .tsv file with two columns(domain, selector), show a list of selectors, with percentage of domains convered for each selector. Also print accumulated percentage of domains covered when using the N most common selectors'
	argparser.add_argument('--dkimKeyRotationAnalyzeResults',
	                       help='Analyze the results of the .pickle output file from --dkimKeyRotation and display the results',
	                       type=argparse.FileType('r'))

	argparser.add_argument('--tsvFile', help=tsvHelp)
	args = argparser.parse_args()

	if (not args.dkimDspStatsMbox and not args.dkimDnsStatsMbox and not args.tsvFile and not args.testKeyboundSelectorClassifier and not args.dkimKeyReuse
	    and not args.dkimKeyRotation and not args.dkimKeyRotationAnalyzeResults):
		argparser.print_help(file=sys.stderr)
		sys.exit(1)

	if args.dkimDspStatsMbox:
		domain_statistics(args.dkimDspStatsMbox)

	if args.tsvFile:
		selector_statistics(args.tsvFile)

	if args.dkimDnsStatsMbox:
		dkim_dns_statistics(args.dkimDnsStatsMbox, args.includeOnlyKeyboundSelectors)

	if args.dkimKeyRotation:
		dsp_verification_results = dkim_key_rotation(args.dkimKeyRotation, args.excludeKeyboundSelectors)
		with open('verification_results.pickle', 'wb') as f:
			pickle.dump(dsp_verification_results, f)

	if args.dkimKeyRotationAnalyzeResults:
		with open(args.dkimKeyRotationAnalyzeResults.name, 'rb') as f:
			dsp_verification_results = pickle.load(f)
		dkim_key_rotation_display_results(dsp_verification_results)

	if args.testKeyboundSelectorClassifier:
		filename: TextIO = args.testKeyboundSelectorClassifier
		test_keybound_selector_classifier(filename)

	if args.dkimKeyReuse:
		import asyncio
		asyncio.run(dkim_key_reuse_statistics())
