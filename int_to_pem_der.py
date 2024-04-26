#!.venv/bin/python3
import binascii
import sys
import json
from Crypto.PublicKey import RSA

if __name__ == '__main__':
    data = json.load(sys.stdin)
    n_hex_str = data['n_hex']
    e_hex_str = data['e_hex']
    n = int(n_hex_str, 16)
    e = int(e_hex_str, 16)
    print(hex(n))
    print(hex(e))
    keyPEM = RSA.construct((n, e)).exportKey(format='PEM')
    print('PEM:', keyPEM.decode('utf-8'))
    keyDER = RSA.importKey(keyPEM).exportKey(format='DER')
    keyDER_base64 = binascii.b2a_base64(keyDER).decode('utf-8')
    print('DER:', keyDER_base64)
