import { findRecords } from "@/lib/db";
import { NextRequest, NextResponse } from "next/server";

export type DomainSearchResults = {
	domain: string;
	selector: string;
	firstSeenAt: Date | null;
	lastSeenAt: Date | null;
	value: string;
};

export async function GET(_request: NextRequest, { params }: { params: { name: string } }) {
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
		return NextResponse.json({ message: error.message }, { status: 500 });
	}
}
