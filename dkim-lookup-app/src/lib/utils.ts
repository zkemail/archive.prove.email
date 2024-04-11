import { ReadonlyHeaders } from "next/dist/server/web/spec-extension/adapters/headers";
import { RateLimiterMemory } from "rate-limiter-flexible";

export type DomainAndSelector = {
	domain: string,
	selector: string
};

export interface DnsDkimFetchResult {
	domain: string;
	selector: string;
	value: string;
	timestamp: Date;
}

export function parseDkimRecord(dkimValue: string): Record<string, string | null> {
	const result: Record<string, string | null> = {};
	const parts = dkimValue.split(';');
	for (const part of parts) {
		const [key, value] = part.split('=');
		result[key.trim()] = value?.trim() || null;
	}
	return result;
}

export function load_domains_and_selectors_from_tsv(fileContent: string): DomainAndSelector[] {
	let result = [];
	const lines = fileContent.split('\n').map(line => line.trim()).filter(line => line);
	for (let i = 0; i < lines.length; i++) {
		const [domain, selector] = lines[i].split('\t');
		if (!selector || !domain) {
			console.error(`error: line ${i}, selector or domain is empty`);
			continue;
		}
		result.push({ domain, selector });
	}
	return result;
}

export function getCanonicalRecordString(dsp: DomainAndSelector, dkimRecordValue: string): string {
	return `${dsp.selector}._domainkey.${dsp.domain} TXT "${dkimRecordValue}"`;
}


function dataToMessage(data: any): string {
	if (!data) {
		return '';
	}
	if (data?.message) {
		return `${data.message}`;
	}
	if (data instanceof Object) {
		return JSON.stringify(data);
	}
	return `${data}`;
}

export function axiosErrorMessage(error: any): string {
	if (error.response) {
		const data = error?.response?.data;
		const message = dataToMessage(data);
		return `${error} - ${message}`;
	}
	else {
		return `${error.message}`;
	}
}

export async function checkRateLimiter(rateLimiter: RateLimiterMemory, headers: ReadonlyHeaders, consumePoints: number) {
	const forwardedFor = headers.get("x-forwarded-for");
	if (forwardedFor) {
		const clientIp = forwardedFor.split(',')[0];
		await rateLimiter.consume(clientIp, consumePoints);
	}
}

export function isValidDate(year: number, month: number, day: number) {
	const date = new Date(year, month - 1, day);
	return date.getFullYear() === year && date.getMonth() === month - 1 && date.getDate() === day;
}

export function truncate(s: string, maxLength: number) {
	if (s.length > maxLength) {
		return s.slice(0, Math.max(maxLength, 3) - 3) + "...";
	} else {
		return s;
	}
}

export const SourceIdentifiers = ['top_1m_lookup', 'api', 'selector_guesser', 'seed', 'try_selectors', 'api_auto', 'unknown'] as const;
export type SourceIdentifier = typeof SourceIdentifiers[number];

export function stringToSourceIdentifier(s: string): SourceIdentifier {
	const sourceIdentifier = SourceIdentifiers.find(id => id === s);
	if (sourceIdentifier) {
		return sourceIdentifier;
	}
	return 'unknown';
}

export function sourceIdentifierToHumanReadable(sourceIdentifierStr: string) {
	switch (stringToSourceIdentifier(sourceIdentifierStr)) {
		case 'top_1m_lookup':
			return 'Scraped';
		case 'api':
			return 'Inbox upload';
		case 'api_auto':
			return 'Inbox upload';
		case 'selector_guesser':
			return 'Selector guesser';
		case 'seed':
			return 'Seed';
		case 'try_selectors':
			return 'Try selectors';
		case 'unknown':
			return 'Unknown';
	}
}
