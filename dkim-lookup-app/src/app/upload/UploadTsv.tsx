"use client";

import { axiosErrorMessage, load_domains_and_selectors_from_tsv } from "@/lib/utils";
import React from "react";
import { LogConsole } from "@/components/LogConsole";
import axios from "axios";
import { useSession } from "next-auth/react";
import { InlineCode } from "@/components/InlineCode";

export default function Page() {

	const { update } = useSession();
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
		for (const dsp of domainSelectorPairs) {
			logmsg(`uploading ${JSON.stringify(dsp)}`);
			try {
				let upsertResponse = await axios.get(upsertApiUrl, { params: dsp });
				await update();
				console.log('upsert response', upsertResponse);
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
				Here you can contribute to the database by providing a TSV file with domains and selectors.
			</p>
			<p>
				One way to create such a file is to first export all messages in your email account as an .mbox file, and then parsing the .mbox file
				with the <InlineCode>mbox_selector_scraper.py</InlineCode> tool, which outputs domains-selector-pairs in TSV format.
				The process is described in more detail in the <a href="https://github.com/foolo/dkim-lookup?tab=readme-ov-file#mbox_selector_scraper">README</a>.
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
