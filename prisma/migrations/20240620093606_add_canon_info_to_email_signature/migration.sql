/*
  Warnings:

  - Added the required column `canonInfo` to the `EmailSignature` table without a default value. This is not possible if the table is not empty.

*/
-- AlterTable
ALTER TABLE "EmailSignature" ADD COLUMN     "canonInfo" TEXT NOT NULL;
