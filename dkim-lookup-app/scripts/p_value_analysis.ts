import { prisma } from "@/lib/db";
import { parseDkimTagList } from "@/lib/utils";

async function main() {
	let dkimRecords = []
	let nextCursor = 0;
	let take = 100000;
	while (true) {
		const cursorObj = (nextCursor == 0) ? null : { cursor: { id: nextCursor } };
		let recs = await prisma.dkimRecord.findMany({
			skip: (nextCursor == 0) ? 0 : 1,
			take: take,
			...cursorObj,
			include: { domainSelectorPair: true }
		})
		console.log(`batch: found ${recs.length} records`);
		if (recs.length == 0) {
			break;
		}
		for (let r of recs) {
			dkimRecords.push(r);
		}
		nextCursor = recs[recs.length - 1].id;
	}
	console.log(`found ${dkimRecords.length} records`);

	let invalid_records_without_p = []
	let invalid_records_with_p = []
	for (let r of dkimRecords) {
		let tagList = parseDkimTagList(r.value);
		if (!tagList.hasOwnProperty('p')) {
			if (r.value.includes('p=')) {
				invalid_records_with_p.push(r);
			}
			else {
				invalid_records_without_p.push(r);
			}
		}
	}
	console.log(`found ${invalid_records_without_p.length} records that do not contain p=`);
	for (let r of invalid_records_without_p) {
		console.log(`domain: ${r.domainSelectorPair.domain}, selector: ${r.domainSelectorPair.selector}, value: ${r.value}`);
	}

	console.log();
	console.log(`found ${invalid_records_with_p.length} records that contain p=, but where p cannot be parsed`);
	for (let r of invalid_records_with_p) {
		console.log(`domain: ${r.domainSelectorPair.domain}, selector: ${r.domainSelectorPair.selector}, value: ${r.value}`);
	}
}

main();
