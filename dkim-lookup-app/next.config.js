/** @type {import('next').NextConfig} */

const cspValue = [
	"default-src 'self'",
	"style-src 'self' 'unsafe-inline'",
	"frame-ancestors 'none'",
	"script-src 'self' 'unsafe-inline' 'unsafe-eval'",
	"img-src 'self' https://authjs.dev/ data:", // https://authjs.dev/ for images during the login flow
	"connect-src 'self' https://*.alchemy.com", // https://*.alchemy.com used by Witness
]

const nextConfig = {
	async headers() {
		return [{
			source: '/(.*)',
			headers: [
				{
					key: 'Content-Security-Policy',
					value: cspValue.join('; '),
				},
				{
					key: 'X-Content-Type-Options',
					value: 'nosniff',
				},
			],
		}]
	},
}

module.exports = nextConfig
