import { addDomainSelectorPair } from "@/lib/utils_server";
import { createInterface } from "node:readline"

async function main() {
	for await (const line of createInterface({ input: process.stdin })) {
		const [domain, selector] = line.split('\t');
		if (!selector || !domain) {
			console.log(`warning: selector or domain is empty`);
			continue;
		}
		let added = await addDomainSelectorPair(domain, selector, 'scraper');
		console.log(`domain: ${domain}, selector: ${selector}, added: ${added}`);
	}
}

main();
