import { SelectorResult } from '@/components/SelectorResult';
import { searchButtonStyle, searchInputBoxStyle } from '@/components/styles';
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

interface SearchFormProps {
	domainQuery: string | undefined;
}

const SearchForm: React.FC<SearchFormProps> = ({ domainQuery }) => {
	return (
		<div>
			<form action="/" method="get">
				<label htmlFor="domain" style={{ paddingRight: '0.5rem' }}>
					Domain name:
				</label>
				<input
					style={searchInputBoxStyle}
					type="text"
					id="domain"
					name="domain"
					placeholder="example.com"
					defaultValue={domainQuery}
				/>
				<button style={searchButtonStyle} type="submit">
					Search
				</button>
			</form>
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
		<main style={{ display: 'flex', minHeight: '100vh', flexDirection: 'column', alignItems: 'center' }}>
			<h2 style={{ padding: '2rem' }}>
				<a href='/' className='defaultcolor'>DKIM Registry</a>
			</h2>
			<SearchForm domainQuery={domainQuery} />
			<DomainSearchResults records={records} domainQuery={domainQuery} />

			<div style={{ textAlign: 'center', marginTop: '5rem', fontSize: '0.8rem' }}>
				<hr style={{ width: '50%', margin: '1rem auto', borderTop: '1px solid black' }} />
				<div><a href="about">About</a> this site</div>
				<div>Visit the project on <a href="https://github.com/foolo/dkim-lookup">GitHub</a></div>
				<div>Visit <a href="https://prove.email/">Proof of Email</a></div>
				<div><a href="upload">Contribute</a> to the registry</div>
				<div>Read the <a href="privacy-policy">Privacy policy</a></div>
			</div>
		</main>
	)
}
