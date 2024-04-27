import os
import argparse
import sys
import mailbox
import base64

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
    #print(f'decode_dkim_header_field: {dkimData}', file=sys.stderr)
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
    signedData: bytes
    signature: bytes


def write_msg_info(msgInfo: MsgInfo, outDir: str, dskey: str, index: int):
    outDirDsp = os.path.join(outDir, dskey)
    #print(f'  {msgInfo.fullMsg}', file=sys.stderr)
    #print(f'  signedData: {msgInfo.signedData}', file=sys.stderr)
    #print(f'  signature: {msgInfo.signature}', file=sys.stderr)
    outDirDspMsgN = os.path.join(outDirDsp, str(index))
    #print(f'  outDirDspMsgN: {outDirDspMsgN}', file=sys.stderr)
    if not os.path.exists(outDirDspMsgN):
        os.makedirs(outDirDspMsgN)
    with open(os.path.join(outDirDspMsgN, 'data'), 'wb') as f:
        f.write(msgInfo.signedData)
    with open(os.path.join(outDirDspMsgN, 'data.sig'), 'wb') as f:
        f.write(msgInfo.signature)


def main():
    parser = argparse.ArgumentParser(description='extract domains and selectors from the DKIM-Signature header fields in an mbox file and output them in TSV format')
    parser.add_argument('mbox_file')
    parser.add_argument('output_dir')
    parser.add_argument('--skip', type=int, default=0, help='skip the first N messages')
    parser.add_argument('--take', type=int, default=0, help='take the first N messages (0 = all remaining)')
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
    message_counter = 0
    print(f'processing {args.mbox_file}', file=sys.stderr)
    mb = mailbox.mbox(args.mbox_file)
    print(f'loaded {args.mbox_file}', file=sys.stderr)
    skip = args.skip
    take = args.take
    for message in mb:
        message_counter += 1
        if message_counter <= skip:
            continue
        if take > 0 and message_counter > skip + take:
            break

        print(f'-----------------------{message_counter}-------------------------', file=sys.stderr)
        dkimSignatureFields = message.get_all('DKIM-Signature')
        if not dkimSignatureFields:
            continue
        for field in dkimSignatureFields:
            tags = decode_dkim_header_field(field)
            domain = tags['d']
            selector = tags['s']
            print(f'domain: {domain}, selector: {selector}', file=sys.stderr)
            # includeHeaders = tags['h'].split(':')
            # includeHeaders = list(map(lambda x: x.strip(), includeHeaders))
            # if 'received' in map(lambda x: x.lower(), includeHeaders):
            #     #print('received in includeHeaders not supported, skipping', file=sys.stderr)
            #     continue
            #canonicalize = tags['c']
            signAlgo = tags['a']
            if signAlgo != 'rsa-sha256' and signAlgo != 'rsa-sha1':
                print(f'skip signAlgo that is not rsa-sha256 or rsa-sha1: {signAlgo}', file=sys.stderr)
                continue
            #canonicalizeTuple = list(map(lambda x: x.encode(), canonicalize.split('/')))
            bodyHash = tags.get('bh', None)
            if not bodyHash:
                print('body hash not found, skipping', file=sys.stderr)
                continue
            bodyLen = tags.get('l', None)
            if bodyLen:
                print('body length param not supported yet, skipping', file=sys.stderr)
                continue
            signature_tag = tags.get('b', None)
            if not signature_tag:
                print('signature tag not found, skipping', file=sys.stderr)
                continue
            signature_base64 = ''.join(list(map(lambda x: x.strip(), signature_tag.splitlines())))
            signature = base64.b64decode(signature_base64)

            infoOut = {}
            d = dkim.DKIM(str(message).encode(), debug_content=True)
            # d.sign(selector.encode(),
            #        domain.encode(),
            #        privkey.encode(),
            #        canonicalize=canonicalizeTuple,
            #        include_headers=list(map(lambda x: x.encode(), includeHeaders)),
            #        length=False,
            #        preknownBodyHash=bodyHash.encode(),
            #        infoOut=infoOut)

            from dkimpy.dkim.dnsplug import get_txt_dnspython
            try:
                sig_result = d.verify(0, dnsfunc=get_txt_dnspython, infoOut=infoOut)
            except dkim.ValidationError as e:
                print(f'ValidationError: {e}', file=sys.stderr)
                continue
            print('infoOut:', infoOut, file=sys.stderr)
            try:
                signed_data = infoOut['signed_data']
            except KeyError:
                print('signed_data not found, skipping', file=sys.stderr)
                continue

            print(f'sig_result: {sig_result}', file=sys.stderr)
            if not sig_result:
                print('signature not ok, skipping', file=sys.stderr)
                continue

            print('signature ok', file=sys.stderr)
            dskey = domain + "_" + selector
            msg_info = MsgInfo(signed_data, signature)
            if dskey in results:
                existing_results = results[dskey]
                if len(existing_results) == 1:
                    write_msg_info(existing_results[0], outDir, dskey, 0)
                write_msg_info(msg_info, outDir, dskey, len(results[dskey]))
            else:
                results[dskey] = []
            results[dskey].append(msg_info)


if __name__ == '__main__':
    main()
