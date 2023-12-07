import dns from 'dns';
import { Prisma, PrismaClient } from '@prisma/client'
const dnsPromises = dns.promises;
const prisma = new PrismaClient()

function load_domains_and_selectors_from_tsv(outputDict: { [domain: string]: string[] }, filename: string): void {
	const fs = require('fs');
	const fileContents = fs.readFileSync(filename, 'utf8');
	const lines = fileContents.split('\n');
	for (let [i, line] of lines.entries()) {
		line = line.trim();
		if (!line) {
			continue;
		}
		const [domain, selector] = line.split('\t');
		if (!selector || !domain) {
			console.error(`error: ${filename} line ${i}, selector or domain is empty`);
			process.exit(1);
		}
		if (!outputDict[domain]) {
			outputDict[domain] = [];
		}
		if (!outputDict[domain].includes(selector)) {
			outputDict[domain].push(selector);
		}
	}
}

interface DnsDkimFetchResult {
	domain: string;
	selector: string;
	value: string;
	timestamp: Date;
}

async function fetchDkimRecordsFromDns(domainSelectorsDict: Record<string, string[]>) {
	for (const domain in domainSelectorsDict) {
		for (const selector of domainSelectorsDict[domain]) {
			console.log(`fetching ${selector}._domainkey.${domain}`);
			const qname = `${selector}._domainkey.${domain}`;
			dnsPromises.resolve(qname, 'TXT').then((response) => {
				if (response.length === 0) {
					console.log(`warning: no records found for ${qname}`);
					return;
				}
				if (response.length > 1) {
					console.log(`warning: > 1 record found for ${qname}, using first one`);
					return;
				}
				const dkimData = response[0].join('');
				const dkimRecord: DnsDkimFetchResult = {
					selector,
					domain,
					value: dkimData,
					timestamp: new Date(),
				};
				addRecordToDb(dkimRecord);
			}).catch((e) => {
				console.log(`warning: dns resolver error: ${e}`);
			});
		}
	}
}

async function addRecordToDb(record: DnsDkimFetchResult) {
	let currentRecord = await prisma.dkimRecord.findFirst({
		where: {
			dkimDomain: {
				equals: record.domain,
				mode: Prisma.QueryMode.insensitive,
			},
			dkimSelector: {
				equals: record.selector,
				mode: Prisma.QueryMode.insensitive,
			},
			value: record.value
		},
	})
	if (currentRecord) {
		console.log(`record already exists: ${record.domain} ${record.selector}`);
		return;
	}

	prisma.dkimRecord.create({
		data: {
			dkimDomain: record.domain,
			dkimSelector: record.selector,
			value: record.value,
			fetchedAt: record.timestamp,
		},
	}).then((record) => {
		console.log(`created record ${record.dkimDomain} ${record.dkimSelector}`);
	}).catch((e) => {
		console.log(`could not create record: ${e}`);
	})
}

async function addRecordsToDb(records: DnsDkimFetchResult[]) {
	for (let record of records) {
		await addRecordToDb(record);
	}
}

function main() {
	const tsvFiles = process.argv.slice(2);
	if (tsvFiles.length < 1) {
		console.log('usage: publish_records.js file1.tsv [file2.tsv ...]');
		process.exit(1);
	}
	console.log('loading domains and selectors');
	const domainSelectorsDict = {};
	for (const file of tsvFiles) {
		console.log(`loading domains and selectors from ${file}`);
		load_domains_and_selectors_from_tsv(domainSelectorsDict, file);
	}
	console.log('fetching dkim records from dns');
	fetchDkimRecordsFromDns(domainSelectorsDict);
}

main();
