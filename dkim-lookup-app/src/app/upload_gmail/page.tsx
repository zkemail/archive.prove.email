"use client";

import React, { useEffect } from "react";
import { useSession, signIn, signOut } from "next-auth/react"
import { LogConsole, LogRecord } from "@/components/LogConsole";
import { DomainSelectorPair, axiosErrorMessage } from "@/lib/utils";
import axios from "axios";
import { GmailResponse } from "../api/gmail/route";
import { AddDspRequest, AddDspResponse } from "../api/dsp/route";

export default function Page() {

	const { data: session, status } = useSession()

	const { update } = useSession();
	const [log, setLog] = React.useState<LogRecord[]>([]);
	const [started, setStarted] = React.useState<boolean>(false);
	const [uploadedPairs, setUploadedPairs] = React.useState<Set<string>>(new Set());
	const [nextPageToken, setNextPageToken] = React.useState<string>('');
	const [progressCounter, setProgressCounter] = React.useState<number>(0);


	useEffect(() => {
		logmsg(`useEffect progressCounter ${progressCounter}`);
		if (started) {
			uploadFromGmail();
		}
		else {
			logmsg('useEffect upload not started');
		}
	}, [progressCounter]);


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

	async function uploadFromGmail(): Promise<number> {
		const gmailApiUrl = 'api/gmail';
		const addDspApiUrl = 'api/dsp';
		logmsg(`starting upload to ${gmailApiUrl}`);
		logmsg(`UFG progressCounter: ${progressCounter}`);
		if (true) {
			logmsg('fetching email batch...');

			try {
				console.log('uploadFromGmail nextPageToken was ', nextPageToken);
				let response = await axios.get<GmailResponse>(gmailApiUrl, { params: { pageToken: nextPageToken } });
				await update();
				console.log(`setting next page token: ${response.data.nextPageToken}`);
				setNextPageToken(response.data.nextPageToken || '');
				let pairs = response.data.domainSelectorPairs;
				logmsg(`received: ${pairs.length} domain/selector pairs`);
				logmsg(`uploadFromGmail new page token: ${nextPageToken}`);
				for (const pair of pairs) {
					const pairString = JSON.stringify(pair);
					if (!uploadedPairs.has(pairString)) {
						logmsg('new pair found, uploading: ' + JSON.stringify(pair));
						let upsertResponse = await axios.post<AddDspResponse>(addDspApiUrl, pair as AddDspRequest);
						await update();
						//console.log('upsert response', upsertResponse);
						//uploadedPairs.add(pairString);
						setUploadedPairs(uploadedPairs => new Set(uploadedPairs).add(pairString));
					}
				}
				setProgressCounter(progressCounter + 1);
				if (!response.data.nextPageToken) {
					logmsg('no more pages, upload complete');
				}
			}
			catch (error: any) {
				throw axiosErrorMessage(error);
			}
		}
		return uploadedPairs.size;
	}

	async function startUpload() {
		if (!started) {
			setStarted(true);
			try {
				uploadFromGmail();
			}
			catch (error) {
				logmsg(`upload failed: ${error}`);
			}
			finally {
				//setStarted(false);
			}
		}
	}

	const startEnabled = !started;

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
				<p>
					<button disabled={!startEnabled} onClick={startUpload}>
						{started ? "Running..." : "Start"}
					</button>
				</p>
				<LogConsole log={log} setLog={setLog} />
			</div >
		</div >
	)
}
