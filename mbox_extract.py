import argparse
import logging
import sys
import mailbox
import dkim
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
    msg: str
    sig: str


def get_dkim_pubkey(domain: str, selector: str):
    # fetch the DKIM public key for a domain and selector
    # this is a placeholder implementation that always returns the same key
    return 'v=DKIM1; k=rsa; p=MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDd3Zu5bL8zj6n2z1Zw4X2rXj5FyJtJ0V3aLlQvZ6QV6J9Q2LzBqIj7kA2J7XzjN4Z3tQz7X1z3J3Z'


#def recalculate_dkim_signature(msg: mailbox.mboxMessage, existingDkimSignatureKeyValues: dict[str, str], publicKey: str):

def sign_msg(dkim_domain: str, dkim_selector: str, msg: str, includeHeaders: list[str], canonicalizeTuple: list[bytes]):
    print(f'sign_msg: signing message with DKIM for domain {dkim_domain} and selector {dkim_selector}', file=sys.stderr)
    # sign a message with DKIM
    logging.basicConfig(format='>>>>>>>>>> %(levelname)s: %(message)s', level=logging.DEBUG)
    signlogger = logging.getLogger()
    signlogger.debug(f"signing...")
    sig = dkim.sign(
        message=msg.encode(),
        selector=str(dkim_selector).encode(),
        domain=dkim_domain.encode(),
        privkey=privkey.encode(),
        include_headers=list(map(lambda x: x.encode(), includeHeaders)),
        canonicalize=canonicalizeTuple,
        logger=signlogger
    )
    #print(sig, file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description='extract domains and selectors from the DKIM-Signature header fields in an mbox file and output them in TSV format')
    parser.add_argument('mbox_file')
    args = parser.parse_args()
    results: dict[str, list[MsgInfo]] = {}
    print(f'processing {args.mbox_file}', file=sys.stderr)
    for index, message in enumerate(mailbox.mbox(args.mbox_file)):
        #print('payload', str(message))

        dkimSigs = message.get_all('DKIM-Signature')
        if not dkimSigs:
            continue
        for sig in dkimSigs:
            dkimRecord = decode_dkim_header_field(sig)
            print(dkimRecord, file=sys.stderr)
            domain = dkimRecord['d']
            selector = dkimRecord['s']
            includeHeaders = dkimRecord['h']
            canonicalize = dkimRecord['c']
            signAlgo = dkimRecord['a']
            canonicalizeTuple = list(map(lambda x: x.encode(), canonicalize.split('/')))

            sign_msg(domain, selector, str(message), includeHeaders.split(':'), canonicalizeTuple)
            dskey = domain + "_" + selector
            if dskey not in results:
                results[dskey] = []
            results[dskey].append(MsgInfo('', sig))
        break


if __name__ == '__main__':
    main()
