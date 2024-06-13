-- CreateTable
CREATE TABLE "EmailPairGcdResult" (
    "id" SERIAL NOT NULL,
    "emailSignatureA_id" INTEGER NOT NULL,
    "emailSignatureB_id" INTEGER NOT NULL,
    "foundGcd" BOOLEAN NOT NULL,
    "timestamp" TIMESTAMP(3) NOT NULL,
    "dkimRecordId" INTEGER,

    CONSTRAINT "EmailPairGcdResult_pkey" PRIMARY KEY ("id")
);

-- AddForeignKey
ALTER TABLE "EmailPairGcdResult" ADD CONSTRAINT "EmailPairGcdResult_emailSignatureA_id_fkey" FOREIGN KEY ("emailSignatureA_id") REFERENCES "EmailSignature"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "EmailPairGcdResult" ADD CONSTRAINT "EmailPairGcdResult_emailSignatureB_id_fkey" FOREIGN KEY ("emailSignatureB_id") REFERENCES "EmailSignature"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "EmailPairGcdResult" ADD CONSTRAINT "EmailPairGcdResult_dkimRecordId_fkey" FOREIGN KEY ("dkimRecordId") REFERENCES "DkimRecord"("id") ON DELETE SET NULL ON UPDATE CASCADE;
