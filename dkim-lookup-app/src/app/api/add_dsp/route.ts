import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { addDomainSelectorPair } from '@/lib/addDomainSelectorPair';
import { z } from 'zod';

export type AddDspResponse = {
	message: object;
};

const AddDspRequestSchema = z.object({
	domain: z.string(),
	selector: z.string(),
});

export type AddDspRequest = z.infer<typeof AddDspRequestSchema>;

export async function POST(request: NextRequest) {
	try {
		const body = await request.json();
		const dsp = AddDspRequestSchema.parse(body);
		let added = await addDomainSelectorPair(dsp.domain, dsp.selector);
		return NextResponse.json(
			{ message: { ...dsp, added } } as AddDspResponse,
			{ status: 200 }
		);
	}
	catch (error) {
		if (error instanceof z.ZodError) {
			return NextResponse.json({ message: error.errors }, { status: 400 });
		}
		return NextResponse.json({ message: `${error}` }, { status: 500 });
	}
}
