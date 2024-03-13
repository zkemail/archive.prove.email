import { DomainSelectorPair, Prisma } from "@prisma/client";
import { createDkimRecord, dspToString, prisma, recordToString, updateDspTimestamp } from "./db";
import { generateWitness } from "./generateWitness";
import { DnsDkimFetchResult } from "./utils";
import dns from 'dns';

async function refreshKey(dsp: DomainSelectorPair) {
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
export async function addDomainSelectorPair(domain: string, selector: string): Promise<boolean> {

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
		refreshKey(dsp);
		return false;
	}
	let dkimDnsRecord = await fetchDkimDnsRecord(domain, selector);
	if (!dkimDnsRecord) {
		console.log(`no dkim dns record found for ${selector}, ${domain}`);
		return false;
	}
	dsp = await prisma.domainSelectorPair.create({
		data: { domain, selector }
	})

	let dkimRecord = await createDkimRecord(dsp, dkimDnsRecord);

	console.log(`updating dsp timestamp for ${dsp.selector}, ${dsp.domain} to ${dkimDnsRecord.timestamp}`);
	updateDspTimestamp(dsp, dkimDnsRecord.timestamp);

	generateWitness(dsp, dkimRecord);
	return true;
}

export async function fetchDkimDnsRecord(domain: string, selector: string): Promise<DnsDkimFetchResult | null> {
	const resolver = new dns.promises.Resolver({ timeout: 2500 });
	const qname = `${selector}._domainkey.${domain}`;
	let response;
	try {
		response = await resolver.resolve(qname, 'TXT');
	}
	catch (error) {
		console.log(`error fetching ${qname}: ${error}`);
		return null;
	}
	if (response.length === 0) {
		console.log(`warning: no records found for ${qname}`);
		return null;
	}
	if (response.length > 1) {
		console.log(`warning: > 1 record found for ${qname}, using first one`);
	}
	console.log(`found dns record for ${qname}`);
	const dkimData = response[0].join('');
	const dkimRecord: DnsDkimFetchResult = {
		selector,
		domain,
		value: dkimData,
		timestamp: new Date(),
	};
	return dkimRecord;
}

/**
 * @returns true iff a record was added
 */
export async function fetchAndStoreDkimDnsRecord(dsp: DomainSelectorPair) {
	console.log(`fetching ${dsp.selector}._domainkey.${dsp.domain} from dns`);
	let dkimDnsRecord = await fetchDkimDnsRecord(dsp.domain, dsp.selector);
	if (!dkimDnsRecord) {
		return;
	}
	let dkimRecord = await prisma.dkimRecord.findFirst({
		where: {
			domainSelectorPair: dsp,
			value: dkimDnsRecord.value
		},
	});

	if (dkimRecord) {
		console.log(`record already exists: ${recordToString(dkimRecord)} for domain/selector pair ${dspToString(dsp)}, updating lastSeenAt to ${dkimDnsRecord.timestamp}`);
		await prisma.dkimRecord.update({
			where: { id: dkimRecord.id },
			data: { lastSeenAt: dkimDnsRecord.timestamp }
		});
	}
	else {
		dkimRecord = await createDkimRecord(dsp, dkimDnsRecord);
	}

	if (!dkimRecord.provenanceVerified) {
		generateWitness(dsp, dkimRecord);
	}
}
