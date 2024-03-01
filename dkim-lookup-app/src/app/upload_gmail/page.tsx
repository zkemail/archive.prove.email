"use client";

import React from "react";
import { useSession, signIn, signOut } from "next-auth/react"
import { LogConsole, LogRecord } from "@/components/LogConsole";
import { DomainSelectorPair, axiosErrorMessage } from "@/lib/utils";
import axios from "axios";
import { GmailResponse } from "../api/gmail/route";
import { AddDspRequest, AddDspResponse } from "../api/add_dsp/route";

export default function Page() {

	const { data: session, status } = useSession()

	const { update } = useSession();
	const [log, setLog] = React.useState<LogRecord[]>([]);
	const [started, setStarted] = React.useState<boolean>(false);

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
		let uploadedPairs: Set<string> = new Set();
		const gmailApiUrl = 'api/gmail';
		const addDspApiUrl = 'api/add_dsp';
		let nextPageToken = "";
		logmsg(`starting upload to ${gmailApiUrl}`);
		while (true) {
			logmsg('fetching email batch...');
			try {
				let response = await axios.get<GmailResponse>(gmailApiUrl, { params: { pageToken: nextPageToken } });
				await update();
				nextPageToken = response.data.nextPageToken || '';
				let pairs = response.data.domainSelectorPairs;
				logmsg(`received: ${pairs.length} domain/selector pairs`);
				for (const pair of pairs) {
					const pairString = JSON.stringify(pair);
					if (!uploadedPairs.has(pairString)) {
						logmsg('new pair found, uploading: ' + JSON.stringify(pair));
						let upsertResponse = await axios.post<AddDspResponse>(addDspApiUrl, pair as AddDspRequest);
						await update();
						console.log('upsert response', upsertResponse);
						uploadedPairs.add(pairString);
					}
				}
				if (!nextPageToken) {
					break;
				}
			}
			catch (error: any) {
				throw axiosErrorMessage(error);
			}
		}
	}

	async function startUpload() {
		if (!started) {
			setStarted(true);
			try {
				await uploadFromGmail();
				logmsg("upload complete");
			}
			catch (error) {
				logmsg(`upload failed: ${error}`);
			}
			finally {
				setStarted(false);
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
