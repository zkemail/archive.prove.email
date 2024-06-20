from prisma import Prisma
from prisma.types import DkimRecordWhereUniqueInput
from prisma.models import DkimRecord
import logging
from typing import Optional


async def load_dkim_records_with_dsps(prisma: Prisma, max_records: int | None = None):
	cursor: Optional[DkimRecordWhereUniqueInput] = None
	records: list[DkimRecord] = []
	take = 50000
	if max_records is not None:
		take = min(take, max_records)
	while True:
		skip = 0 if cursor is None else 1
		new_records = await prisma.dkimrecord.find_many(take=take, include={'domainSelectorPair': True}, cursor=cursor, skip=skip)
		logging.info(f'fetched {len(records)} records')
		if len(new_records) == 0:
			break
		records.extend(new_records)
		if max_records is not None and len(records) >= max_records:
			break
		cursor = {'id': new_records[-1].id}
	return records
