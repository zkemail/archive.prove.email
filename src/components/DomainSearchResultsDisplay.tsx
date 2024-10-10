"use client";
import { RecordWithSelector } from "@/lib/db";
import React, { useEffect } from "react";
import { useInView } from "react-intersection-observer";
import { SelectorResult } from "./SelectorResult";

interface DomainSearchResultProps {
  domainQuery: string | undefined;
  records: RecordWithSelector[];
  loadMore: () => void;
  cursor: number | null;
}

export const DomainSearchResultsDisplay: React.FC<DomainSearchResultProps> = ({
  domainQuery,
  records,
  loadMore,
  cursor,
}) => {
  const { ref: inViewElement, inView } = useInView();

  useEffect(() => {
    if (inView) {
      loadMore();
    }
  }, [inView]);

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
