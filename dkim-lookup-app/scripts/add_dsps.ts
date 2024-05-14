import { addDomainSelectorPair } from "@/lib/utils_server";
import { createInterface } from "node:readline"
import { readFileSync } from 'node:fs';


async function process_line(line: string) {
	const [domain, selector] = line.split('\t');
	if (!selector || !domain) {
		console.log(`warning: selector or domain is empty`);
		return;
	}
	try {
		let added = await addDomainSelectorPair(domain, selector, 'scraper');
		console.log(`domain: ${domain}, selector: ${selector}, added: ${added}`);
	}
	catch (error: any) {
		console.error(`add_dsps.ts error: ${error}`);
	}
}

async function main() {
	const args = process.argv.slice(2);
	if (args.length == 1) {
		const filename = args[0];
		console.log(`reading DSPs from file: ${filename}`);
		const fileContent = readFileSync(filename, 'utf8');
		const lines = fileContent.split('\n').map(line => line.trim()).filter(line => line);
		for (let i = 0; i < lines.length; i++) {
			const line = lines[i];
			console.log(`processing line ${i + 1} of ${lines.length}`);
			await process_line(line);
		}
	}
	else {
		console.log('reading DSPs from stdin');
		for await (const line of createInterface({ input: process.stdin })) {
			await process_line(line);
		}
	}
}

main();
