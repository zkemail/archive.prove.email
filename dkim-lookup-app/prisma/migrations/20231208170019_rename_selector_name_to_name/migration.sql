/*
  Warnings:

  - You are about to drop the column `selectorName` on the `Selector` table. All the data in the column will be lost.
  - Added the required column `name` to the `Selector` table without a default value. This is not possible if the table is not empty.

*/
-- AlterTable
ALTER TABLE "Selector" DROP COLUMN "selectorName",
ADD COLUMN     "name" TEXT NOT NULL;
