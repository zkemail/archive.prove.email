"use client";

import { findKeysPaginated, findKeysPaginatedModifiedQuery } from "@/app/actions";
import Loading from "@/app/loading";
import { RecordWithSelector } from "@/lib/db";
import { parseDkimTagList } from "@/lib/utils";
import { useEffect, useState } from "react";
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

  async function loadRecords() {
    const { records, flag } = await DomainResultsLoader(domainQuery);
    setFlag(flag);
    setRecords(records);
    setCursor(records[records.length - 1]?.id);
    setIsLoading(false);
  }

  useEffect(() => {
    setIsLoading(true);
    loadRecords();
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

    const uniqueRecords = [...records, ...newRecords].reduce((acc, record) => {
      if (!acc.find((r) => r.id === record.id)) {
        acc.push(record);
      }
      return acc;
    }, [] as RecordWithSelector[]);

    setCursor(lastCursor);
    setRecords(uniqueRecords);
  }

  return isLoading ? (
    <Loading />
  ) : (
    <DomainSearchResultsDisplay records={records} domainQuery={domainQuery} loadMore={loadMore} cursor={cursor} />
  );
}

export default DomainSearchResults;
