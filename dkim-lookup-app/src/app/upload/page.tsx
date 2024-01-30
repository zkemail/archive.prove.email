"use client";

import React from "react";
import { useSession, signIn, signOut } from "next-auth/react"
import UploadTsv from "./UploadTsv";

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
			{(status == "authenticated" && session?.user?.email) &&
				<div>
					<div>Signed in as {session?.user?.email}</div>
					<button onClick={() => signOut()}>Sign out</button>
				</div>
			}
			<UploadTsv />
		</div >
	)
}
