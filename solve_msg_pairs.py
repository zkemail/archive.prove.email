#!.venv/bin/python3
import argparse
import os
import subprocess
import sys


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
            print(dspPath, file=sys.stderr)
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
            print(" ".join(cmd), file=sys.stderr)
            subprocess.run(cmd)
