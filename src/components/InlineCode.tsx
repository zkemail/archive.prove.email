type Props = { children?: React.ReactNode };

export function InlineCode({ children }: Props): React.ReactNode {
	return (
		<span style={{
			fontFamily: 'monospace',
			backgroundColor: 'white',
			borderRadius: '0.375rem',
			border: '1px solid #e0e0e0',
			padding: '0.2rem 0.4rem',
		}}>
			{children}
		</span>
	);
}
