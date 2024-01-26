import { prisma } from '@/lib/db';
import { fetchAndUpsertRecord } from '@/lib/fetch_and_upsert';
import { readFileSync } from 'node:fs';
import { load_domains_and_selectors_from_tsv } from '@/lib/tsv';

abstract class Updater {
	abstract update(domain: string, selector: string): Promise<void>;
}

class PrismaUpdater extends Updater {
	async update(domain: string, selector: string) {
		try {
			await fetchAndUpsertRecord(domain, selector, prisma);
		}
		catch (error) {
			console.log(`error updating ${domain}, ${selector}: ${error}`);
		}
	}
}

async function fetchDkimRecordsFromDns(domainSelectorsDict: Record<string, string[]>, updater: Updater) {
	for (const domain in domainSelectorsDict) {
		for (const selector of domainSelectorsDict[domain]) {
			await updater.update(domain, selector);
		}
	}
}

function print_usage() {
	console.log('usage:');
	console.log('  yarn update_records records_file');
	console.log('    records_file: A .tsv file with domain and selector columns');
	console.log('example:');
	console.log('  yarn update_records records.tsv');
}

function main() {
	const args = process.argv.slice(2);
	if (args.length != 1) {
		print_usage();
		process.exit(1);
	}
	let filename = args[0];
	const domainSelectorsDict = {};
	console.log(`loading domains and selectors from ${filename}`);
	const updater = new PrismaUpdater();
	const fileContents = readFileSync(filename, 'utf8');
	load_domains_and_selectors_from_tsv(domainSelectorsDict, fileContents);
	console.log('fetching dkim records from dns');
	fetchDkimRecordsFromDns(domainSelectorsDict, updater);
}

main();
