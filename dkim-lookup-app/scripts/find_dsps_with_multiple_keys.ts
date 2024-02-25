import { prisma } from "@/lib/db";

async function main() {
	let dsps = await prisma.domainSelectorPair.findMany();
	console.log(`found ${dsps.length} domain/selector pairs`);
	for (let dsp of dsps) {
		let records = await prisma.dkimRecord.findMany({ where: { domainSelectorPairId: dsp.id } });
		if (records.length > 1) {
			console.log(`found ${records.length} keys for ${dsp.domain}, ${dsp.selector}`);
			for (let record of records) {
				console.log(`#${record.id}: ${record.value}`)
			}
			console.log();
		}
	}
}

main();
