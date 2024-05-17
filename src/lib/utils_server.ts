import { DomainSelectorPair, Prisma } from "@prisma/client";
import { createDkimRecord, dspToString, prisma, recordToString, updateDspTimestamp } from "./db";
import { generateWitness } from "./generateWitness";
import { DnsDkimFetchResult, SourceIdentifier } from "./utils";
import dns from 'dns';

async function refreshKeysFromDns(dsp: DomainSelectorPair) {
	let now = new Date();
	let oneHourAgo = new Date(now.getTime() - 1000 * 60 * 60);
	if (!dsp.lastRecordUpdate || dsp.lastRecordUpdate < oneHourAgo) {
		console.log(`refresh key for ${dspToString(dsp)}`);
		await fetchAndStoreDkimDnsRecord(dsp);
		updateDspTimestamp(dsp, new Date());
	}
}

/**
 * @returns true iff a record was added
 */
export async function addDomainSelectorPair(domain: string, selector: string, sourceIdentifier: SourceIdentifier): Promise<boolean> {

	domain = domain.toLowerCase();
	selector = selector.toLowerCase();

	// check if record exists
	let dsp = await prisma.domainSelectorPair.findFirst({
		where: {
			domain: {
				equals: domain,
				mode: Prisma.QueryMode.insensitive,
			},
			selector: {
				equals: selector,
				mode: Prisma.QueryMode.insensitive
			}
		}
	});
	if (dsp) {
		console.log(`found domain/selector pair ${dspToString(dsp)}`);
		refreshKeysFromDns(dsp);
		return false;
	}
	let records = await fetchDkimDnsRecord(domain, selector);
	if (records.length === 0) {
		console.log(`no dkim dns record found for ${selector}, ${domain}`);
		return false;
	}
	console.log(`found ${records.length} dkim dns records for ${selector}, ${domain}, adding DSP and records`);

	let newDsp = await prisma.domainSelectorPair.create({
		data: {
			domain,
			selector,
			sourceIdentifier,
			lastRecordUpdate: new Date(),
			records: {
				create: [...records.map(record => ({
					value: record.value,
					firstSeenAt: record.timestamp,
					lastSeenAt: record.timestamp,
					provenanceVerified: false
				}))]
			}
		},
		include: {
			records: true
		}
	})
	newDsp.records.forEach(record => {
		generateWitness(newDsp, record);
	});

	return true;
}

export async function fetchDkimDnsRecord(domain: string, selector: string): Promise<DnsDkimFetchResult[]> {
	const resolver = new dns.promises.Resolver({ timeout: 2500 });
	const qname = `${selector}._domainkey.${domain}`;
	let records;
	try {
		records = (await resolver.resolve(qname, 'TXT')).map(record => record.join(''));
	}
	catch (error) {
		console.log(`error fetching ${qname}: ${error}`);
		return [];
	}
	console.log(`found: ${records.length} records for ${qname}`);
	let result = [];
	for (let record of records) {
		console.log(`record: ${record}`);
		console.log(`found dns record for ${qname}`);
		const dkimRecord: DnsDkimFetchResult = {
			selector,
			domain,
			value: record,
			timestamp: new Date(),
		};
		result.push(dkimRecord);
	}
	return result
}

/**
 * @returns true iff a record was added
 */
export async function fetchAndStoreDkimDnsRecord(dsp: DomainSelectorPair) {
	console.log(`fetching ${dsp.selector}._domainkey.${dsp.domain} from dns`);
	let dnsRecords = await fetchDkimDnsRecord(dsp.domain, dsp.selector);
	for (let dnsRecord of dnsRecords) {
		let dbRecord = await prisma.dkimRecord.findFirst({
			where: {
				domainSelectorPair: dsp,
				value: dnsRecord.value
			},
		});

		if (dbRecord) {
			console.log(`record already exists: ${recordToString(dbRecord)} for domain/selector pair ${dspToString(dsp)}, updating lastSeenAt to ${dnsRecord.timestamp}`);
			await prisma.dkimRecord.update({
				where: { id: dbRecord.id },
				data: { lastSeenAt: dnsRecord.timestamp }
			});
		}
		else {
			dbRecord = await createDkimRecord(dsp, dnsRecord);
		}

		if (!dbRecord.provenanceVerified) {
			generateWitness(dsp, dbRecord);
		}
	}
}
