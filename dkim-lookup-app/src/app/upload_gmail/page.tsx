"use client";

import React, { useEffect } from "react";
import { useSession, signIn, signOut } from "next-auth/react"
import { LogConsole, LogRecord } from "@/components/LogConsole";
import { axiosErrorMessage } from "@/lib/utils";
import axios from "axios";
import { GmailResponse } from "../api/gmail/route";
import { AddDspRequest, AddDspResponse } from "../api/dsp/route";

export default function Page() {

	const gmailApiUrl = 'api/gmail';
	const addDspApiUrl = 'api/dsp';

	const { data: session, status } = useSession()

	const { update } = useSession();
	const [log, setLog] = React.useState<LogRecord[]>([]);
	const [uploadedPairs, setUploadedPairs] = React.useState<Set<string>>(new Set());
	const [nextPageToken, setNextPageToken] = React.useState<string>('');
	const [processedMessages, setProcessedMessages] = React.useState<number>(0);
	const [totalMessages, setTotalMessages] = React.useState<number | null>(null);

	type ProgressState = 'Not started' | 'Running...' | 'Paused' | 'Interrupted' | 'Completed';
	const [progressState, setProgressState] = React.useState<ProgressState>('Not started');

	useEffect(() => {
		if (progressState === 'Paused') {
			logmsg(progressState);
		}
		if (progressState === 'Running...') {
			uploadFromGmail();
		}
	}, [nextPageToken]);

	if (status == "unauthenticated") {
		return <div>
			<p>You need to be signed in to use this page.</p>
			<p>
				For the authentication with Google, OAuth 2.0 is used.
				The OAuth tokens (access and refresh token) are stored in a JSON Web Token in the web browser.
				The server does not store any tokens.
			</p>
			<button onClick={() => signIn()}>Sign in</button>
		</div>
	}
	if (status === "loading" && !session) {
		return <p>loading...</p>
	}

	function logmsg(message: string) {
		console.log(message);
		setLog(log => [...log, { message, date: new Date() }]);
	}

	async function uploadFromGmail() {
		setProgressState('Running...');
		try {
			logmsg(`fetching page ${nextPageToken}`);
			let response = await axios.get<GmailResponse>(gmailApiUrl, { params: { pageToken: nextPageToken }, timeout: 20000 });
			await update();
			if (response.data.messagesTotal) {
				setTotalMessages(response.data.messagesTotal);
			}
			let pairs = response.data.domainSelectorPairs;
			for (const pair of pairs) {
				const pairString = JSON.stringify(pair);
				if (!uploadedPairs.has(pairString)) {
					logmsg('new pair found, uploading: ' + JSON.stringify(pair));
					let response = await axios.post<AddDspResponse>(addDspApiUrl, pair as AddDspRequest);
					await update();
					console.log(`${addDspApiUrl} response`, response);
					uploadedPairs.add(pairString);
				}
				setUploadedPairs(uploadedPairs => new Set(uploadedPairs).add(pairString));
			}
			if (response.data.nextPageToken) {
				setNextPageToken(response.data.nextPageToken);
				setProcessedMessages(processedMessages => processedMessages + response.data.messagesProcessed);
			}
			else {
				setProgressState('Completed');
				setNextPageToken('');
				logmsg('upload complete');
			}
		}
		catch (error: any) {
			logmsg(`error: ${axiosErrorMessage(error)}`);
			setProgressState('Interrupted');
		}
	}

	let showStartButton = progressState === 'Not started';
	let showResumeButton = progressState === 'Paused' || progressState === 'Interrupted';
	let showPauseButton = progressState === 'Running...';



	return (
		<div>
			<h1>Upload from Gmail</h1>
			<div>
				{session?.user?.email && <div>Signed in as {session?.user?.email}</div>}
				{session && <button onClick={() => signOut()}>Sign out</button>}
			</div>
			<p>
				On this page, you can contribute to the project by uploading domains and selectors from your Gmail account.
			</p>
			<div>
				<p>
					Domains and selectors will be extracted from the DKIM-Signature header field in each email message in your Gmail account.
				</p>
				<div>
					Progress: {progressState}
				</div>
				<div>
					{showStartButton && <button onClick={() => {
						uploadFromGmail();
					}}>Start</button>}
					{showResumeButton && <button onClick={() => {
						uploadFromGmail();
					}}>Resume</button>}
					{showPauseButton && <button onClick={() => {
						logmsg('pausing upload...');
						setProgressState('Paused');
					}}>Pause</button>}

				</div>
				<div style={{ marginTop: '1rem', marginBottom: '1rem' }}>
					<div>
						Processed email messages: {processedMessages} {totalMessages ? `of ${totalMessages}` : ''}
					</div>
					<div>
						Uploaded domain/selector pairs: {uploadedPairs.size}
					</div>
				</div>
				<LogConsole log={log} setLog={setLog} />
			</div >
		</div >
	)
}
