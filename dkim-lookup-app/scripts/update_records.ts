import axios from 'axios';
import { createPrismaClient } from '@/lib/db';
import { fetchAndUpsertRecord, fetchRecord } from '@/lib/fetch_and_upsert';
import { PrismaClient } from '@prisma/client'
import { readFileSync } from 'node:fs';
import { load_domains_and_selectors_from_tsv } from '@/lib/tsv';

abstract class Updater {
	abstract update(domain: string, selector: string): Promise<void>;
}

class PrismaUpdater extends Updater {
	prismaClient: PrismaClient = createPrismaClient();
	async update(domain: string, selector: string) {
		try {
			await fetchAndUpsertRecord(domain, selector, this.prismaClient);
		}
		catch (error) {
			console.log(`error updating ${domain}, ${selector}: ${error}`);
		}
	}
}

class ApiUpdater extends Updater {
	apiEndpoint: string;
	constructor(apiHostname: string) {
		super();
		this.apiEndpoint = apiHostname;
	}

	async update(domain: string, selector: string) {
		let dkimRecord = await fetchRecord(domain, selector);
		if (!dkimRecord) {
			console.log(`no record found for ${selector}, ${domain}`);
			return;
		}

		let url = new URL(this.apiEndpoint);
		url.searchParams.set('domain', domain);
		url.searchParams.set('selector', selector);
		url.searchParams.set('dkimValue', dkimRecord.value);
		console.log(`calling ${url}`);
		await axios.get(url.toString(), { headers: { 'Authorization': `Bearer ${process.env.CRON_SECRET}` } })
			.then(response => {
				console.log('response:', response.data);
			}).catch(error => {
				console.error(`error calling ${url}`);
				console.error(error.message);
				if (error.response) {
					console.error(error.response.data);
				}
				process.exit(1);
			});
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
	console.log('  yarn update_records records_file [api_endpoint]');
	console.log('    records_file: A .tsv file with domain and selector columns');
	console.log('    api_endpoint: URL of the API endpoint. If not provided, direct database access will be used');
	console.log('example:');
	console.log('  yarn update_records records.tsv http://localhost:3000/api/upsert_dkim_record');
}

function main() {
	const args = process.argv.slice(2);
	if (!(args.length == 1 || args.length == 2)) {
		print_usage();
		process.exit(1);
	}
	let filename = args[0];
	let api_hostname = (args.length >= 2) ? args[1] : null;
	const domainSelectorsDict = {};
	console.log(`loading domains and selectors from ${filename}`);
	const updater = api_hostname ? new ApiUpdater(api_hostname) : new PrismaUpdater();
	load_domains_and_selectors_from_tsv(domainSelectorsDict, filename);
	console.log('fetching dkim records from dns');
	fetchDkimRecordsFromDns(domainSelectorsDict, updater);
}

main();
