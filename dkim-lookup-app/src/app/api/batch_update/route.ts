import { prisma } from '@/lib/db';
import { fetchAndStoreDkimDnsRecord } from '@/lib/fetch_and_upsert';
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

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
		const dsps = await prisma.domainSelectorPair.findMany(
			{
				orderBy: { lastRecordUpdate: 'asc' },
				take: numRecords,
			}
		);
		for (const dsp of dsps) {
			try {
				await fetchAndStoreDkimDnsRecord(dsp);
			}
			catch (error) {
				console.log(`error updating ${dsp.domain}, ${dsp.selector}: ${error}`);
			}
		}
		return NextResponse.json(
			{ updatedRecords: dsps },
			{ status: 200 }
		);
	} catch (error) {
		return NextResponse.json(
			{ error: error },
			{ status: 500 }
		);
	}
}