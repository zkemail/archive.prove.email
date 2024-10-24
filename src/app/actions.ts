"use server";
import { prisma } from "@/lib/db";
import { DkimRecord, DomainSelectorPair, Prisma } from "@prisma/client";

export type AutocompleteResults = string[];

export async function autocomplete(query: string) {
  if (!query) {
    return [];
  }

  const dsps: { domain: string }[] = await prisma.$queryRaw`SELECT DISTINCT domain FROM "DomainSelectorPair" WHERE domain ~* ${query} LIMIT 8;`;

  const results = dsps.map((d) => d.domain);

  return results.sort((a, b) => {
    const aStartsWithQuery = a.toLowerCase().startsWith(query.toLowerCase());
    const bStartsWithQuery = b.toLowerCase().startsWith(query.toLowerCase());

    return aStartsWithQuery === bStartsWithQuery ? 0 : aStartsWithQuery ? -1 : 1;
  });
}

export type RecordWithSelector = DkimRecord & { domainSelectorPair: DomainSelectorPair };

export async function findKeysPaginated(
  domainQuery: string,
  cursorIndex: number | null
): Promise<RecordWithSelector[]> {
  let cursorObj = {};
  if (cursorIndex) {
    cursorObj = {
      cursor: { id: cursorIndex },
      skip: 1,
    };
  }

  if (!domainQuery.includes(".") && !domainQuery.includes("-")) {
    return await prisma.dkimRecord.findMany({
      where: {
        domainSelectorPair: {
          domain: {
            startsWith: domainQuery,
          },
        },
      },
      include: {
        domainSelectorPair: true,
      },
      take: 25,
    });
  }

  const modifiedQuery = domainQuery.replace(/\./g, "-");
  const modifiedQuery2 = domainQuery.replace(/\-/g, ".");

  return await prisma.dkimRecord.findMany({
    where: {
      domainSelectorPair: {
        OR: [
          {
            domain: {
              contains: domainQuery,
              mode: Prisma.QueryMode.insensitive,
            },
          },
          {
            domain: {
              contains: modifiedQuery,
              mode: Prisma.QueryMode.insensitive,
            },
          },
          {
            domain: {
              contains: modifiedQuery2,
              mode: Prisma.QueryMode.insensitive,
            },
          },
        ],
      },
    },
    include: {
      domainSelectorPair: true,
    },
    take: 25,
    ...cursorObj,
  });
}
