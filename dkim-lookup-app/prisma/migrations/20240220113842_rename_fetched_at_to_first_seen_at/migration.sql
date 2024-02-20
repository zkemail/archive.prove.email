-- AlterTable
ALTER TABLE "DkimRecord" RENAME COLUMN "fetchedAt" TO "firstSeenAt";
ALTER TABLE "DkimRecord" ALTER COLUMN "firstSeenAt" DROP DEFAULT;
