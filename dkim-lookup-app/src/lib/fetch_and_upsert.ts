import dns from 'dns';
import { Prisma, PrismaClient } from '@prisma/client'

const dnsPromises = dns.promises;


interface DnsDkimFetchResult {
	domain: string;
	selector: string;
	value: string;
	timestamp: Date;
}

// returns true iff a record was added
async function upsertRecord(record: DnsDkimFetchResult, prisma: PrismaClient): Promise<boolean> {
	let currentRecord = await prisma.dkimRecord.findFirst({
		where: {
			dkimDomain: {
				equals: record.domain,
				mode: Prisma.QueryMode.insensitive,
			},
			dkimSelector: {
				equals: record.selector,
				mode: Prisma.QueryMode.insensitive,
			},
			value: record.value
		},
	})
	if (currentRecord) {
		console.log(`record already exists: ${record.domain} ${record.selector}`);
		return false;
	}

	prisma.dkimRecord.create({
		data: {
			dkimDomain: record.domain,
			dkimSelector: record.selector,
			value: record.value,
			fetchedAt: record.timestamp,
		},
	}).then((record) => {
		console.log(`created record ${record.dkimDomain} ${record.dkimSelector}`);
		return true;
	}).catch((e) => {
		console.log(`could not create record: ${e}`);
	})
	return false;
}


// returns true iff a record was added
export async function fetchAndUpsertRecord(domain: string, selector: string, prisma: PrismaClient): Promise<boolean> {
	console.log(`fetching ${selector}._domainkey.${domain}`);
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


