import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { addDomainSelectorPair } from '@/lib/addDomainSelectorPair';

export type AddDspResponse = {
	message: string;
	error?: string;
};

export async function GET(request: NextRequest) {
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
		await addDomainSelectorPair(domain, selector);

		let response: AddDspResponse = { message: `added ${domain}, ${selector}` };
		return NextResponse.json(response, { status: 200 });
	}
	catch (error) {
		console.log(`error updating: ${error}`, error);
		return NextResponse.json(`${error}`, { status: 500 });
	}
}
