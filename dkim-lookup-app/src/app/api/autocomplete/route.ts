import { prisma } from "@/lib/db";
import { NextRequest, NextResponse } from "next/server";

export type AutocompleteResults = string[];

export async function GET(request: NextRequest) {
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
