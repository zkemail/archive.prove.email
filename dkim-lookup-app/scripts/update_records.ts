import { createPrismaClient } from '@/lib/db';
import { fetchAndUpsertRecord } from '@/lib/fetch_and_upsert';
import { PrismaClient } from '@prisma/client'

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

async function fetchDkimRecordsFromDns(domainSelectorsDict: Record<string, string[]>, prisma: PrismaClient) {
	for (const domain in domainSelectorsDict) {
		for (const selector of domainSelectorsDict[domain]) {
			await fetchAndUpsertRecord(domain, selector, prisma);
		}
	}
}

function main() {
	const tsvFiles = process.argv.slice(2);
	if (tsvFiles.length < 1) {
		console.log('usage: yarn update_records file1.tsv [file2.tsv ...]');
		process.exit(1);
	}
	console.log('loading domains and selectors');
	const domainSelectorsDict = {};
	for (const file of tsvFiles) {
		console.log(`loading domains and selectors from ${file}`);
		load_domains_and_selectors_from_tsv(domainSelectorsDict, file);
	}
	const prisma = createPrismaClient();
	console.log('fetching dkim records from dns');
	fetchDkimRecordsFromDns(domainSelectorsDict, prisma);
}

main();
