"use client";

import { InlineCode } from "@/components/InlineCode";
import { cardStyle } from "@/components/styles";
import React from "react";

export default function Page() {
	return (
		<div>
			<h1>Contribute</h1>
			<p>
				This page lets you contribute to the <a href="https://registry.prove.email/">DKIM Registry</a> site, part of the <a href="https://prove.email">Proof of Email</a> project.
			</p>
			<p>
				You can contribute to the project by uploading domains and selectors from your own Gmail account or from a TSV file.
			</p>
			<h3>
				How it works:
			</h3>
			<p>
				When you sign in with your Gmail account and press Start, the site will
				extract the <InlineCode>DKIM-Signature</InlineCode> field from each email message in your Gmail account.
				A signature can look something like this:
			</p>
			<div style={cardStyle}>
				<code>
					DKIM-Signature: v=1; a=rsa-sha256; d=example.net; s=brisbane;
					c=relaxed/simple; q=dns/txt; i=foo@eng.example.net;
					t=1117574938; x=1118006938; l=200;
					h=from:to:subject:date:keywords:keywords;
					z=From:foo@eng.example.net|To:joe@example.com|
					Subject:demo=20run|Date:July=205,=202005=203:44:08=20PM=20-0700;
					bh=MTIzNDU2Nzg5MDEyMzQ1Njc4OTAxMjM0NTY3ODkwMTI=;
					b=dzdVyOfAKCdLXdJOc9G2q8LoXSlEniSbav+yuU4zGeeruD00lszZ
					VoG4ZHRNiYzR
				</code>
			</div>
			<p>
				In the example above, the domain is <InlineCode>example.net</InlineCode> and the selector is <InlineCode>brisbane</InlineCode>.
				These are the values that will be extracted and uploaded to the registry.
			</p>
			<p>
				The data will be used to build a publicly accessible archive of current and historical DKIM records.
			</p>
			<p>
				To start contributing, visit the <strong><a href="upload">Upload</a></strong> page.
			</p>
			<p>
				Read the <a href="privacy-policy">Privacy policy</a>
			</p>
		</div >
	)
}
