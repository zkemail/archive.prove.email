"use client";

import { findKeysPaginated } from "@/app/actions";
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
  let records = null;
  records = domainQuery ? await findKeysPaginated(domainQuery, null) : [];
  records = records.filter((record) => dkimValueHasPrivateKey(record.value));
  return records;
}

function DomainSearchResults({ domainQuery, isLoading, setIsLoading }: DomainSearchResultsProps) {
  const [records, setRecords] = useState<RecordWithSelector[]>([]);
  const [cursor, setCursor] = useState<number | null>(null);

  useEffect(() => {
    setIsLoading(true);
    async function loadRecords() {
      const newRecords = await DomainResultsLoader(domainQuery);
      setRecords(newRecords);
      setCursor(newRecords[newRecords.length - 1]?.id);
      setIsLoading(false);
    }

    loadRecords();
  }, [domainQuery]);

  async function loadMore() {
    if (!cursor) {
      return;
    }

    let newRecords = domainQuery ? await findKeysPaginated(domainQuery, cursor) : [];
    if (!newRecords.length) {
      // If no new records are found, stop further loading
      setCursor(null);
      return;
    }

    let lastCursor = newRecords[newRecords.length - 1]?.id;
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
