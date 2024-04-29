#!.venv/bin/python3
import argparse
import binascii
import json
import os
import subprocess
import sys
from Crypto.PublicKey import RSA


def subdirs(d):
    return [f for f in os.listdir(d) if os.path.isdir(os.path.join(d, f))]


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('rootdir')
    args = parser.parse_args()
    rootdir = args.rootdir
    for d in subdirs(rootdir):
        domainPath = os.path.join(rootdir, d)
        for s in subdirs(domainPath):
            dspPath = os.path.join(domainPath, s)
            print()
            print(f'processing {dspPath}', file=sys.stderr)
            msgDirs = subdirs(dspPath)
            if len(msgDirs) < 2:
                print(f'expected at least 2 message directories in {dspPath}', file=sys.stderr)
                continue
            msgDirA = os.path.join(dspPath, msgDirs[0])
            msgDirB = os.path.join(dspPath, msgDirs[1])
            cmd = [
                "docker",
                "run",
                "--rm",
                "--mount",
                f"type=bind,source={os.getcwd()},target=/app",
                "--workdir=/app",
                "sagemath:latest",
                "sage",
                "sigs2rsa.py",
                msgDirA + "/data",
                msgDirB + "/data",
            ]
            print("+ " + " ".join(cmd), file=sys.stderr)
            output = subprocess.check_output(cmd)
            data = json.loads(output)
            n = int(data['n_hex'], 16)
            e = int(data['e_hex'], 16)
            if (n < 2):
                print(f'no large GCD found for {dspPath}', file=sys.stderr)
                continue
            try:
                print(f'found large GCD for {dspPath}', file=sys.stderr)
                keyPEM = RSA.construct((n, e)).exportKey(format='PEM')
                print('PEM:', keyPEM.decode('utf-8'))
                keyDER = RSA.importKey(keyPEM).exportKey(format='DER')
                keyDER_base64 = binascii.b2a_base64(keyDER).decode('utf-8')
                print('DER:', keyDER_base64)
            except ValueError as e:
                print(f'ValueError: {e}', file=sys.stderr)
                continue
