import { RecordWithSelector } from '@/lib/db';
import { FC, ReactNode } from 'react';
import { cardStyle } from './styles';

interface RowProps {
	label: string;
	children: ReactNode;
}

const Row: FC<RowProps> = ({ label: title, children }) => {
	return (
		<div style={{ display: 'flex', flexWrap: 'wrap' }}>
			<div style={{ width: '25%', paddingBottom: '0.5rem' }}>{title}</div>
			<div style={{ width: '75%' }} >{children}</div>
		</div>
	);
};

interface SelectorResultProps {
	record: RecordWithSelector;
}

export const SelectorResult: React.FC<SelectorResultProps> = ({ record }) => {

	return (
		<div style={cardStyle}>
			<Row label='Selector:'>{record.selector.name}</Row>
			<Row label='Fetched date:'>{record.fetchedAt.toLocaleString()}</Row>
			<Row label='Value:'>
				<pre style={{
					overflowWrap: 'break-word',
					whiteSpace: 'pre-wrap',
					maxWidth: '32rem',
					margin: '0',
				}}>
					{record.value}
				</pre>
			</Row>
		</div>
	);
};
