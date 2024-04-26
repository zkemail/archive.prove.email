import os
import argparse
import logging
import sys
import mailbox

sys.path.insert(0, "dkimpy")
import dkimpy.dkim as dkim
from dataclasses import dataclass

# https://russell.ballestrini.net/quickstart-to-dkim-sign-email-with-python/

privkey = """-----BEGIN PRIVATE KEY-----
MIICdwIBADANBgkqhkiG9w0BAQEFAASCAmEwggJdAgEAAoGBAKjfGUdZ23sjVsIc
8btWpFGsdtVxmlfZ8g47RW26vi5+c1jjKYEIhTnhtRLJD+9S18GgdfQzMXJiBoxU
NYWd+6tC0ANl0iDnq+VcmyQ5rEOFvdwVtqkgShPf6hSI5shSZ5JDh6f3OI7O6PtY
KnernKhOapgHm1dPgrYNnJRf8uPHAgMBAAECgYAErzuqSQnXnqFXfSoPglXIljot
rZsUeM1IK8i/RIDmFUfp3VNXav8XHfXB8aXpg6jMjED5Zzol7CY2Wlepvzot+IFD
Py5dshvz7D6Af9qqffcR5czvXRwu4qud9RcdQxAjBoyZagigjIb8iUYlrzEq3TtG
rY0DxR8RaUErTUNKcQJBANHAwoQEScBe4Ee9tSCqSxWEaXR0LQ6ZW7c/RchaGKEi
dx+O8I0+8P/BavJZp+B4fSkpcavwwzmWGZe4S7aBDOMCQQDOGtXNBKJsEU9nUnyQ
0TM1tRoTe8XZbbFHk1gWS5ShlVuJaRdcK2HxA+3ckQdeB/9v3b9yhX/KDFw0MM7w
DMbNAkB4qBx8mobePPVg71S41JzaZM/QqF+ezUL/90qqBIG0d0H1CmF/rpwtUtK1
VDOIoWbF/cwgrx9uCdTw/Je5BSUnAkEAngKszxUygK90tL3kihIYtKA3caB+uocC
VuF7svwW4xpipyJOqncIC4L7pRH7F/gBuX3D/MSkh/6Z4dlZjWf+MQJBALcmALEn
R9PFTctb7138xCv7KHTVYJR/IhVOvhlVsISNDw2cn850ryrrGnbT6RUjYk2w6VGQ
lcD1AW8sD6HEpo0=
-----END PRIVATE KEY-----
"""


def decode_dkim_header_field(dkimData: str):
    print(f'decode_dkim_header_field: {dkimData}', file=sys.stderr)
    # decode a DKIM-Signature header field such as "v=1; a=rsa-sha256; d=example.net; s=brisbane;"
    # to a dictionary such as {'v': '1', 'a': 'rsa-sha256', 'd': 'example.net', 's': 'brisbane'}
    tagValuePairStrings = list(map(lambda x: x.strip(), dkimData.split(';')))
    res: dict[str, str] = {}
    for s in tagValuePairStrings:
        if not s:
            continue
        key, value = s.split('=', 1)
        key = key.strip()
        value = value.strip()
        res[key] = value
    return res


@dataclass
class MsgInfo:
    fullMsg: str
    signedData: bytes
    signature: bytes


def main():
    parser = argparse.ArgumentParser(description='extract domains and selectors from the DKIM-Signature header fields in an mbox file and output them in TSV format')
    parser.add_argument('mbox_file')
    parser.add_argument('output_dir')
    args = parser.parse_args()
    mbox_file = args.mbox_file
    print(f'processing {mbox_file}', file=sys.stderr)
    outDir = args.output_dir
    if not os.path.exists(outDir):
        os.makedirs(outDir)
    # Create .gitignore file in outDir
    gitignore_path = os.path.join(outDir, '.gitignore')
    with open(gitignore_path, 'w') as f:
        f.write('*\n')
    results: dict[str, list[MsgInfo]] = {}
    maxResults = 100
    for index, message in enumerate(mailbox.mbox(args.mbox_file)):
        if index >= maxResults:
            break
        print('----------------------------------------------------')
        dkimSigs = message.get_all('DKIM-Signature')
        if not dkimSigs:
            continue
        for sig in dkimSigs:
            dkimRecord = decode_dkim_header_field(sig)
            print(dkimRecord, file=sys.stderr)
            domain = dkimRecord['d']
            selector = dkimRecord['s']
            print(dkimRecord['h'])
            includeHeaders = dkimRecord['h'].split(':')
            includeHeaders = list(map(lambda x: x.strip(), includeHeaders))
            canonicalize = dkimRecord['c']
            signAlgo = dkimRecord['a']
            canonicalizeTuple = list(map(lambda x: x.encode(), canonicalize.split('/')))
            bodyHash = dkimRecord['bh']
            bodyLen = dkimRecord.get('l', None)
            if bodyLen:
                print('body length param not supported yet, skipping')
                continue

            logging.basicConfig(format='>>>>>>>>>> %(levelname)s: %(message)s', level=logging.DEBUG)
            signlogger = logging.getLogger()
            signlogger.debug(f"signing...")

            infoOut = {}

            d = dkim.DKIM(str(message).encode(), logger=signlogger, signature_algorithm=signAlgo.encode(), linesep=b'\r\n', tlsrpt=False, debug_content=True)
            d.sign(selector.encode(),
                         domain.encode(),
                         privkey.encode(),
                         canonicalize=canonicalizeTuple,
                         include_headers=list(map(lambda x: x.encode(), includeHeaders)),
                         length=False,
                         preknownBodyHash=bodyHash.encode(),
                         infoOut=infoOut)
            print('infoOut:', infoOut)
            signedData = infoOut['signedData']
            signature = infoOut['signature']
            dskey = domain + "_" + selector
            if dskey not in results:
                results[dskey] = []
            results[dskey].append(MsgInfo(str(message), signedData, signature))

    for dskey, msgInfos in results.items():
        print(f'{dskey}:')
        outDirDsp = os.path.join(outDir, dskey)
        if len(msgInfos) < 2:
            continue
        for index, msgInfo in enumerate(msgInfos):
            #print(f'  {msgInfo.fullMsg}')
            print(f'  signedData: {msgInfo.signedData}')
            print(f'  signature: {msgInfo.signature}')
            outDirDspMsgN = os.path.join(outDirDsp, str(index))
            print(f'  outDirDspMsgN: {outDirDspMsgN}')
            if not os.path.exists(outDirDspMsgN):
                os.makedirs(outDirDspMsgN)
            with open(os.path.join(outDirDspMsgN, 'fullMsg.txt'), 'w') as f:
                f.write(msgInfo.fullMsg)
            with open(os.path.join(outDirDspMsgN, 'signedData'), 'wb') as f:
                f.write(msgInfo.signedData)
            with open(os.path.join(outDirDspMsgN, 'signedData.sig'), 'wb') as f:
                f.write(msgInfo.signature)


if __name__ == '__main__':
    main()
