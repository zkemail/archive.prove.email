export default function Page() {

	return (
		<div>
			<h1>About</h1>
			<p>
				The website lets you search for a domain and returns archived DKIM selectors and keys for that domain.
				The site is a part of the <a href="https://prove.email/">Proof of Email</a> project.
			</p>
			<p>
				On the <a href="upload">Contribute</a> page, users can contribute with new domains and selectors,
				which are extracted from the DKIM-Signature header field in each email message in the user's Gmail account.
			</p>
		</div >
	)
}
