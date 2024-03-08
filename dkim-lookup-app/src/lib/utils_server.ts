import { DomainSelectorPair } from "@prisma/client";
import { fetchDkimDnsRecord } from "./fetchDkimDnsRecord";
import { createDkimRecord, dspToString, prisma, recordToString } from "./db";
import { generateWitness } from "./generateWitness";

/**
 * @returns true iff a record was added
 */
export async function fetchAndStoreDkimDnsRecord(dsp: DomainSelectorPair) {
	console.log(`fetching ${dsp.selector}._domainkey.${dsp.domain} from dns`);
	let dkimDnsRecord = await fetchDkimDnsRecord(dsp.domain, dsp.selector);
	if (!dkimDnsRecord) {
		console.log(`no record found for ${dsp.selector}, ${dsp.domain}`);
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
