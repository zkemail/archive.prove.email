-- CreateTable
CREATE TABLE "EmailSignature" (
    "id" SERIAL NOT NULL,
    "domain" TEXT NOT NULL,
    "selector" TEXT NOT NULL,
    "headerHash" TEXT NOT NULL,
    "dkimSignature" TEXT NOT NULL,
    "timestamp" TIMESTAMP(3),

    CONSTRAINT "EmailSignature_pkey" PRIMARY KEY ("id")
);
