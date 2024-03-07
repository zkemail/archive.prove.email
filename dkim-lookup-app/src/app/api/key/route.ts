import { findRecords } from "@/lib/db";
import { NextRequest, NextResponse } from "next/server";
import { headers } from "next/headers";
import { RateLimiterMemory } from "rate-limiter-flexible";

export type DomainSearchResults = {
	domain: string;
	selector: string;
	firstSeenAt: Date | null;
	lastSeenAt: Date | null;
	value: string;
};

const rateLimiter = new RateLimiterMemory({ points: 50, duration: 10 });

export async function GET(request: NextRequest) {
	const forwardedFor = headers().get("x-forwarded-for");
	if (forwardedFor) {
		const clientIp = forwardedFor.split(',')[0];
		try {
			await rateLimiter.consume(clientIp, 10);
		}
		catch (error: any) {
			return NextResponse.json('Rate limit exceeded', { status: 429 });
		}
	}

	try {
		const domainName = request.nextUrl.searchParams.get('domain');
		if (!domainName) {
			return NextResponse.json('missing domain parameter', { status: 400 });
		}
		let records = await findRecords(domainName);
		let result: DomainSearchResults[] = records.map((record) => ({
			domain: record.domainSelectorPair.domain,
			selector: record.domainSelectorPair.selector,
			firstSeenAt: record.firstSeenAt,
			lastSeenAt: record.lastSeenAt,
			value: record.value
		}));
		return NextResponse.json(result, { status: 200 });
	}
	catch (error: any) {
		return NextResponse.json(error.toString(), { status: 500 });
	}
}
