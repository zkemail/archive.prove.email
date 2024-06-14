/*
  Warnings:

  - The primary key for the `EmailPairGcdResult` table will be changed. If it partially fails, the table could be left without primary key constraint.
  - You are about to drop the column `id` on the `EmailPairGcdResult` table. All the data in the column will be lost.

*/
-- AlterTable
ALTER TABLE "EmailPairGcdResult" DROP CONSTRAINT "EmailPairGcdResult_pkey",
DROP COLUMN "id",
ADD CONSTRAINT "EmailPairGcdResult_pkey" PRIMARY KEY ("emailSignatureA_id", "emailSignatureB_id");
