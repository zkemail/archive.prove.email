"use client";

type Props = { date: Date };

export function Timestamp({ date }: Props): React.ReactNode {
	return (
		<span title={date.toISOString()}>
			{date.toLocaleString()}
		</span>
	);
}
