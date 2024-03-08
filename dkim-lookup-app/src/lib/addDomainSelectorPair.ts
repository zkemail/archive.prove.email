import { createDkimRecord, dspToString, prisma, updateDspTimestamp } from './db';
import { DomainSelectorPair, Prisma } from '@prisma/client';
import { fetchDkimDnsRecord } from './fetchDkimDnsRecord';
import { generateWitness } from './generateWitness';
import { fetchAndStoreDkimDnsRecord } from './utils_server';

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
