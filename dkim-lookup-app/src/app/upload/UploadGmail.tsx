"use client";

import axios from "axios";
import React from "react";
import { LogConsole } from "@/components/LogConsole";
import { upsert } from "@/lib/api_calls";
import { DomainSelectorPair } from "@/lib/utils";

export default function Page() {

	const [log, setLog] = React.useState<string[]>([]);
	const [started, setStarted] = React.useState<boolean>(false);

	function logmsg(message: string) {
		console.log(message);
		setLog(log => [...log, message]);
	}

	async function uploadFromGmail() {
		let uploadedPairs: Set<string> = new Set();
		const gmailApiUrl = 'api/gmail';
		let nextPageToken = "";
		let done = false;
		logmsg(`starting upload to ${gmailApiUrl}`);
		while (!done) {
			logmsg('fetching email batch...');
			await axios.get(gmailApiUrl, { params: { pageToken: nextPageToken } })
				.then(response => {
					nextPageToken = response.data.nextPageToken;
					let pairs = response.data.domainSelectorPairs as DomainSelectorPair[];
					logmsg(`received: ${pairs.length} domain/selector pairs`);
					for (const pair of pairs) {
						const pairString = JSON.stringify(pair);
						if (!uploadedPairs.has(pairString)) {
							logmsg('new pair found, uploading: ' + JSON.stringify(pair));
							upsert(pair.domain, pair.selector);
							uploadedPairs.add(pairString);
						}
					}
					done = !nextPageToken;
				}).catch(error => {
					console.log(error);
					let data = error?.response?.data;
					let message = `${error}` + (data ? ` - ${data}` : "");
					throw message;
				})
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
			<h3>Upload from Gmail</h3>
			<p>
				Fetch the domain and selector from the DKIM-Signature header field in email messages in your Gmail account and add them to the database.
			</p>
			<p>
				<button disabled={!startEnabled} onClick={startUpload}>
					{started ? "Running..." : "Start"}
				</button>
			</p>
			<LogConsole log={log} setLog={setLog} />
		</div >
	)
}
