import { readFileSync } from 'node:fs';
import { createPrismaClient } from '@/lib/db';
import { fetchAndUpsertRecord } from '@/lib/fetch_and_upsert';

// loads a list of selectors and a list of domains (the list of selectors can be generated with statistics.py)
// tries every selector with every domain and adds the domain/selector pair to the database if it doesn't already exist

function load_list(filename: string): string[] {
	const fileContents = readFileSync(filename, 'utf8');
	return fileContents.split('\n').map(line => line.trim()).filter(line => line);
}

async function main() {
	const inputFiles = process.argv.slice(2);
	if (inputFiles.length != 2) {
		console.log('usage: yarn try_selectors DOMAINS_LIST SELECTORS_LIST');
		process.exit(1);
	}
	let [domainsFilename, selectorsFilename] = inputFiles;
	const domains = load_list(domainsFilename);
	const selectors = readFileSync(selectorsFilename, 'utf8').split('\n').map(line => line.trim()).filter(line => line).map(line => line.split('\t')[0].trim());
	const prisma = createPrismaClient();

	let newFoundRecords = [];
	for (const domain of domains) {
		for (const selector of selectors) {
			try {
				if (await fetchAndUpsertRecord(domain, selector, prisma)) {
					newFoundRecords.push(`${selector}, ${domain}`);
				}
			}
			catch (error) {
				console.log(`error updating ${domain}, ${selector}: ${error}`);
			}
		}
	}

	console.log();
	console.log(`found ${newFoundRecords.length} new records:`);
	for (const record of newFoundRecords) {
		console.log(record);
	}
}

main();
