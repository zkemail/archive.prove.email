#!.venv/bin/python3
import argparse
import os
import subprocess

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('rootdir')
    args = parser.parse_args()
    rootdir = args.rootdir
    for d in os.listdir(rootdir):
        dspDir = os.path.join(rootdir, d)
        if os.path.isdir(dspDir):
            print(dspDir)
            msgDirs = os.listdir(dspDir)
            msgDirA = os.path.join(dspDir, msgDirs[0])
            msgDirB = os.path.join(dspDir, msgDirs[1])
            cmd = [
                "docker",
                "run",
                "--mount",
                f"type=bind,source={os.getcwd()},target=/app",
                "--workdir=/app",
                "sagemath:latest",
                "sage",
                "sigs2rsa.py",
                msgDirA + "/data",
                msgDirB + "/data",
            ]
            print(" ".join(cmd))
            subprocess.run(cmd)
