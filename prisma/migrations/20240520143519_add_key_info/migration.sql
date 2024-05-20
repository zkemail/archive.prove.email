-- CreateEnum
CREATE TYPE "KeyType" AS ENUM ('RSA', 'Ed25519');

-- AlterTable
ALTER TABLE "DkimRecord" ADD COLUMN     "keyData" TEXT,
ADD COLUMN     "keyType" "KeyType",
ADD COLUMN     "source" TEXT;
