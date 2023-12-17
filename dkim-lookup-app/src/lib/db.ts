import { PrismaClient, Prisma, DkimRecord, Selector } from '@prisma/client'

export function createPrismaClient(): PrismaClient {
	return new PrismaClient({
		datasources: {
			db: {
				url: process.env.POSTGRES_PRISMA_URL + '&pool_timeout=0'
			},
		},
	});
}

export type RecordWithSelector = (DkimRecord & { selector: Selector });

export async function findRecords(domainQuery: string, prisma: PrismaClient): Promise<RecordWithSelector[]> {
	return await prisma.dkimRecord.findMany({
		where: {
			selector: {
				domain: {
					equals: domainQuery,
					mode: Prisma.QueryMode.insensitive,
				},
			}
		},
		include: {
			selector: true
		}
	});
}
