"use client";

import { findKeysPaginated, findKeysPaginatedModifiedQuery } from "@/app/actions";
import Loading from "@/app/loading";
import { RecordWithSelector } from "@/lib/db";
import { parseDkimTagList } from "@/lib/utils";
import { useCallback, useEffect, useState } from "react";
import { DomainSearchResultsDisplay } from "./DomainSearchResultsDisplay";

interface DomainSearchResultsProps {
  domainQuery: string | undefined;
  isLoading: boolean;
  setIsLoading: (isLoading: boolean) => void;
}

function dkimValueHasPrivateKey(dkimValue: string): boolean {
  return !!parseDkimTagList(dkimValue).p;
}

async function DomainResultsLoader(domainQuery: string | undefined) {
  if (!domainQuery) return { records: [], flag: false };
  let flag = false;

  let fetchedRecords = await findKeysPaginated(domainQuery, null);

  if (fetchedRecords.length === 0) {
    fetchedRecords = await findKeysPaginatedModifiedQuery(domainQuery, null);
    flag = true;
  }

  const records = fetchedRecords.filter((record) => dkimValueHasPrivateKey(record.value));

  return { records, flag };
}

function DomainSearchResults({ domainQuery, isLoading, setIsLoading }: DomainSearchResultsProps) {
  const [records, setRecords] = useState<RecordWithSelector[]>([]);
  const [cursor, setCursor] = useState<number | null>(null);
  const [flag, setFlag] = useState<boolean>(false);

  const loadRecords = useCallback(
    async (domainQuery: string | undefined) => {
      const { records, flag } = await DomainResultsLoader(domainQuery);
      setFlag(flag);
      setRecords(records);
      setCursor(records[records.length - 1]?.id);
      setIsLoading(false);
    },
    [domainQuery]
  );

  useEffect(() => {
    setIsLoading(true);
    loadRecords(domainQuery);
  }, [domainQuery]);

  async function loadMore() {
    if (!cursor) return;

    let newRecords = [];

    if (flag) {
      newRecords = domainQuery ? await findKeysPaginatedModifiedQuery(domainQuery, cursor) : [];
    } else {
      newRecords = domainQuery ? await findKeysPaginated(domainQuery, cursor) : [];
    }

    if (!newRecords.length) {
      // If no new records are found, stop further loading
      setCursor(null);
      return;
    }

    const lastCursor = newRecords[newRecords.length - 1]?.id;
    if (lastCursor === cursor) {
      setCursor(null);
      return;
    }

    newRecords = newRecords.filter((record) => dkimValueHasPrivateKey(record.value));

    const recordMap = new Map(records.map((record) => [record.id, record]));

    newRecords.forEach((record) => {
      if (!recordMap.has(record.id)) {
        recordMap.set(record.id, record);
      }
    });

    setCursor(lastCursor);
    setRecords(Array.from(recordMap.values()));
  }

  return isLoading ? (
    <Loading />
  ) : (
    <DomainSearchResultsDisplay records={records} domainQuery={domainQuery} loadMore={loadMore} cursor={cursor} />
  );
}

export default DomainSearchResults;
