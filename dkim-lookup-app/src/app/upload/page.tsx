"use client";

import React from "react";
import { useSession, signIn, signOut } from "next-auth/react"
import UploadTsv from "./UploadTsv";
import UploadGmail from "./UploadGmail";

export default function Page() {

	const { data: session, status } = useSession()

	if (status == "unauthenticated") {
		return <div>
			<p>You need to be signed in to use this page.</p>
			<button onClick={() => signIn()}>Sign in</button>
		</div>
	}
	if (status == "loading") {
		return <p>loading...</p>
	}

	return (
		<div>
			<h1>Upload</h1>
			{(status == "authenticated") &&
				<div>
					{session?.user?.email && <div>Signed in as {session?.user?.email}</div>}
					<button onClick={() => signOut()}>Sign out</button>
				</div>
			}

			<p>
				On this page, you can contribute to the project by uploading domains and selectors
				from your own Gmail account or from a TSV file.
			</p>

			<UploadGmail />
			<UploadTsv />
		</div >
	)
}
