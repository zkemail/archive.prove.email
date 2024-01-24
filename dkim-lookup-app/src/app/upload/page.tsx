"use client";

import { load_domains_and_selectors_from_tsv } from "@/lib/tsv";
import axios from "axios";
import React, { useRef } from "react";
import { useSession } from "next-auth/react"

export default function Page() {

	const [log, setLog] = React.useState<string[]>([]);
	const scrollDiv = useRef<HTMLInputElement>(null);
	const [selectedFile, setSelectedFile] = React.useState<File | undefined>();
	const [started, setStarted] = React.useState<boolean>(false);

	const signinUrl = new URL('api/auth/signin', window.location.origin);

	const { data: session, status } = useSession()

	if (status == "unauthenticated") {
		return <p>
			You need to be signed in to use this page. Sign in via
			<a href={signinUrl.toString()}> {signinUrl.toString()}</a>
		</p>
	}
	if (status == "loading") {
		return <p className="m-4">loading...</p>
	}

	function fileSelectCallback(event: React.ChangeEvent<HTMLInputElement>) {
		const file = event.target.files?.[0];
		setSelectedFile(file);
	}

	function logmsg(message: string) {
		console.log(message);
		setLog(log => [...log, message]);
		if (scrollDiv.current) {
			scrollDiv.current.scrollTop = scrollDiv.current.scrollHeight;
		}
	}

	function uploadFile() {
		if (!selectedFile) {
			logmsg("no file selected");
			return;
		}
		const reader = new FileReader();
		reader.readAsText(selectedFile);
		reader.onload = async function (event) {
			let fileContent = event.target?.result;
			if (!fileContent) {
				logmsg("error: no file content");
				return;
			}
			if (typeof fileContent !== "string") {
				logmsg("error: file content is not a string");
				return;
			}
			const domainSelectorsDict: Record<string, string[]> = {};
			load_domains_and_selectors_from_tsv(domainSelectorsDict, fileContent);
			const baseUrl = new URL('api/upsert_dkim_record', window.location.origin);
			logmsg(`starting upload to ${baseUrl}`);
			for (const domain in domainSelectorsDict) {
				for (const selector of domainSelectorsDict[domain]) {
					let url = new URL(baseUrl.toString());
					url.searchParams.set('domain', domain);
					url.searchParams.set('selector', selector);
					let result = await axios.get(url.toString())
						.then(response => {
							console.log('response.data: ', response.data);
							logmsg(`${domain} ${selector} ${response.data.message}`);
							if (scrollDiv.current) {
								scrollDiv.current.scrollTop = scrollDiv.current.scrollHeight;
							}
							return true;
						}).catch(error => {
							logmsg(`error calling ${url}`);
							logmsg(error.message);
							return false;
						});
					if (!result) {
						return;
					}
				}
			}
			logmsg("upload complete");
		};
	}

	function startStopButton() {
		if (!started) {
			setStarted(true);
			uploadFile();
		}
	}

	const startEnabled = selectedFile && !started;

	return (
		<div className="p-4">
			{(status == "authenticated" && session?.user?.email) &&
				<p>Signed in as
					<span className="font-bold"> {session?.user?.email}</span> – <a href="/api/auth/signout">Sign out</a>
				</p>
			}
			<p>
				Add records to the database by providing a TSV file with domains and selectors.
				This page will parse the file and add the records to the database via the <code>api/upsert_dkim_record</code> API.
			</p>
			<p className="mt-2 mb-2">
				<p>Select a file:</p>
				<input type="file" onChange={fileSelectCallback} accept=".tsv,.txt" />

			</p>
			<div>
				<button
					disabled={!startEnabled}
					className="border border-black bg-gray-200 p-0.5 px-2 rounded disabled:text-gray-400 disabled:border-gray-400"
					onClick={startStopButton}
				>
					{started ? "Running..." : "Start"}
				</button>
			</div>
			<div className="mt-2">
				<p>Log:</p>
				<div className='overflow-y-scroll pb-8 bg-white text-xs h-[75vh] border border-black' ref={scrollDiv} >
					{log.map((line, index) =>
						<pre key={index}>{line}</pre>
					)}
				</div>

			</div>
		</div >
	)
}
