import { createPrismaClient } from '@/lib/db';
import { upsertRecord } from '@/lib/fetch_and_upsert';
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { getServerSession } from "next-auth/next"
import { authOptions } from "@/app/auth";

const prisma = createPrismaClient();

export async function GET(request: NextRequest) {
	const session = await getServerSession(authOptions);

	if (!session || !session.user?.email) {
		return new Response('Unauthorized. Sign in via api/auth/signin', { status: 401 });
	}
	const authorized_addresses = (process.env.AUTHORIZED_EMAIL_ADDRESSES || '').split(',').map(email => email.trim());
	if (!authorized_addresses.includes(session.user.email)) {
		return new Response('Unauthorized. Email not in whitelist', { status: 401 });
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
