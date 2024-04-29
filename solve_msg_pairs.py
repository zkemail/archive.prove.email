#!.venv/bin/python3
import argparse
import os
import subprocess
import sys

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('rootdir')
    args = parser.parse_args()
    rootdir = args.rootdir
    for d in os.listdir(rootdir):
        domainDir = os.path.join(rootdir, d)
        if os.path.isdir(domainDir):
            selectorDirs = os.listdir(domainDir)
            for s in selectorDirs:
                dspDir = os.path.join(domainDir, s)
                print(dspDir, file=sys.stderr)
                msgDirs = os.listdir(dspDir)
                msgDirA = os.path.join(dspDir, msgDirs[0])
                msgDirB = os.path.join(dspDir, msgDirs[1])
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
