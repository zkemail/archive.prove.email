import { SearchInput } from '@/components/SearchInput';
import { SelectorResult } from '@/components/SelectorResult';
import { RecordWithSelector, findRecords } from '@/lib/db';
import { parseDkimRecord } from '@/lib/utils';

function dkimValueHasPrivateKey(dkimValue: string): boolean {
	return parseDkimRecord(dkimValue).p !== null;
}

interface DomainSearchResultProps {
	records: RecordWithSelector[];
	domainQuery: string | undefined;
}

const DomainSearchResults: React.FC<DomainSearchResultProps> = ({ records, domainQuery }) => {
	if (!domainQuery) {
		return <div>Enter a search term</div>
	};
	if (!records?.length) {
		return <div>No records found for "{domainQuery}"</div>
	}
	return (
		<div>
			<p>Search results for <b>{domainQuery}</b></p>
			<div>
				{records.map((record) => (
					<SelectorResult key={record.id} record={record} />
				))}
			</div>
		</div>
	);
};

export default async function Home({ searchParams }: {
	searchParams: { [key: string]: string | string[] | undefined }
}) {
	const domainQuery = searchParams?.domain?.toString();
	let records = domainQuery ? (await findRecords(domainQuery)) : []
	records = records.filter((record) => dkimValueHasPrivateKey(record.value));

	return (
		<div style={{ display: 'flex', minHeight: '100vh', flexDirection: 'column', alignItems: 'center' }}>
			<h2 style={{ padding: '2rem' }}>
				<a href='/' className='defaultcolor'>DKIM Registry</a>
			</h2>
			<SearchInput domainQuery={domainQuery} />
			<DomainSearchResults records={records} domainQuery={domainQuery} />

			<div style={{ textAlign: 'center', marginTop: '5rem', fontSize: '0.8rem' }}>
				<hr style={{ width: '50%', margin: '1rem auto', borderTop: '1px solid black' }} />
				<div><a href="about">About</a> this site</div>
				<div>Visit the project on <a href="https://github.com/foolo/dkim-lookup">GitHub</a></div>
				<div>Visit <a href="https://prove.email/">Proof of Email</a></div>
				<div><a href="contribute">Contribute</a> to the registry</div>
				<div>Explore the <a href="api-explorer">API</a></div>
				<div>Read the <a href="privacy-policy">Privacy policy</a></div>
			</div>
		</div>
	)
}
