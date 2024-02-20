import dns from 'dns';
import { Prisma, DomainSelectorPair, DkimRecord } from '@prisma/client'
import { prisma } from './db';
import { getCanonicalRecordString } from './utils';
import { WitnessClient } from '@witnessco/client';

let resolver = new dns.promises.Resolver({ timeout: 2500 });

interface DnsDkimFetchResult {
	domain: string;
	selector: string;
	value: string;
	timestamp: Date;
}

function dspToString(dsp: DomainSelectorPair): string {
	return `#${dsp.id}, ${dsp.domain}, ${dsp.selector}`;
}

function recordToString(record: DkimRecord): string {
	let value = record.value;
	const maxLen = 50;
	let valueTruncated = (value.length > maxLen) ? value.slice(0, maxLen - 1) + '…' : value;
	return `#${record.id}, "${valueTruncated}"`;
}

async function updateDspTimestamp(dsp: DomainSelectorPair, timestamp: Date) {
	let updatedSelector = await prisma.domainSelectorPair.update({
		where: {
			id: dsp.id
		},
		data: {
			lastRecordUpdate: timestamp
		}
	})
	console.log(`updated dsp timestamp ${dspToString(updatedSelector)}`);
}

export async function fetchDkimDnsRecord(domain: string, selector: string): Promise<DnsDkimFetchResult | null> {
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


async function generateWitness(dsp: DomainSelectorPair, dkimRecord: DkimRecord) {
	let canonicalRecordString = getCanonicalRecordString(dsp, dkimRecord.value);
	const witness = new WitnessClient(process.env.WITNESS_API_KEY);
	const leafHash = witness.hash(canonicalRecordString);
	const timestamp = await witness.postLeafAndGetTimestamp(leafHash);
	console.log(`leaf ${leafHash} was timestamped at ${timestamp}`);
	const proof = await witness.getProofForLeafHash(leafHash);
	const verified = await witness.verifyProofChain(proof);
	if (!verified) {
		throw 'proof chain verification failed';
	}
	console.log(`proof chain verified, setting provenanceVerified for ${recordToString(dkimRecord)}`);
	await prisma.dkimRecord.update({
		where: {
			id: dkimRecord.id
		},
		data: {
			provenanceVerified: true
		}
	});
}

async function createDkimRecord(dsp: DomainSelectorPair, dkimDsnRecord: DnsDkimFetchResult) {
	let dkimRecord = await prisma.dkimRecord.create({
		data: {
			domainSelectorPairId: dsp.id,
			value: dkimDsnRecord.value,
			firstSeenAt: dkimDsnRecord.timestamp,
			provenanceVerified: false
		},
	});
	console.log(`created dkim record ${recordToString(dkimRecord)} for domain/selector pair ${dspToString(dsp)}`);
	return dkimRecord;
}

/**
 * @returns true iff a record was added
 */
export async function fetchAndStoreDkimDnsRecord(dsp: DomainSelectorPair) {
	console.log(`fetching ${dsp.selector}._domainkey.${dsp.domain} from dns`);
	let dkimDnsRecord = await fetchDkimDnsRecord(dsp.domain, dsp.selector);
	if (!dkimDnsRecord) {
		console.log(`no record found for ${dsp.selector}, ${dsp.domain}`);
		return false;
	}
	let dkimRecord = await prisma.dkimRecord.findFirst({
		where: {
			domainSelectorPair: dsp,
			value: dkimDnsRecord.value
		},
	});

	if (dkimRecord) {
		console.log(`record already exists: ${recordToString(dkimRecord)} for domain/selector pair ${dspToString(dsp)}`);
	}
	else {
		dkimRecord = await createDkimRecord(dsp, dkimDnsRecord);
	}

	console.log(`updating dsp timestamp for ${dsp.selector}, ${dsp.domain} to ${dkimDnsRecord.timestamp}`);
	updateDspTimestamp(dsp, dkimDnsRecord.timestamp);

	if (!dkimRecord.provenanceVerified) {
		generateWitness(dsp, dkimRecord);
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
