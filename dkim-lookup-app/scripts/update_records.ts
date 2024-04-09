import { readFileSync } from 'node:fs';
import { AddDspAdminRequest, AddDspAdminResponse } from '@/app/api/dsp_admin/route';
import axios from 'axios';

function print_usage() {
	console.log('usage:');
	console.log('  pnpm update_records API_URL RECORDS_FILE SOURCE_IDENTIFIER START_LINE');
	console.log('    API_URL: The URL of the API endpoint to call');
	console.log('    RECORDS_FILE: A .tsv file with domain and selector columns');
	console.log('    SOURCE_IDENTIFIER: A string to identify the source of the records');
	console.log('    START_LINE: The first line number (one-indexed) to process from the TSV file');
	console.log('example:');
	console.log('  pnpm update_records http://localhost:3000/api/dsp_admin records.tsv batch_lookup_results 1');
}

async function main() {
	const args = process.argv.slice(2);
	if (args.length != 4) {
		print_usage();
		process.exit(1);
	}
	const url = args[0];
	const filename = args[1];
	const sourceIdentifier = args[2];
	const startLine = parseInt(args[3]);
	console.log(`loading domains and selectors from ${filename}`);
	const fileContent = readFileSync(filename, 'utf8');
	const lines = fileContent.split('\n').map(line => line.trim()).filter(line => line);
	console.log('fetching dkim records from dns');
	let addedPairs = 0;


	const config = {
		headers: { Authorization: `Bearer ${process.env.CRON_SECRET}` }
	};
	console.log(`config: ${JSON.stringify(config)}`)

	for (let lineNumber = startLine; lineNumber <= lines.length; lineNumber++) {
		const line = lines[lineNumber - 1];
		console.log(`processing line ${lineNumber} of ${lines.length}`);
		const [domain, selector] = line.split('\t');
		if (!selector || !domain) {
			console.log(`warning: line ${lineNumber}, selector or domain is empty`);
			continue;
		}

		const dsp = { domain, selector };
		const request = { sourceIdentifier, ...dsp };
		try {
			let response = await axios.post<AddDspAdminResponse>(url, request as AddDspAdminRequest, config);
			if (response.data.added) {
				console.log(`${JSON.stringify(dsp)} was added to the registry`);
				addedPairs++;
			}
		}
		catch (error: any) {
			console.log(`error calling ${url}:`, error);
			process.exit(1);
		}

	}
	console.log(`added ${addedPairs} domain-selector pairs`);
}

main();
