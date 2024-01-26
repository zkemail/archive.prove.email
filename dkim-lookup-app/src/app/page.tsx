import { SelectorResult } from '@/components/SelectorResult';
import { searchButtonStyle, searchInputBoxStyle } from '@/components/styles';
import { RecordWithSelector, prisma, findRecords } from '@/lib/db';


function parseDkimRecord(dkimValue: string): Record<string, string | null> {
	const result: Record<string, string | null> = {};
	const parts = dkimValue.split(';');
	for (const part of parts) {
		const [key, value] = part.split('=');
		result[key.trim()] = value?.trim() || null;
	}
	return result;
}

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
	let records = domainQuery ? (await findRecords(domainQuery, prisma)) : []
	records = records.filter((record) => dkimValueHasPrivateKey(record.value));

	return (
		<main style={{ display: 'flex', minHeight: '100vh', flexDirection: 'column', alignItems: 'center' }}>
			<h2 style={{ padding: '2rem' }}>
				<a href='/' className='defaultcolor'>DKIM Lookup</a>
			</h2>
			<SearchForm domainQuery={domainQuery} />
			<DomainSearchResults records={records} domainQuery={domainQuery} />
			<p>Visit the project on <a href="https://github.com/foolo/dkim-lookup">GitHub</a></p>
		</main>
	)
}
