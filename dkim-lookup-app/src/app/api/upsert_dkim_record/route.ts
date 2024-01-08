import { createPrismaClient } from '@/lib/db';
import { upsertRecord } from '@/lib/fetch_and_upsert';
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

const prisma = createPrismaClient();

export async function GET(request: NextRequest) {

	const authHeader = request.headers.get('authorization');
	if (authHeader !== `Bearer ${process.env.CRON_SECRET}`) {
		return new Response('Unauthorized', { status: 401 });
	}
	try {
		console.log(`request url: ${request.nextUrl}`);
		let domain = request.nextUrl.searchParams.get('domain');
		if (!domain) {
			throw 'missing domain parameter in query';
		}

		let selector = request.nextUrl.searchParams.get('selector');
		if (!selector) {
			throw 'missing selector parameter in query';
		}

		let value = request.nextUrl.searchParams.get('dkimValue');
		if (!value) {
			throw 'missing dkimValue parameter in query';
		}

		let timestamp = new Date()

		let added = await upsertRecord({ domain, selector, value, timestamp }, prisma);

		return NextResponse.json(
			{ message: `${added ? 'added' : 'updated'} ${domain}, ${selector}` },
			{ status: 200 }
		);
	} catch (error) {
		console.log(`error updating: ${error}`, error);
		return NextResponse.json(
			{ error: `${error}` },
			{ status: 500 }
		);
	}
}
