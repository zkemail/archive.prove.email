/*
  Warnings:

  - You are about to drop the column `dkimDomain` on the `DkimRecord` table. All the data in the column will be lost.
  - You are about to drop the column `dkimSelector` on the `DkimRecord` table. All the data in the column will be lost.
  - Added the required column `selectorId` to the `DkimRecord` table without a default value. This is not possible if the table is not empty.

*/
-- AlterTable
ALTER TABLE "DkimRecord" DROP COLUMN "dkimDomain",
DROP COLUMN "dkimSelector",
ADD COLUMN     "selectorId" INTEGER NOT NULL;

-- CreateTable
CREATE TABLE "Selector" (
    "id" SERIAL NOT NULL,
    "domain" TEXT NOT NULL,
    "selectorName" TEXT NOT NULL,
    "lastRecordUpdate" TIMESTAMP(3),

    CONSTRAINT "Selector_pkey" PRIMARY KEY ("id")
);

-- AddForeignKey
ALTER TABLE "DkimRecord" ADD CONSTRAINT "DkimRecord_selectorId_fkey" FOREIGN KEY ("selectorId") REFERENCES "Selector"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
