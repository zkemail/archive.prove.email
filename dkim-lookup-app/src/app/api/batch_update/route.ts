import { createPrismaClient } from '@/lib/db';
import { fetchAndUpsertRecord } from '@/lib/fetch_and_upsert';
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

const prisma = createPrismaClient();


function getNumRecords() {
	let takeParam = process.env.BATCH_UPDATE_NUM_RECORDS;
	if (takeParam) {
		console.log(`using process.env.BATCH_UPDATE_NUM_RECORDS: ${takeParam}`);
		let take = Number(takeParam);
		if (isNaN(take)) {
			console.log(`invalid process.env.BATCH_UPDATE_NUM_RECORDS: ${takeParam}, using 0`);
			return 0;
		}
		return take;
	} else {
		console.log('process.env.BATCH_UPDATE_NUM_RECORDS not set, using 0');
		return 0;
	}
}

export async function GET(request: NextRequest) {

	const authHeader = request.headers.get('authorization');
	if (authHeader !== `Bearer ${process.env.CRON_SECRET}`) {
		return new Response('Unauthorized', { status: 401 });
	}

	let numRecords = getNumRecords();

	console.log(`updating ${numRecords} records`);

	try {
		const records = await prisma.selector.findMany(
			{
				orderBy: { lastRecordUpdate: 'asc' },
				take: numRecords,
			}
		);
		for (const result of records) {
			await fetchAndUpsertRecord(result.domain, result.name, prisma);
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