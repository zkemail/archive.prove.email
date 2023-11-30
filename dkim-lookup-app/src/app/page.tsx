import { PrismaClient, Prisma, DkimRecord } from '@prisma/client'

interface DomainSearchResultProps {
	records: DkimRecord[];
}

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

const DomainSearchResults: React.FC<DomainSearchResultProps> = ({ records }) => {
	return (
		<div className='dkim-records'>
			<table>
				<thead>
					<tr>
						<th>Selector</th>
						<th>Fetched date</th>
						<th>Value</th>
					</tr>
				</thead>
				<tbody>
					{records.map((record) => (
						<tr key={record.id}>
							<td className='px-4'>{record.dkimSelector}</td>
							<td className='px-4'>{record.fetchedAt.toLocaleString()}</td>
							<td className='px-4'>
								<textarea className='w-80 h-40' readOnly>
									{record.value}
								</textarea>
							</td>
						</tr>
					))}
				</tbody>
			</table>
		</div>
	);
};

interface SearchFormProps {
	domainQuery: string | undefined;
}

const SearchForm: React.FC<SearchFormProps> = ({ domainQuery }) => {
	return (
		<div className='search-form'>
			<form action="/" method="get">
				<label htmlFor="domain" className='px-2'>
					Domain name:
				</label>
				<input
					type="text"
					id="domain"
					name="domain"
					placeholder="example.com"
					defaultValue={domainQuery}
				/>
				<button className='border border-black' type="submit">Search</button>
			</form>
		</div>
	);
};

export default async function Home({ searchParams }: {
	searchParams: { [key: string]: string | string[] | undefined }
}) {
	const prisma = new PrismaClient()
	const domainQuery = searchParams?.domain?.toString();
	let records: DkimRecord[] = [];
	if (domainQuery) {
		records = await prisma.dkimRecord.findMany({
			where: {
				dkimDomain: {
					equals: domainQuery,
					mode: Prisma.QueryMode.insensitive,
				},
			},
		})
	}

	records = records.filter((record) => dkimValueHasPrivateKey(record.value));

	return (
		<main className="flex min-h-screen flex-col items-center">
			<h1 className='p-8 text-xl font-bold'>
				DKIM Lookup
			</h1>
			<SearchForm domainQuery={domainQuery} />
			{domainQuery
				? records.length > 0
					? <div><p className='p-4'>Search results for "{domainQuery}"</p><DomainSearchResults records={records} /></div>
					: <p>No records found for "{domainQuery}"</p>
				: <p>Enter a search term</p>}
			<p className='p-8'>Visit the project on <a href="https://github.com/foolo/dkim-lookup">GitHub</a></p>
		</main>
	)
}
