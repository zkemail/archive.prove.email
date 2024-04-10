import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { addDomainSelectorPair } from '@/lib/utils_server';
import { z } from 'zod';
import { SourceIdentifiers } from '@/lib/utils';

export type AddDspAdminResponse = {
	message: object;
	added?: boolean;
};

const AddDspRequestSchema = z.object({
	domain: z.string(),
	selector: z.string(),
	sourceIdentifier: z.enum(SourceIdentifiers),
});

export type AddDspAdminRequest = z.infer<typeof AddDspRequestSchema>;

export async function POST(request: NextRequest) {
	const authHeader = request.headers.get('authorization');
	if (authHeader !== `Bearer ${process.env.CRON_SECRET}`) {
		return new Response('Unauthorized', { status: 401 });
	}
	try {
		const body = await request.json();
		const dsp = AddDspRequestSchema.parse(body);
		let added = await addDomainSelectorPair(dsp.domain, dsp.selector, dsp.sourceIdentifier);
		return NextResponse.json(
			{ message: dsp, added } as AddDspAdminResponse,
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
