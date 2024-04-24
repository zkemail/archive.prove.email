# https://blog.ploetzli.ch/2018/calculating-an-rsa-public-key-from-two-signatures/

import binascii, hashlib
from sage.all import *

def pkcs1_padding(size_bytes, hexdigest, hashfn):
    oid = {hashlib.sha256: '608648016503040201'}[hashfn]
    result = '06' + ("%02X" % (len(oid)//2)) + oid + '05' + '00'
    result = '30' + ("%02X" % (len(result)//2)) + result
    
    result = result + '04' + ("%02X" % (len(hexdigest)//2)) + hexdigest
    result = '30' + ("%02X" % (len(result)//2)) + result
    
    result = '0001' + ('ff' * int(size_bytes - 3 - len(result)/2) ) + '00' + result
    return result

def hash_pad(size_bytes, data, hashfn):
    hexdigest = hashfn(data).hexdigest()
    return pkcs1_padding(size_bytes, hexdigest, hashfn)

def message_sig_pair(size_bytes, data, signature, hashfn=hashlib.sha256):
    return ( Integer('0x' + hash_pad(size_bytes, data, hashfn)), Integer('0x' + binascii.hexlify(signature).decode('utf-8')) )

def find_n(*filenames):
    data_raw = []
    signature_raw = []
    for fn in filenames:
        data_raw.append( open(fn, 'rb').read() )
        signature_raw.append( open(fn+'.sig', 'rb').read() )
    size_bytes = len(signature_raw[0])
    if any(len(s) != size_bytes for s in signature_raw):
        raise Exception("All signature sizes must be identical")
    
    for hashfn in [hashlib.sha256]:
        pairs = [message_sig_pair(size_bytes, m, s, hashfn) for (m,s) in zip(data_raw, signature_raw)]
        for e in [0x10001, 3, 17]:
            gcd_input = [ (s^e - m) for (m,s) in pairs ]
            result = gcd(*gcd_input)
            if result != 1:
                return (hashfn, e, result)

