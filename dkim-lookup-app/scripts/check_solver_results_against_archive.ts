import { RecordWithSelector, prisma } from "@/lib/db";
import { Prisma } from "@prisma/client";
import { parseDkimRecord } from "@/lib/utils";
import { readFileSync } from "node:fs";


async function process_line(line: string) {
	const [domain, selector, key] = line.split('\t');
	if (!selector || !domain || !key) {
		throw new Error(`selector or domain is empty`);
	}
	return [domain, selector, key];
}

export async function findRecords(domain: string, selector: string): Promise<RecordWithSelector[]> {
	return await prisma.dkimRecord.findMany({
		where: {
			domainSelectorPair: {
				AND: [
					{
						domain: {
							equals: domain,
							mode: Prisma.QueryMode.insensitive,
						}
					},
					{
						selector: {
							equals: selector,
							mode: Prisma.QueryMode.insensitive,
						}
					}
				]
			}
		},
		include: {
			domainSelectorPair: true
		}
	});
}

async function check_key(domain: string, selector: string, key: string) {
	let records = await findRecords(domain, selector);
	let new_p = parseDkimRecord(key).p;
	for (let record of records) {
		let existing_p = parseDkimRecord(record.value).p;
		if (new_p === existing_p) {
			return true;
		}
	}
	return false;
}


async function main() {
	console.log('reading DSPs from stdin');
	let existingDsps = [];
	let notExistingDsps = [];
	let knownDspsKeyArchiveMismatch = [];
	let knownDspsKeyArchiveMatch = [];

	const args = process.argv.slice(2);
	if (args.length == 1) {
		const filename = args[0];
		console.log(`reading DSPs from file: ${filename}`);
		const fileContent = readFileSync(filename, 'utf8');
		const lines = fileContent.split('\n').map(line => line.trim()).filter(line => line);
		for (let i = 0; i < lines.length; i++) {
			const line = lines[i];
			console.log(`processing line ${i + 1} of ${lines.length}`);
			const [domain, selector, solved_key] = await process_line(line);

			let searchResult = await prisma.domainSelectorPair.findFirst({
				where: {
					domain: domain,
					selector: selector
				}
			});
			if (searchResult) {
				existingDsps.push([domain, selector]);
				console.log(`domain: ${domain}, selector: ${selector}, already exists in archive, checking key`);
				if (await check_key(domain, selector, solved_key)) {
					knownDspsKeyArchiveMatch.push([domain, selector]);
				}
				else {
					console.log(`domain: ${domain}, selector: ${selector}, solved key does not match any of the keys in the archive, solved_key: ${solved_key}`);
					knownDspsKeyArchiveMismatch.push([domain, selector, solved_key]);
				}
			}
			else {
				console.log(`domain: ${domain}, selector: ${selector}, does not exist in archive`);
				notExistingDsps.push([domain, selector]);
			}
			console.log(`existingDsps: ${existingDsps.length}, notExistingDsps: ${notExistingDsps.length}, knownDspsKeyArchiveMatch: ${knownDspsKeyArchiveMatch.length}, knownDspsKeyArchiveMismatch: ${knownDspsKeyArchiveMismatch.length}`);
		}

		console.log();
		console.log(`existingDsps: ${existingDsps.length}`);
		for (let [domain, selector] of existingDsps) {
			console.log(`domain: ${domain}, selector: ${selector}`);
		}
		console.log();
		console.log(`notExistingDsps: ${notExistingDsps.length}`);
		for (let [domain, selector] of notExistingDsps) {
			console.log(`domain: ${domain}, selector: ${selector}`);
		}
		console.log();
		console.log(`knowns DSPs where the solved key matches any of the keys in the archive: ${knownDspsKeyArchiveMatch.length}`);
		for (let [domain, selector] of knownDspsKeyArchiveMatch) {
			console.log(`domain: ${domain}, selector: ${selector}`);
		}
		console.log();
		console.log(`knowns DSPs where the solved key does not match any of the keys in the archive: ${knownDspsKeyArchiveMismatch.length}`);
		for (let [domain, selector, solved_key] of knownDspsKeyArchiveMismatch) {
			console.log(`domain: ${domain}, selector: ${selector}, solved_key: ${solved_key}`);
		}
	}
}

main();
