import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { NextAuthProvider } from './session-provider'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
	title: 'DKIM Registry',
	description: 'DKIM archive website',
}

const DevModeNotice: React.FC = () => {
	if (process.env.NODE_ENV !== 'development') {
		return null;
	}
	return (
		<span style={{ color: 'white', backgroundColor: 'orange', paddingLeft: '0.5rem', paddingRight: '0.5rem', marginLeft: '1rem' }}>
			development
		</span>
	)
};

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
						<DevModeNotice />
					</header>
					<main style={{ margin: '0.5rem' }}>
						{children}
					</main>
				</body>
			</NextAuthProvider>
		</html>
	)
}
