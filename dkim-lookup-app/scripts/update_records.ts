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

function print_usage() {
	console.log('usage:');
	console.log('  yarn update_records records_file');
	console.log('    records_file: A .tsv file with domain and selector columns');
	console.log('example:');
	console.log('  yarn update_records records.tsv');
}

async function main() {
	const args = process.argv.slice(2);
	if (args.length != 1) {
		print_usage();
		process.exit(1);
	}
	let filename = args[0];
	console.log(`loading domains and selectors from ${filename}`);
	const updater = new PrismaUpdater();
	const fileContents = readFileSync(filename, 'utf8');
	let domainSelectorPairs = load_domains_and_selectors_from_tsv(fileContents);
	console.log('fetching dkim records from dns');
	for (const p of domainSelectorPairs) {
		await updater.update(p.domain, p.selector);
	}
}

main();
