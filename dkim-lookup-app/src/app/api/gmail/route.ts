import { authOptions } from '@/app/auth';
import { DomainSelectorPair, parseDkimRecord } from '@/lib/utils';
import { gmail_v1, google } from 'googleapis';
import { getToken } from 'next-auth/jwt';
import { getServerSession } from 'next-auth/next';
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

async function handleMessage(messageId: string, gmail: gmail_v1.Gmail, resultArray: DomainSelectorPair[]) {
	console.log('handle message', messageId);
	const messageRes = await gmail.users.messages.get({ userId: 'me', id: messageId, format: 'metadata' })
	let headers = messageRes.data.payload?.headers
	if (!headers) {
		throw 'missing headers';
	}
	let dkimSig = headers.find((header: any) => header.name === 'DKIM-Signature');
	if (!dkimSig?.value) {
		throw 'missing DKIM-Signature header';
	}
	let tags = parseDkimRecord(dkimSig.value);
	let domain = tags.d
	if (!domain) {
		throw 'missing d tag';
	}
	let selector = tags.s
	if (!selector) {
		throw 'missing s tag';
	}
	let domainSelectorPair = { domain, selector };
	resultArray.push(domainSelectorPair);
	return resultArray;
}


export async function GET(request: NextRequest) {
	const session = await getServerSession(authOptions);
	if (!session || !session.user?.email) {
		return new Response('Unauthorized. Sign in via api/auth/signin', { status: 401 });
	}

	const token = await getToken({
		req: request
	})
	const oauth2Client = new google.auth.OAuth2(process.env.GOOGLE_CLIENT_ID, process.env.GOOGLE_CLIENT_SECRET, process.env.GOOGLE_REDIRECT_URI);
	const gmail = google.gmail({ version: 'v1', auth: oauth2Client });

	const accessToken = token?.accessToken
	if (!accessToken || !(typeof accessToken === 'string')) {
		return NextResponse.json({ status: 401 });
	}

	oauth2Client.setCredentials({
		access_token: accessToken,
	})

	let pageToken = request.nextUrl.searchParams.get('pageToken');
	let pageTokenParam = pageToken ? { pageToken } : {};

	let listResults = await gmail.users.messages.list({ userId: 'me', maxResults: 10, ...pageTokenParam })

	let messages = listResults?.data?.messages || [];
	let domainSelectorPairs: DomainSelectorPair[] = [];
	for (let message of messages) {
		if (!message.id) {
			console.log(`no messageId for message`, message);
			continue;
		}
		try {
			await handleMessage(message.id, gmail, domainSelectorPairs);
		}
		catch (e) {
			console.log(`error handling message ${message.id}`, e);
		}
	}
	let nextPageToken = listResults.data.nextPageToken;
	return NextResponse.json({ domainSelectorPairs, nextPageToken }, { status: 200 });
}