export default function Page() {

	return (
		<div>
			<h1>Privacy Policy</h1>

			<h2>Privacy Policy for Proof of Email</h2>
			<p>This Privacy Policy describes how DKIM Registry, operated by <strong>Proof of Email</strong> (hereinafter referred to as "we", "us", or "our"), collects, uses, and shares your personal information when you use our website located at <a href="https://registry.prove.email">registry.prove.email</a> (the "Website").</p>
			<p><strong>Information We Collect:</strong></p>
			<ul>
				<li><strong>User Email Address:</strong> When you sign in with your Gmail account to contribute domains and selectors, we collect your email address solely for displaying it to you within the platform.</li>
				<li><strong>Email Message Header Fields:</strong> With your consent, we access your email message metadata, specifically the header fields, to extract domains and selectors from the <code>DKIM-Signature</code> header. This information is used to build our archive of archived DKIM records.</li>
			</ul>
			<p><strong>How We Use Your Information:</strong></p>
			<ul>
				<li><strong>Contribution page:</strong> We use your email address solely for displaying it within the platform when you use the "Contribute" feature.</li>
				<li><strong>Build DKIM Archive:</strong> We use the extracted domains and selectors from your email header fields to build a publicly accessible archive of historical DKIM records. This archive helps ensure email authentication and combat email spoofing.</li>
			</ul>
			<p><strong>Information Sharing and Disclosure:</strong></p>
			<ul>
				<li>We do not share your personal information with any third parties except as required by law or to protect our rights and interests.</li>
				<li>The archived DKIM records, containing domains and selectors (but not personal information), are publicly accessible on the Website.</li>
				<li>We may share anonymized or aggregated data with third parties for research or analytical purposes.</li>
			</ul>
			<p><strong>Data Security:</strong></p>
			<ul>
				<li>We take reasonable steps to protect your personal information from unauthorized access, disclosure, alteration, or destruction. However, no internet transmission is completely secure, and we cannot guarantee the security of your information.</li>
			</ul>
			<p><strong>Your Choices:</strong></p>
			<ul>
				<li>You can choose not to contribute domains and selectors by not using the "Contribute" feature.</li>
				<li>You can revoke your consent for us to access your email message metadata at any time by managing your Gmail app permissions.</li>
				<li>You can request to delete your user account by contacting us.</li>
			</ul>
			<p><strong>Changes to this Privacy Policy:</strong></p>
			<ul>
				<li>We may update this Privacy Policy from time to time. We will notify you of any changes by posting the new Privacy Policy on the Website.</li>
			</ul>
		</div >
	)
}
