import NextAuth from "next-auth"

declare module "next-auth" {
	interface Session {
		has_metadata_scope: boolean | undefined,
	}
}
