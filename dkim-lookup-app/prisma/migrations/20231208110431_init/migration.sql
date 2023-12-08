-- CreateTable
CREATE TABLE "DkimRecord" (
    "id" SERIAL NOT NULL,
    "dkimSelector" TEXT NOT NULL,
    "dkimDomain" TEXT NOT NULL,
    "fetchedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "value" TEXT NOT NULL,

    CONSTRAINT "DkimRecord_pkey" PRIMARY KEY ("id")
);
