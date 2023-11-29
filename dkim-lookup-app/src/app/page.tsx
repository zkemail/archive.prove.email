import { PrismaClient, Prisma, DkimRecord } from '@prisma/client'

interface DomainSearchResultProps {
  records: DkimRecord[];
}

const DomainSearchResults: React.FC<DomainSearchResultProps> = ({ records }) => {
  return (
    <div className='dkim-records'>
      <table>
        <thead>
          <tr>
            <th>Selector</th>
            <th>Fetched date</th>
          </tr>
        </thead>
        <tbody>
          {records.map((record) => (
            <tr key={record.id}>
              <td className='px-4'>{record.dkimSelector}</td>
              <td className='px-4'>{record.fetchedAt.toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
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
        dkimDomain: domainQuery,
      },
    })
  }

  return (
    <main className="flex min-h-screen flex-col items-center">
      <h1 className='p-8 text-xl font-bold'>
        DKIM Lookup
      </h1>
      {domainQuery
        ? records.length > 0
          ? <div><p className='p-4'>Search results for "{domainQuery}"</p><DomainSearchResults records={records} /></div>
          : <p>No records found for "{domainQuery}"</p>
        : <p>Enter a search term</p>}
    </main>
  )
}
