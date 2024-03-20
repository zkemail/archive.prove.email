import { authOptions } from '@/app/auth';
import { DomainAndSelector, parseDkimRecord } from '@/lib/utils';
import { gmail_v1, google } from 'googleapis';
import { getToken } from 'next-auth/jwt';
import { getServerSession } from 'next-auth/next';
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

async function handleMessage(messageId: string, gmail: gmail_v1.Gmail, resultArray: DomainAndSelector[]) {
	const messageRes = await gmail.users.messages.get({ userId: 'me', id: messageId, format: 'metadata' })
	let headers = messageRes.data.payload?.headers
	if (!headers) {
		throw 'missing headers';
	}
	let dkimSigs = headers.filter((header: any) => header.name === 'DKIM-Signature');
	for (let dkimSig of dkimSigs) {
		if (!dkimSig.value) {
			console.log('missing DKIM-Signature value', dkimSig);
			continue;
		}
		let tags = parseDkimRecord(dkimSig.value);
		let domain = tags.d
		if (!domain) {
			console.log('missing d tag', tags);
			continue;
		}
		let selector = tags.s
		if (!selector) {
			console.log('missing s tag', tags);
			continue;
		}
		let domainSelectorPair = { domain, selector };
		resultArray.push(domainSelectorPair);
	}
	return resultArray;
}

export type GmailResponse = {
	messagesProcessed: number,
	messagesTotal?: number,
	domainSelectorPairs: DomainAndSelector[],
	nextPageToken: string | null
}

async function handleRequest(request: NextRequest) {
	const session = await getServerSession(authOptions);
	if (!session || !session.user?.email) {
		return new Response('Unauthorized. Sign in via api/auth/signin', { status: 401 });
	}

	const token = await getToken({ req: request })
	const oauth2Client = new google.auth.OAuth2(process.env.GOOGLE_CLIENT_ID, process.env.GOOGLE_CLIENT_SECRET, process.env.GOOGLE_REDIRECT_URI);
	const gmail = google.gmail({ version: 'v1', auth: oauth2Client });

	const access_token = token?.access_token
	if (!access_token || !(typeof access_token === 'string')) {
		return NextResponse.json('invalid access token', { status: 500 });
	}

	oauth2Client.setCredentials({ access_token })

	let pageToken = request.nextUrl.searchParams.get('pageToken');
	let isFirstPage = !pageToken;
	let messagesTotal = isFirstPage ? (await gmail.users.getProfile({ userId: 'me' })).data.messagesTotal : null;
	let pageTokenParam = pageToken ? { pageToken } : {};
	let messageTotalParam = messagesTotal ? { messagesTotal } : {};

	let listResults = await gmail.users.messages.list({ userId: 'me', maxResults: 10, ...pageTokenParam })

	let messages = listResults?.data?.messages || [];
	let domainSelectorPairs: DomainAndSelector[] = [];
	console.log(`handling ${messages.length} messages`);
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
	let nextPageToken = listResults.data.nextPageToken || null;
	let messagesProcessed = messages.length;
	let response: GmailResponse = { domainSelectorPairs, nextPageToken, messagesProcessed, ...messageTotalParam };
	return NextResponse.json(response, { status: 200 });
}

export async function GET(request: NextRequest) {
	try {
		return await handleRequest(request);
	}
	catch (error: any) {
		console.log('handleRequest error ', error);
		return NextResponse.json(error.toString(), { status: 500 });
	}
}