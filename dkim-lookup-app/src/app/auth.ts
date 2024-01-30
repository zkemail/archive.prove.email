import GoogleProvider from "next-auth/providers/google"

export const authOptions = {
	providers: [
		GoogleProvider({
			clientId: process.env.GOOGLE_CLIENT_ID || '',
			clientSecret: process.env.GOOGLE_CLIENT_SECRET || '',
			checks: 'none',
			authorization: {
				params: {
					prompt: "consent",
					scope: 'https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/gmail.metadata',
				},
			},
		}),
	],
	callbacks: {
		async jwt({ token, account }: { token: any, account: any }) {
			if (account) {
				token.accessToken = account.access_token
				token.refreshToken = account.refresh_token
			}
			return token
		},
	}
}

