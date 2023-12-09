import { SelectorResult } from '@/components/SelectorResult';
import { fetchAndUpsertRecord } from '@/lib/fetch_and_upsert';
import { PrismaClient, Prisma, DkimRecord, Selector } from '@prisma/client'

const prisma = new PrismaClient();

export type RecordWithSelector = (DkimRecord & { selector: Selector });

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
		return <p>Enter a search term</p>
	};
	if (!records?.length) {
		return <p>No records found for "{domainQuery}"</p>
	}
	return (
		<div>
			<p className='p-4'>Search results for <b>{domainQuery}</b></p>
			<div className='dkim-records'>
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
		<div className='search-form'>
			<form action="/" method="get">
				<label htmlFor="domain" className='px-2'>
					Domain name:
				</label>
				<input
					className='border border-gray-400 px-3 py-1.5 m-2 rounded-md'
					type="text"
					id="domain"
					name="domain"
					placeholder="example.com"
					defaultValue={domainQuery}
				/>
				<button
					className='rounded-md text-white bg-sky-600 hover:bg-sky-500 px-3 py-1.5'
					type="submit"
				>
					Search
				</button>
			</form>
		</div>
	);
};

async function findRecords(domainQuery: string, prisma: PrismaClient): Promise<RecordWithSelector[]> {
	return await prisma.dkimRecord.findMany({
		where: {
			selector: {
				domain: {
					equals: domainQuery,
					mode: Prisma.QueryMode.insensitive,
				},
			}
		},
		include: {
			selector: true
		}
	});
}

export default async function Home({ searchParams }: {
	searchParams: { [key: string]: string | string[] | undefined }
}) {
	const domainQuery = searchParams?.domain?.toString();
	let records: RecordWithSelector[] = [];
	if (domainQuery) {
		records = await findRecords(domainQuery, prisma);
		let updated = false;
		for (const record of records) {
			updated = updated || await fetchAndUpsertRecord(record.selector.domain, record.selector.name, prisma);
		}
		if (updated) {
			records = await findRecords(domainQuery, prisma);
		}
	}

	records = records.filter((record) => dkimValueHasPrivateKey(record.value));

	return (
		<main className="flex min-h-screen flex-col items-center">
			<h1 className='p-8 text-xl font-bold'>
				<a href='/' className='text-pagetext hover:text-pagetext'>DKIM Lookup</a>
			</h1>
			<SearchForm domainQuery={domainQuery} />
			<DomainSearchResults records={records} domainQuery={domainQuery} />
			<p className='p-8'>Visit the project on <a href="https://github.com/foolo/dkim-lookup">GitHub</a></p>
		</main>
	)
}
