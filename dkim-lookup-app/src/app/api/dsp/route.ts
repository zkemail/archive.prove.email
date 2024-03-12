import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { addDomainSelectorPair } from '@/lib/utils_server';
import { z } from 'zod';
import { headers } from "next/headers";
import { RateLimiterMemory } from 'rate-limiter-flexible';
import { checkRateLimiter } from '@/lib/utils';

export type AddDspResponse = {
	message: object;
	added?: boolean;
};

const AddDspRequestSchema = z.object({
	domain: z.string(),
	selector: z.string(),
});

export type AddDspRequest = z.infer<typeof AddDspRequestSchema>;

const rateLimiter = new RateLimiterMemory({ points: 1200, duration: 360 });

export async function POST(request: NextRequest) {
	try {
		await checkRateLimiter(rateLimiter, headers(), 1);
	}
	catch (error: any) {
		return NextResponse.json('Rate limit exceeded', { status: 429 });
	}

	try {
		const body = await request.json();
		const dsp = AddDspRequestSchema.parse(body);
		let added = await addDomainSelectorPair(dsp.domain, dsp.selector);
		return NextResponse.json(
			{ message: dsp, added } as AddDspResponse,
			{ status: 200 }
		);
	}
	catch (error: any) {
		if (error instanceof z.ZodError) {
			return NextResponse.json(error.errors, { status: 400 });
		}
		return NextResponse.json(error.toString(), { status: 500 });
	}
}
