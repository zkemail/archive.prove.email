import { findRecords } from "@/lib/db";
import { NextRequest, NextResponse } from "next/server";
import { headers } from "next/headers";
import { RateLimiterMemory } from "rate-limiter-flexible";
import { checkRateLimiter } from "@/lib/utils";

export type DomainSearchResults = {
	domain: string;
	selector: string;
	firstSeenAt: Date | null;
	lastSeenAt: Date | null;
	value: string;
};

const rateLimiter = new RateLimiterMemory({ points: 5, duration: 10 });

export async function GET(_request: NextRequest, { params }: { params: { name: string } }) {
	try {
		await checkRateLimiter(rateLimiter, headers(), 1);
	}
	catch (error: any) {
		return NextResponse.json('Rate limit exceeded', { status: 429 });
	}

	try {
		const domainName = params.name;
		if (!domainName) {
			return NextResponse.json([]);
		};
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
