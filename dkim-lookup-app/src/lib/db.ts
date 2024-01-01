import { PrismaClient, Prisma, DkimRecord, Selector } from '@prisma/client'

export function createPrismaClient(): PrismaClient {
	let prismaUrl = new URL(process.env.POSTGRES_PRISMA_URL as string);
	prismaUrl.searchParams.set('pool_timeout', '0');
	return new PrismaClient({
		datasources: {
			db: {
				url: prismaUrl.toString()
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
