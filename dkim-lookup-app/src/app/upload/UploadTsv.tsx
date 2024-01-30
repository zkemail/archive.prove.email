"use client";

import { load_domains_and_selectors_from_tsv } from "@/lib/utils";
import axios from "axios";
import React from "react";
import { LogConsole } from "@/components/LogConsole";
import { upsert } from "@/lib/api_calls";

export default function Page() {

	const [log, setLog] = React.useState<string[]>([]);
	const [selectedFile, setSelectedFile] = React.useState<File | undefined>();
	const [started, setStarted] = React.useState<boolean>(false);

	function fileSelectCallback(event: React.ChangeEvent<HTMLInputElement>) {
		const file = event.target.files?.[0];
		setSelectedFile(file);
	}

	function logmsg(message: string) {
		console.log(message);
		setLog(log => [...log, message]);
	}

	function readFile(file: File) {
		return new Promise((resolve, reject) => {
			var fr = new FileReader();
			fr.onload = () => {
				resolve(fr.result)
			};
			fr.onerror = reject;
			fr.readAsText(file);
		});
	}

	async function uploadFile() {
		if (!selectedFile) {
			throw "no file selected";
		}
		let fileContent = await readFile(selectedFile);
		if (!fileContent || (typeof fileContent !== "string")) {
			throw "error: invalid file content:" + fileContent;
		}

		let domainSelectorPairs = load_domains_and_selectors_from_tsv(fileContent);

		const upsertApiUrl = 'api/upsert_dkim_record';
		logmsg(`starting upload to ${upsertApiUrl}`);
		for (const { domain, selector } of domainSelectorPairs) {
			logmsg(`uploading ${domain} ${selector}`);
			upsert(domain, selector);
		}
	}

	async function startUpload() {
		if (!started) {
			setStarted(true);
			try {
				await uploadFile();
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

	const startEnabled = selectedFile && !started;

	return (
		<div>
			<h3>Upload from TSV file</h3>
			<p>
				Add records to the database by providing a TSV file with domains and selectors.
				This page will parse the file and add the records to the database via the <code>api/upsert_dkim_record</code> API.
			</p>
			<div>
				<div>Select a file:</div>
				<input type="file" onChange={fileSelectCallback} accept=".tsv,.txt" />
			</div>
			<p>
				<button disabled={!startEnabled} onClick={startUpload}>
					{started ? "Running..." : "Start"}
				</button>
			</p>
			<LogConsole log={log} setLog={setLog} />
		</div >
	)
}
