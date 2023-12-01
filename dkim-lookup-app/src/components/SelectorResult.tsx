import { DkimRecord } from '@prisma/client'

interface SelectorResultProps {
	record: DkimRecord;
}

export const SelectorResult: React.FC<SelectorResultProps> = ({ record }) => {
	return (
		<div className='border-2 border-black'>
			<div>Selector: {record.dkimSelector}</div>
			<div>Fetched date: {record.fetchedAt.toLocaleString()}</div>
			<div>Value:<pre className='break-words whitespace-pre-wrap max-w-lg'>{record.value}</pre></div>
		</div>
	);
};
