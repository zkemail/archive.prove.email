import { findRecords } from "@/lib/db";
import { NextRequest, NextResponse } from "next/server";
import { Ratelimit } from "@upstash/ratelimit";
import { Redis } from "@upstash/redis";

const ratelimit = new Ratelimit({
	redis: Redis.fromEnv(),
	limiter: Ratelimit.slidingWindow(10, "10 s"),
	analytics: true,
	prefix: "dkimreg",
});
const ratelimitIdentifier = "api";

export type DomainSearchResults = {
	domain: string;
	selector: string;
	firstSeenAt: Date | null;
	lastSeenAt: Date | null;
	value: string;
};

export async function GET(_request: NextRequest, { params }: { params: { name: string } }) {

	const ratelimitResponse = await ratelimit.limit(ratelimitIdentifier);
	if (!ratelimitResponse.success) {
		return NextResponse.json({ message: "Rate limit exceeded" }, { status: 429 });
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
		return NextResponse.json({ message: error.message }, { status: 500 });
	}
}
