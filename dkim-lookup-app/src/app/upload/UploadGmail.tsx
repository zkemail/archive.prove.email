"use client";

import axios from "axios";
import React from "react";
import { LogConsole } from "@/components/LogConsole";
import { DomainSelectorPair, axiosErrorMessage } from "@/lib/utils";
import { useSession } from "next-auth/react";

export default function Page() {

	const { update } = useSession();
	const [log, setLog] = React.useState<string[]>([]);
	const [started, setStarted] = React.useState<boolean>(false);

	function logmsg(message: string) {
		console.log(message);
		setLog(log => [...log, message]);
	}

	async function uploadFromGmail() {
		let uploadedPairs: Set<string> = new Set();
		const gmailApiUrl = 'api/gmail';
		const upsertApiUrl = 'api/upsert_dkim_record';
		let nextPageToken = "";
		logmsg(`starting upload to ${gmailApiUrl}`);
		while (true) {
			logmsg('fetching email batch...');
			try {
				let response = await axios.get(gmailApiUrl, { params: { pageToken: nextPageToken } });
				await update();
				nextPageToken = response.data.nextPageToken;
				let pairs = response.data.domainSelectorPairs as DomainSelectorPair[];
				logmsg(`received: ${pairs.length} domain/selector pairs`);
				for (const pair of pairs) {
					const pairString = JSON.stringify(pair);
					if (!uploadedPairs.has(pairString)) {
						logmsg('new pair found, uploading: ' + JSON.stringify(pair));
						let upsertResponse = await axios.get(upsertApiUrl, { params: pair });
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
