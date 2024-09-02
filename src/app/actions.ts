"use server";
import { prisma } from "@/lib/db";
import { DkimRecord, DomainSelectorPair, Prisma } from "@prisma/client";

export type AutocompleteResults = string[];

export async function autocomplete(query: string) {
	if (!query) {
		return [];
	}
	let dsps = await prisma.domainSelectorPair.findMany({
		distinct: ['domain'],
		where: { domain: { startsWith: query } },
		orderBy: { domain: 'asc' },
		take: 8
	});
	return Array.from(new Set(dsps.map(d => d.domain)));
}

export type RecordWithSelector = (DkimRecord & { domainSelectorPair: DomainSelectorPair });

export async function findKeysPaginated(domainQuery: string, cursorIndex: number | null): Promise<RecordWithSelector[]> {
	let cursorObj = {};
	if (cursorIndex) {
		cursorObj = {
			cursor: { id: cursorIndex },
			skip: 1
		}
	}
	return await prisma.dkimRecord.findMany({
		where: {
			domainSelectorPair: {
				OR: [
					{
						domain: {
							equals: domainQuery,
							mode: Prisma.QueryMode.insensitive,
						}
					},
					{
						domain: {
							endsWith: '.' + domainQuery,
							mode: Prisma.QueryMode.insensitive,
						}
					}
				]
			}
		},
		include: {
			domainSelectorPair: true
		},
		take: 50,
		...cursorObj,
	});
}
