import { DkimRecord } from '@prisma/client'
import { Card } from './layout/Card';
import { FC, ReactNode } from 'react';

interface RowProps {
	label: string;
	children: ReactNode;
}

const Row: FC<RowProps> = ({ label: title, children }) => {
	return (
		<div className='flex flex-wrap'>
			<div className='w-1/4 pb-2'>{title}</div>
			<div className='w-3/4'>{children}</div>
		</div>
	);
};

interface SelectorResultProps {
	record: DkimRecord;
}

export const SelectorResult: React.FC<SelectorResultProps> = ({ record }) => {
	return (
		<Card>
			<Row label='Selector:'>{record.dkimSelector}</Row>
			<Row label='Fetched date:'>{record.fetchedAt.toLocaleString()}</Row>
			<Row label='Value:'>
				<pre className='break-words whitespace-pre-wrap max-w-lg'>{record.value}</pre>
			</Row>
		</Card>
	);
};
