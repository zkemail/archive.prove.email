"use server";
import { prisma } from "@/lib/db";

export type AutocompleteResults = string[];

export async function autocomplete(query: string) {
	if (!query) {
		return [];
	}
	let dsps = await prisma.domainSelectorPair.findMany({
		distinct: ['domain'],
		where: { domain: { startsWith: query } },
		take: 8
	});
	return Array.from(new Set(dsps.map(d => d.domain)));
}
