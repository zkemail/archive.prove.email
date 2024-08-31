"use server";
import { prisma } from "@/lib/db";
import { DkimRecord, DomainSelectorPair, Prisma } from "@prisma/client";

export type AutocompleteResults = string[];

export async function autocomplete(query: string) {
  if (!query) {
    return [];
  }
  const modifiedQuery = query.replace(/\./g, "-");
  const modifiedQuery2 = query.replace(/\-/g, ".");

  let dsps = await prisma.domainSelectorPair.findMany({
    distinct: ["domain"],
    where: {
      OR: [
        {
          domain: {
            contains: query,
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
    orderBy: { domain: "asc" },
    take: 8,
  });
  const results = Array.from(new Set(dsps.map((d) => d.domain)));

  const sortedResults = results.sort((a, b) => {
    const aStartsWithQuery = a.toLowerCase().startsWith(query.toLowerCase());
    const bStartsWithQuery = b.toLowerCase().startsWith(query.toLowerCase());

    if (aStartsWithQuery && !bStartsWithQuery) {
      return -1;
    }
    if (!aStartsWithQuery && bStartsWithQuery) {
      return 1;
    }
    return 0;
  });
  return sortedResults;
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

  const modifiedQuery = domainQuery.replace(/\./g, "-");
  const modifiedQuery2 = domainQuery.replace(/\-/g, ".");

  const results = await prisma.dkimRecord.findMany({
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
    take: 50,
    ...cursorObj,
  });

  const sortedResults = results.sort((a, b) => {
    const aStartsWithQuery = a.domainSelectorPair.domain.toLowerCase().startsWith(domainQuery.toLowerCase());
    const bStartsWithQuery = b.domainSelectorPair.domain.toLowerCase().startsWith(domainQuery.toLowerCase());

    if (aStartsWithQuery && !bStartsWithQuery) {
      return -1;
    }
    if (!aStartsWithQuery && bStartsWithQuery) {
      return 1;
    }
    if (a.domainSelectorPair.selector < b.domainSelectorPair.selector) {
      return -1;
    }
    if (a.domainSelectorPair.selector > b.domainSelectorPair.selector) {
      return 1;
    }
    return 0;
  });

  return sortedResults;
}
