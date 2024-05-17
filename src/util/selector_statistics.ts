import { prisma } from "@/lib/db";
import path from "path";
import fs from "fs";

// usage:
// pnpm tsx src/util/selector_statistics.ts OUTPUT_DIRECTORY

async function main() {

	const outputDirectory = process.argv[2];
	console.log(`Output directory: ${outputDirectory}`);

	let dsps = await prisma.domainSelectorPair.findMany();
	let selectors = dsps.map(dsp => dsp.selector);

	let uniqueSelectors = new Set(selectors);
	const selectorStatisticsSummaryStream = fs.createWriteStream(path.join(outputDirectory, 'selector_statistics_summary.txt'));
	selectorStatisticsSummaryStream.write(`Found ${dsps.length} domain/selector pairs\n`);
	selectorStatisticsSummaryStream.write(`Found ${uniqueSelectors.size} unique selectors\n\n`);

	const uniqueSelectorsStream = fs.createWriteStream(path.join(outputDirectory, 'unique_selectors.txt'));
	const uniqueSelectorsExcludingHashesStream = fs.createWriteStream(path.join(outputDirectory, 'unique_selectors_excluding_hashes.txt'));

	// sort the unique selectors alphabetically
	let sortedUniqueSelectors = Array.from(uniqueSelectors).sort();
	for (let selector of sortedUniqueSelectors) {
		uniqueSelectorsStream.write(`${selector}\n`);
		if (selector.length != 32) {
			uniqueSelectorsExcludingHashesStream.write(`${selector}\n`);
		}
	}
	uniqueSelectorsStream.end();
	uniqueSelectorsExcludingHashesStream.end();

	// count the number of times each selector appears
	let selectorCounts = selectors.reduce((acc, selector) => {
		acc[selector] = (acc[selector] || 0) + 1;
		return acc;
	}, {} as { [selector: string]: number });

	const uniqueSelectorsCount = Object.keys(selectorCounts).length;

	// sort the selectors by the number of times they appear, and secondarily alphabetically
	let sortedSelectors = Object.keys(selectorCounts).sort((a, b) => {
		if (selectorCounts[b] === selectorCounts[a]) {
			return a.localeCompare(b);
		}
		return selectorCounts[b] - selectorCounts[a];
	});

	const selectorFrequenciesStream = fs.createWriteStream(path.join(outputDirectory, 'selector_frequencies.txt'));
	const selectorFrequenciesGt1Stream = fs.createWriteStream(path.join(outputDirectory, 'selector_frequencies_gt1.txt'));

	selectorFrequenciesStream.write('FREQUENCY\tSELECTOR\n');
	for (let selector of sortedSelectors) {
		selectorFrequenciesStream.write(`${selectorCounts[selector]}\t${selector}\n`);
		if (selectorCounts[selector] > 1) {
			selectorFrequenciesGt1Stream.write(`${selector}\n`);
		}
	}
	selectorFrequenciesStream.end();
	selectorFrequenciesGt1Stream.end();

	// count the number of selectors that appear each number of times
	let countCounts = Object.values(selectorCounts).reduce((acc, count) => {
		acc[count] = (acc[count] || 0) + 1;
		return acc;
	}, {} as { [count: number]: number });

	// sort the counts by the number of selectors that appear that number of times
	let sortedCounts = Object.keys(countCounts).sort((a, b) => countCounts[parseInt(b)] - countCounts[parseInt(a)]);
	for (let count of sortedCounts) {
		const selectorCount = countCounts[parseInt(count)];
		const selectorPercent = (selectorCount / uniqueSelectorsCount * 100).toFixed(2);
		selectorStatisticsSummaryStream.write(`${selectorCount} selectors (${selectorPercent}%) occur ${count} times\n`);
	}
}

main();
