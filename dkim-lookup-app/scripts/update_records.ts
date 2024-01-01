import { createPrismaClient } from '@/lib/db';
import { fetchAndUpsertRecord } from '@/lib/fetch_and_upsert';
import { PrismaClient } from '@prisma/client'
import { readFileSync } from 'node:fs';

function load_domains_and_selectors_from_tsv(outputDict: { [domain: string]: string[] }, filename: string): void {
	const fileContents = readFileSync(filename, 'utf8');
	const lines = fileContents.split('\n').map(line => line.trim()).filter(line => line);
	for (let i = 0; i < lines.length; i++) {
		const [domain, selector] = lines[i].split('\t');
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
