import { readFileSync } from 'node:fs';
import { addDomainSelectorPair } from '@/lib/utils_server';

function print_usage() {
	console.log('usage:');
	console.log('  pnpm update_records RECORDS_FILE SOURCE');
	console.log('    RECORDS_FILE: A .tsv file with domain and selector columns');
	console.log('    SOURCE_IDENTIFIER: A string to identify the source of the records');
	console.log('    START_LINE: The first line number (one-indexed) to process from the TSV file');
	console.log('example:');
	console.log('  pnpm update_records records.tsv batch_lookup_results 1');
}

async function main() {
	const args = process.argv.slice(2);
	if (args.length != 3) {
		print_usage();
		process.exit(1);
	}
	const filename = args[0];
	const sourceIdentifier = args[1];
	const startLine = parseInt(args[2]);
	console.log(`loading domains and selectors from ${filename}`);
	const fileContent = readFileSync(filename, 'utf8');
	const lines = fileContent.split('\n').map(line => line.trim()).filter(line => line);
	console.log('fetching dkim records from dns');
	for (let lineNumber = startLine; lineNumber <= lines.length; lineNumber++) {
		const line = lines[lineNumber - 1];
		console.error(`processing line ${lineNumber} of ${lines.length}`);
		const [domain, selector] = line.split('\t');
		if (!selector || !domain) {
			console.error(`warning: line ${lineNumber}, selector or domain is empty`);
			continue;
		}
		console.log(`updating ${domain}, ${selector}`);
		try {
			await addDomainSelectorPair(domain, selector, sourceIdentifier);
		}
		catch (error) {
			console.log(`error updating ${domain}, ${selector}: ${error}`);
		}
	}
}

main();
