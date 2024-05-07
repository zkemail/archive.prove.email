import { prisma } from "@/lib/db";
import { Prisma } from "@prisma/client";
import { parseDkimTagList } from "@/lib/utils";
import { readFileSync } from "node:fs";


async function process_line(line: string) {
	const [domain, selector, key] = line.split('\t');
	if (!selector || !domain || !key) {
		throw new Error(`selector or domain is empty`);
	}
	return [domain, selector, key];
}

export async function findKnownKeys(domain: string, selector: string) {
	let records = await prisma.dkimRecord.findMany({
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
	let result = [];
	for (let record of records) {
		const p = parseDkimTagList(record.value).p;
		if (p) {
			result.push(p);
		}
		else {
			console.log(`skip known key with empty/invalid value for domain: ${domain}, selector: ${selector}, record: ${record.value}`);
		}
	}
	return result;
}

async function main() {
	console.log('reading DSPs from stdin');
	let previouslyUnseenKeysFound = [];
	let solvedKeysNotMatchingArchive = [];
	let solvedKeysMatchingArchive = [];

	const args = process.argv.slice(2);
	if (args.length == 1) {
		const filename = args[0];
		console.log(`reading DSPs from file: ${filename}`);
		const fileContent = readFileSync(filename, 'utf8');
		const lines = fileContent.split('\n').map(line => line.trim()).filter(line => line);
		for (let i = 0; i < lines.length; i++) {
			const line = lines[i];
			const [domain, selector, solved_key_tag_list] = await process_line(line);
			const key_der_format = parseDkimTagList(solved_key_tag_list).p;
			const knownKeys = await findKnownKeys(domain, selector);
			if (knownKeys.length == 0) {
				previouslyUnseenKeysFound.push([domain, selector, solved_key_tag_list]);
			}
			else {
				if (knownKeys.includes(key_der_format)) {
					solvedKeysMatchingArchive.push([domain, selector, solved_key_tag_list]);
				}
				else {
					solvedKeysNotMatchingArchive.push([domain, selector, solved_key_tag_list]);
				}
			}
			console.log(`line ${i + 1} of ${lines.length}, previouslyUnseenKeysFound: ${previouslyUnseenKeysFound.length}, solvedKeysMatchingArchive: ${solvedKeysMatchingArchive.length}, solvedKeysNotMatchingArchive: ${solvedKeysNotMatchingArchive.length}`);
		}


		console.log();
		console.log(`solved keys for which there are no keys in the archive for the corresponding DSP: ${previouslyUnseenKeysFound.length}`);
		for (let [domain, selector, solved_key] of previouslyUnseenKeysFound) {
			console.log(`domain: ${domain}, selector: ${selector}, solved_key: ${solved_key}`);
		}
		console.log();
		console.log(`solved keys which match a key in the archive: ${solvedKeysMatchingArchive.length}`);
		for (let [domain, selector] of solvedKeysMatchingArchive) {
			console.log(`domain: ${domain}, selector: ${selector}`);
		}
		console.log();
		console.log(`solved keys for which there are keys in the archive for the corresponding DSP, but no match: ${solvedKeysNotMatchingArchive.length}`);
		for (let [domain, selector, solved_key] of solvedKeysNotMatchingArchive) {
			console.log(`domain: ${domain}, selector: ${selector}, solved_key: ${solved_key}`);
		}
	}
}

main();
