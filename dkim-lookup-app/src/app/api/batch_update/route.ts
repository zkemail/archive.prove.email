import { fetchAndUpsertRecord } from '@/lib/fetch_and_upsert';
import { PrismaClient } from '@prisma/client';
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

const prisma = new PrismaClient();

export async function GET(request: NextRequest) {

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