import { prisma } from "@/lib/db";

export const revalidate = 60;

export default async function Page() {

	// https://github.com/prisma/prisma/issues/4228
	type CountResult = [{ count: BigInt }]
	let [uniqueDomainsCount] = await prisma.$queryRaw`SELECT COUNT(DISTINCT domain) FROM "DomainSelectorPair";` as CountResult;

	let domainSelectorPairCount = await prisma.domainSelectorPair.count();
	let dkimKeyCount = await prisma.dkimRecord.count();

	return (
		<div>
			<h1>Statistics</h1>
			<p>
				Unique domains: {uniqueDomainsCount.count.toString()}
			</p>
			<p>
				Domain/selector-pairs: {domainSelectorPairCount}
			</p>
			<p>
				DKIM keys: {dkimKeyCount}
			</p>
		</div>
	)
}
