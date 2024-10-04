"use client";
import { RecordWithSelector } from "@/lib/db";
import { SelectorResult } from "./SelectorResult";
import React, { useEffect } from "react";
import { findKeysPaginated } from "@/app/actions";
import { useInView } from "react-intersection-observer";

interface DomainSearchResultProps {
  domainQuery: string | undefined;
  initialRecords: RecordWithSelector[];
}

export const DomainSearchResults: React.FC<DomainSearchResultProps> = ({ domainQuery, initialRecords }) => {
  const [cursor, setCursor] = React.useState<number | null>(initialRecords[initialRecords.length - 1]?.id);
  const [records, setRecords] = React.useState(initialRecords);
  const { ref: inViewElement, inView } = useInView();

  useEffect(() => {
    setCursor(initialRecords[initialRecords.length - 1]?.id);
    setRecords(initialRecords);
  }, [domainQuery]);

  useEffect(() => {
    if (inView) {
      loadMore();
    }
  }, [inView]);

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

  if (!domainQuery) {
    return <div>Enter a search term</div>;
  }
  if (!records?.length) {
    return <div>No records found for "{domainQuery}"</div>;
  }
  return (
    <div>
      <p>
        Search results for <b>{domainQuery}</b>
      </p>
      <div>
        {records.map((record) => (
          <SelectorResult key={record.id} record={record} />
        ))}
      </div>
      {!cursor && <p>No more records</p>}
      <div ref={inViewElement} />
    </div>
  );
};
