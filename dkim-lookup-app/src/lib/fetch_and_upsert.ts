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
	console.log(`updated selector ${selectorToString(updatedSelector)}`);
}

async function upsertRecord(newRecord: DnsDkimFetchResult, prisma: PrismaClient): Promise<boolean> {
	console.log(`upserting record, ${newRecord.selector}, ${newRecord.domain}`);
	let currentSelector = await prisma.selector.findFirst({
		where: {
			domain: {
				equals: newRecord.domain,
				mode: Prisma.QueryMode.insensitive,
			},
			name: {
				equals: newRecord.selector,
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
				domain: newRecord.domain,
				name: newRecord.selector
			}
		})
		console.log(`created selector ${selectorToString(currentSelector)}`);
	}

	let currentRecord = await prisma.dkimRecord.findFirst({
		where: {
			selector: currentSelector,
			value: newRecord.value
		},
	})
	if (currentRecord) {
		console.log(`record already exists: ${recordToString(currentRecord)} for selector ${selectorToString(currentSelector)}`);
		updateSelectorTimestamp(currentSelector, new Date(), prisma);
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

	updateSelectorTimestamp(currentSelector, dkimRecord.fetchedAt, prisma);
	return false;
}

/**
 * @returns true iff a record was added
 */
export async function fetchAndUpsertRecord(domain: string, selector: string, prisma: PrismaClient): Promise<boolean> {
	console.log(`fetching ${selector}._domainkey.${domain} from dns`);
	const qname = `${selector}._domainkey.${domain}`;
	dnsPromises.resolve(qname, 'TXT').then((response) => {
		if (response.length === 0) {
			console.log(`warning: no records found for ${qname}`);
			return;
		}
		if (response.length > 1) {
			console.log(`warning: > 1 record found for ${qname}, using first one`);
			return;
		}
		console.log(`found dns record for ${qname}`);
		const dkimData = response[0].join('');
		const dkimRecord: DnsDkimFetchResult = {
			selector,
			domain,
			value: dkimData,
			timestamp: new Date(),
		};
		return upsertRecord(dkimRecord, prisma);
	}).catch((e) => {
		console.log(`warning: dns resolver error: ${e}`);
	});
	return false;
}
