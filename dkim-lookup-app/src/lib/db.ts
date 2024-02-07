import { PrismaClient, Prisma, DkimRecord, Selector } from '@prisma/client'

const createPrismaClient = () => {
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

declare global {
	var prismaClient: undefined | ReturnType<typeof createPrismaClient>
}
export const prisma = globalThis.prismaClient ?? createPrismaClient();
if (process.env.NODE_ENV !== 'production') {
	globalThis.prismaClient = prisma;
}


export type RecordWithSelector = (DkimRecord & { selector: Selector });

export async function findRecords(domainQuery: string): Promise<RecordWithSelector[]> {
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
