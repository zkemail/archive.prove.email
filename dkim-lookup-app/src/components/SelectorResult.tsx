import { RecordWithSelector } from '@/lib/db';
import { FC, ReactNode } from 'react';
import { cardStyle } from './styles';
import { getCanonicalRecordString } from '@/lib/utils';
import { WitnessClient } from '@witnessco/client';

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


const witness = new WitnessClient();

interface ProvenanceIconProps {
	record: RecordWithSelector;
}

const ProvenanceIcon: FC<ProvenanceIconProps> = ({ record }) => {
	const canonicalRecordString = getCanonicalRecordString(record.domainSelectorPair, record.value);
	const leafHash = witness.hash(canonicalRecordString);
	const witnessUrl = `https://api.witness.co/getTimestampByLeafHash?chainId=84532&leafHash=${leafHash}`;
	return (
		<a href={witnessUrl} target="_blank" rel="noreferrer">
			<img
				src="/icons8-clock-checked-96.png" alt="witness verified icon"
				style={{ width: '1rem' }}
				title='Check provenance with Witness'
			/>
		</a>
	);
};


interface SelectorResultProps {
	record: RecordWithSelector;
}

export const SelectorResult: React.FC<SelectorResultProps> = ({ record }) => {

	return (
		<div style={cardStyle}>
			<Row label='Domain:'>{record.domainSelectorPair.domain}</Row>
			<Row label='Selector:'>{record.domainSelectorPair.selector}</Row>
			<Row label='First seen at:'>
				{record.firstSeenAt.toLocaleString()}&nbsp;
				{record.provenanceVerified && <ProvenanceIcon record={record} />}
			</Row>
			{record.lastSeenAt &&
				<Row label='Last seen at:'>
					{record.lastSeenAt.toLocaleString()}&nbsp;
				</Row>
			}
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
