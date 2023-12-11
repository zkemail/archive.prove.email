import { PrismaClient, Prisma, DkimRecord, Selector } from '@prisma/client'


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
