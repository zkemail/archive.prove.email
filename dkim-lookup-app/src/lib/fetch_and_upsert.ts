import dns from 'dns';
import { Prisma, DomainSelectorPair, DkimRecord } from '@prisma/client'
import { prisma } from './db';
import { WitnessClient } from '@witnesswtf/client';
import { getCanonicalRecordString } from './utils';

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
	console.log(`updated domain/selector pair timestamp ${dspToString(updatedSelector)}`);
}

async function findOrCreateDomainSelectorPair(domain: string, selector: string): Promise<DomainSelectorPair> {
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
	}
	else {
		dsp = await prisma.domainSelectorPair.create({
			data: { domain, selector }
		})
		console.log(`created domain/selector pair ${dspToString(dsp)}`);
	}
	return dsp;
}

export async function fetchRecord(domain: string, selector: string): Promise<DnsDkimFetchResult | null> {
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


async function generateWitness(canonicalRecordString: string) {
	const witness = new WitnessClient();
	const leafHash = witness.hash(canonicalRecordString);
	const timestamp = await witness.postLeafAndGetTimestamp(leafHash);
	console.log(`leaf ${leafHash} was timestamped at ${timestamp}`);
	const proof = await witness.getProofForLeafHash(leafHash);
	const verified = await witness.verifyProofChain(proof);
	if (!verified) {
		throw 'proof chain verification failed';
	}
}

/**
 * @returns true iff a record was added
 */
export async function fetchAndUpsertRecord(domain: string, selector: string): Promise<boolean> {
	console.log(`fetching ${selector}._domainkey.${domain} from dns`);
	let dkimRecord = await fetchRecord(domain, selector);
	if (!dkimRecord) {
		console.log(`no record found for ${selector}, ${domain}`);
		return false;
	}
	let dsp = await findOrCreateDomainSelectorPair(domain, selector);

	let dbRecord = await prisma.dkimRecord.findFirst({
		where: {
			domainSelectorPair: dsp,
			value: dkimRecord.value
		},
	});

	if (dbRecord) {
		console.log(`record already exists: ${recordToString(dbRecord)} for domain/selector pair ${dspToString(dsp)}`);
	}
	else {
		dbRecord = await prisma.dkimRecord.create({
			data: {
				domainSelectorPairId: dsp.id,
				value: dkimRecord.value,
				fetchedAt: dkimRecord.timestamp,
				provenanceVerified: false
			},
		});
		console.log(`created dkim record ${recordToString(dbRecord)} for domain/selector pair ${dspToString(dsp)}`);
	}

	console.log(`updating selector timestamp for ${dsp.selector}, ${dsp.domain} to ${dkimRecord.timestamp}`);
	updateDspTimestamp(dsp, dkimRecord.timestamp);

	if (!dbRecord.provenanceVerified) {
		let canonicalRecordString = getCanonicalRecordString({ domain, selector }, dkimRecord.value);
		generateWitness(canonicalRecordString);
		await prisma.dkimRecord.update({
			where: {
				id: dbRecord.id
			},
			data: {
				provenanceVerified: true
			}
		});
		return true;
	}
	return false;
}
