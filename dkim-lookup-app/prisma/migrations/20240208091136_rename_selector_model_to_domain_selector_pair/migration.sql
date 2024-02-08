ALTER TABLE IF EXISTS "Selector" RENAME TO "DomainSelectorPair";

ALTER TABLE "DomainSelectorPair" RENAME COLUMN "name" TO "selector";
ALTER TABLE "DomainSelectorPair" RENAME CONSTRAINT "Selector_pkey" TO "DomainSelectorPair_pkey";

ALTER TABLE "DkimRecord" RENAME COLUMN "selectorId" TO "domainSelectorPairId";
ALTER TABLE "DkimRecord" RENAME CONSTRAINT "DkimRecord_selectorId_fkey" TO "DkimRecord_domainSelectorPairId_fkey";
