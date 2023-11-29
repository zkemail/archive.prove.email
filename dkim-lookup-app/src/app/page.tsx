import { PrismaClient, Prisma } from '@prisma/client'

export default async function Home() {

  const prisma = new PrismaClient()

  let records = await prisma.dkimRecord.findMany();

  return (
    <main className="flex min-h-screen flex-col items-center">
      <h1 className='p-20 text-xl font-bold'>
        DKIM Lookup
      </h1>
      <div className='dkim-records'>
        <table>
          <thead>
            <tr>
              <th>Id</th>
              <th>Domain</th>
              <th>Selector</th>
              <th>Fetched date</th>
            </tr>
          </thead>
          <tbody>
            {records.map((record) => (
              <tr key={record.id}>
                <td>{record.id}</td>
                <td>{record.dkimDomain}</td>
                <td>{record.dkimSelector}</td>
                <td>{record.fetchedAt.toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </main>
  )
}
