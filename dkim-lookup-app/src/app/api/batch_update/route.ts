import { createPrismaClient } from '@/lib/db';
import { fetchAndUpsertRecord } from '@/lib/fetch_and_upsert';
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

const prisma = createPrismaClient();

export async function GET(request: NextRequest) {

	const authHeader = request.headers.get('authorization');
	if (authHeader !== `Bearer ${process.env.CRON_SECRET}`) {
		return new Response('Unauthorized', { status: 401 });
	}

	try {
		const records = await prisma.selector.findMany(
			{
				orderBy: { lastRecordUpdate: 'asc' },
				take: 10
			}
		);
		for (const result of records) {
			fetchAndUpsertRecord(result.domain, result.name, prisma);
		}
		return NextResponse.json(
			{ updatedRecords: records },
			{ status: 200 }
		);
	} catch (error) {
		return NextResponse.json(
			{ error: error },
			{ status: 500 }
		);
	}
}