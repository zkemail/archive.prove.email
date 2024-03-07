import { prisma } from "@/lib/db";
import { NextRequest, NextResponse } from "next/server";
import { headers } from "next/headers";
import { RateLimiterMemory } from "rate-limiter-flexible";
import { checkRateLimiter } from "@/lib/utils";

export type AutocompleteResults = string[];

const rateLimiter = new RateLimiterMemory({ points: 10, duration: 10 });

export async function GET(request: NextRequest) {
	try {
		await checkRateLimiter(rateLimiter, headers(), 1);
	}
	catch (error: any) {
		return NextResponse.json('Rate limit exceeded', { status: 429 });
	}

	try {
		const searchParams = request.nextUrl.searchParams;
		const query = searchParams.get('query');
		if (!query) {
			return NextResponse.json([]);
		}
		let domains = await prisma.domainSelectorPair.findMany({
			distinct: ['domain'],
			where: { domain: { startsWith: query } },
			take: 8
		});
		let uniqueMatches: AutocompleteResults = Array.from(new Set(domains.map(d => d.domain)));
		return NextResponse.json(uniqueMatches);
	}
	catch (error: any) {
		return NextResponse.json(error.toString(), { status: 500 });
	}
}
