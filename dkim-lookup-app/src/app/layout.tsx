import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { NextAuthProvider } from './session-provider'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
	title: 'DKIM Registry',
	description: 'DKIM archive website',
}

export default function RootLayout({
	children,
}: {
	children: React.ReactNode
}) {
	return (
		<html lang="en">
			<NextAuthProvider>
				<body className={inter.className} style={{ margin: 0 }}>
					<header style={{
						background: '#fcfdfe',
						padding: '0.5rem',
						borderBottom: '1px solid #aaa',
					}}>
						<a href='/' className='defaultcolor' style={{ fontWeight: 600 }}>
							DKIM Registry
						</a>
					</header>
					<main style={{ margin: '0.5rem' }}>
						{children}
					</main>
				</body>
			</NextAuthProvider>
		</html>
	)
}
