import dns from 'dns';
import { Prisma, PrismaClient, Selector, DkimRecord } from '@prisma/client'

const dnsPromises = dns.promises;


interface DnsDkimFetchResult {
	domain: string;
	selector: string;
	value: string;
	timestamp: Date;
}

function selectorToString(selector: Selector): string {
	return `#${selector.id}, ${selector.domain}, ${selector.name}`;
}

function recordToString(record: DkimRecord): string {
	let value = record.value;
	const maxLen = 50;
	let valueTruncated = (value.length > maxLen) ? value.slice(0, maxLen - 1) + '…' : value;
	return `#${record.id}, "${valueTruncated}"`;
}

async function updateSelectorTimestamp(selector: Selector, timestamp: Date, prisma: PrismaClient) {
	let updatedSelector = await prisma.selector.update({
		where: {
			id: selector.id
		},
		data: {
			lastRecordUpdate: timestamp
		}
	})
	console.log(`updated selector timestamp ${selectorToString(updatedSelector)}`);
}

async function findOrCreateSelector(domain: string, selector: string, prisma: PrismaClient): Promise<Selector> {
	let currentSelector = await prisma.selector.findFirst({
		where: {
			domain: {
				equals: domain,
				mode: Prisma.QueryMode.insensitive,
			},
			name: {
				equals: selector,
				mode: Prisma.QueryMode.insensitive
			}
		}
	});
	if (currentSelector) {
		console.log(`found selector ${selectorToString(currentSelector)}`);
	}
	else {
		currentSelector = await prisma.selector.create({
			data: {
				domain: domain,
				name: selector
			}
		})
		console.log(`created selector ${selectorToString(currentSelector)}`);
	}
	return currentSelector;
}

async function upsertRecord(newRecord: DnsDkimFetchResult, prisma: PrismaClient): Promise<boolean> {
	console.log(`upserting record, ${newRecord.selector}, ${newRecord.domain}`);
	let currentSelector = await findOrCreateSelector(newRecord.domain, newRecord.selector, prisma);
	let currentRecord = await prisma.dkimRecord.findFirst({
		where: {
			selector: currentSelector,
			value: newRecord.value
		},
	})
	if (currentRecord) {
		console.log(`record already exists: ${recordToString(currentRecord)} for selector ${selectorToString(currentSelector)}`);
		return false;
	}
	console.log(`creating record for selector ${selectorToString(currentSelector)}`);

	let dkimRecord = await prisma.dkimRecord.create({
		data: {
			selectorId: currentSelector.id,
			value: newRecord.value,
			fetchedAt: newRecord.timestamp,
		},
	})
	console.log(`created dkim record ${recordToString(dkimRecord)} for selector ${selectorToString(currentSelector)}`);
	return true;
}

/**
 * @returns true iff a record was added
 */
export async function fetchAndUpsertRecord(domain: string, selector: string, prisma: PrismaClient): Promise<boolean> {
	console.log(`fetching ${selector}._domainkey.${domain} from dns`);
	const qname = `${selector}._domainkey.${domain}`;

	try {
		let response = await dnsPromises.resolve(qname, 'TXT');
		if (response.length === 0) {
			console.log(`warning: no records found for ${qname}`);
			return false;
		}
		if (response.length > 1) {
			console.log(`warning: > 1 record found for ${qname}, using first one`);
			return false;
		}
		console.log(`found dns record for ${qname}`);
		const dkimData = response[0].join('');
		const dkimRecord: DnsDkimFetchResult = {
			selector,
			domain,
			value: dkimData,
			timestamp: new Date(),
		};
		let updated = await upsertRecord(dkimRecord, prisma);
		console.log(`updating selector timestamp for ${selector}, ${domain}`);
		let selectorInDb = await findOrCreateSelector(domain, selector, prisma);
		updateSelectorTimestamp(selectorInDb, new Date(), prisma);
		return updated;
	}
	catch(e) {
		console.log(`fetchAndUpsertRecord error: ${e}`);
	}
	return false;
}
