# https://blog.ploetzli.ch/2018/calculating-an-rsa-public-key-from-two-signatures/

import binascii, hashlib
import json
import os
import sys
import sage.all
import logging


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


def remove_small_prime_factors(n):
    for p in sage.all.primes(10000):
        while n % p == 0:
            logging.debug(f'removing small prime factor {p}')
            n = n // p
    return n


def find_n(messages: list[bytes], signatures: list[bytes]):
    size_bytes = len(signatures[0])
    if any(len(s) != size_bytes for s in signatures):
        logging.error(f"all signature sizes must be identical")
        return 0, 0

    if len(set(signatures)) != len(signatures):
        logging.error(f"duplicate signatures found")
        return 0, 0

    for hashfn in [hashlib.sha256]:
        pairs = [message_sig_pair(size_bytes, m, s, hashfn) for (m, s) in zip(messages, signatures)]
        logging.error(f'ppppppppppppp pairs={pairs}')
        for e in [0x10001, 3, 17]:
            logging.debug(f'solving for hashfn={hashfn.__name__}, e={e}')
            gcd_input = [(s**e - m) for (m, s) in pairs]

            starttime = sage.all.cputime()
            n = sage.all.gcd(*gcd_input)
            logging.info(f'TTTT sage.all.gcd cpu time={sage.all.cputime(starttime)}')
            #logging.info(f'gcd_input count: {len(gcd_input)}')
            #logging.info(f'gcd_input 0, num bits: {gcd_input[0].nbits()}')
            #logging.info(f'gcd_input 1, num bits: {gcd_input[1].nbits()}')
            
            if n.nbits() > 10000:
                logging.error(f'skip n with > 10000 bits')
                continue

            n = remove_small_prime_factors(n)
            logging.info(f'result n=({n.nbits()} bit number)')

            if n > 1:
                logging.info(f'found gcd, n={n}')
                return (n, e)
    return 0, 0


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('data1_base64')
    parser.add_argument('signature1_base64')
    parser.add_argument('data2_base64')
    parser.add_argument('signature2_base64')
    parser.add_argument('--loglevel', type=int, default=logging.INFO)
    args = parser.parse_args()
    data1 = binascii.a2b_base64(args.data1_base64)
    data2 = binascii.a2b_base64(args.data2_base64)
    signature1 = binascii.a2b_base64(args.signature1_base64)
    signature2 = binascii.a2b_base64(args.signature2_base64)
    logging.root.name = os.path.basename(__file__)
    logging.basicConfig(level=args.loglevel, format='%(name)s: %(levelname)s: %(message)s')
    n, e = find_n([data1, data2], [signature1, signature2])
    print(json.dumps({'n_hex': hex(n), 'e_hex': hex(e)}))
