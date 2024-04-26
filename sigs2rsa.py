# https://blog.ploetzli.ch/2018/calculating-an-rsa-public-key-from-two-signatures/

import binascii, hashlib
import json
import sys
import sage.all


def pkcs1_padding(size_bytes, hexdigest, hashfn):
    oid = {hashlib.sha256: '608648016503040201', hashlib.sha512: '608648016503040203'}[hashfn]
    result = '06' + ("%02X" % (len(oid) // 2)) + oid + '05' + '00'
    result = '30' + ("%02X" % (len(result) // 2)) + result

    result = result + '04' + ("%02X" % (len(hexdigest) // 2)) + hexdigest
    result = '30' + ("%02X" % (len(result) // 2)) + result

    result = '0001' + ('ff' * int(size_bytes - 3 - len(result) / 2)) + '00' + result
    return result


def hash_pad(size_bytes, data, hashfn):
    hexdigest = hashfn(data).hexdigest()
    return pkcs1_padding(size_bytes, hexdigest, hashfn)


def message_sig_pair(size_bytes, data, signature, hashfn):
    return (sage.all.Integer('0x' + hash_pad(size_bytes, data, hashfn)), sage.all.Integer('0x' + binascii.hexlify(signature).decode('utf-8')))


def find_n(*filenames):
    data_raw = []
    signature_raw = []
    for fn in filenames:
        data_raw.append(open(fn, 'rb').read())
        signature_raw.append(open(fn + '.sig', 'rb').read())
    size_bytes = len(signature_raw[0])
    if any(len(s) != size_bytes for s in signature_raw):
        raise Exception("All signature sizes must be identical")

    for hashfn in [hashlib.sha256, hashlib.sha512]:
        pairs = [message_sig_pair(size_bytes, m, s, hashfn) for (m, s) in zip(data_raw, signature_raw)]
        for e in [0x10001, 3, 17]:
            gcd_input = [(s**e - m) for (m, s) in pairs]
            n = sage.all.gcd(*gcd_input)
            print(f'hashfn={hashfn.__name__}, n={n}, e={e}', file=sys.stderr)
            if n != 1:
                return (n, e)
    return 0, 0


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('file1', type=str)
    parser.add_argument('file2', type=str)
    args = parser.parse_args()
    n, e = find_n(args.file1, args.file2)
    print(json.dumps({'n_hex': hex(n), 'e_hex': hex(e)}))
