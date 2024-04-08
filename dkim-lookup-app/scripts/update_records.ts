import { readFileSync } from 'node:fs';
import { load_domains_and_selectors_from_tsv } from '@/lib/utils';
import { addDomainSelectorPair } from '@/lib/utils_server';

abstract class Updater {
	abstract update(domain: string, selector: string, sourceIdentifier: string): Promise<void>;
}

class PrismaUpdater extends Updater {
	async update(domain: string, selector: string, sourceIdentifier: string) {
		try {
			await addDomainSelectorPair(domain, selector, sourceIdentifier);
		}
		catch (error) {
			console.log(`error updating ${domain}, ${selector}: ${error}`);
		}
	}
}

function print_usage() {
	console.log('usage:');
	console.log('  pnpm update_records RECORDS_FILE SOURCE');
	console.log('    RECORDS_FILE: A .tsv file with domain and selector columns');
	console.log('    SOURCE_IDENTIFIER: A string to identify the source of the records');
	console.log('example:');
	console.log('  pnpm update_records records.tsv batch_lookup_results');
}

async function main() {
	const args = process.argv.slice(2);
	if (args.length != 2) {
		print_usage();
		process.exit(1);
	}
	let filename = args[0];
	let sourceIdentifier = args[1];
	console.log(`loading domains and selectors from ${filename}`);
	const updater = new PrismaUpdater();
	const fileContents = readFileSync(filename, 'utf8');
	let domainSelectorPairs = load_domains_and_selectors_from_tsv(fileContents);
	console.log('fetching dkim records from dns');
	for (const p of domainSelectorPairs) {
		await updater.update(p.domain, p.selector, sourceIdentifier);
	}
}

main();
