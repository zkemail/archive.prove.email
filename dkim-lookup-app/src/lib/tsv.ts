
export function load_domains_and_selectors_from_tsv(outputDict: { [domain: string]: string[] }, fileContent: string): void {
	const lines = fileContent.split('\n').map(line => line.trim()).filter(line => line);
	for (let i = 0; i < lines.length; i++) {
		const [domain, selector] = lines[i].split('\t');
		if (!selector || !domain) {
			console.error(`error: line ${i}, selector or domain is empty`);
			process.exit(1);
		}
		if (!outputDict[domain]) {
			outputDict[domain] = [];
		}
		if (!outputDict[domain].includes(selector)) {
			outputDict[domain].push(selector);
		}
	}
}
