export function parseDkimRecord(dkimValue: string): Record<string, string | null> {
	const result: Record<string, string | null> = {};
	const parts = dkimValue.split(';');
	for (const part of parts) {
		const [key, value] = part.split('=');
		result[key.trim()] = value?.trim() || null;
	}
	return result;
}


export type DomainSelectorPair = {domain: string, selector: string};

export function load_domains_and_selectors_from_tsv(fileContent: string): DomainSelectorPair[] {
	let result = [];
	const lines = fileContent.split('\n').map(line => line.trim()).filter(line => line);
	for (let i = 0; i < lines.length; i++) {
		const [domain, selector] = lines[i].split('\t');
		if (!selector || !domain) {
			console.error(`error: line ${i}, selector or domain is empty`);
			continue;
		}
		result.push({domain, selector});
	}
	return result;
}

export function getCanonicalRecordString(dsp: DomainSelectorPair, dkimRecordValue: string): string {
	return `${dsp.selector}._domainkey.${dsp.domain} TXT "${dkimRecordValue}"`;
}
