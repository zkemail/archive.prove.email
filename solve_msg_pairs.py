#!.venv/bin/python3
import argparse
import binascii
import json
import logging
import os
import queue
import subprocess
import sys
import threading
from Crypto.PublicKey import RSA


def subdirs(d):
    return [f for f in os.listdir(d) if os.path.isdir(os.path.join(d, f))]


dsp_directory_queue: "queue.Queue[str]" = queue.Queue()


def call_solver_and_process_result(dspPath):
    logging.info(f'processing {dspPath}')
    msgDirs = subdirs(dspPath)
    if len(msgDirs) < 2:
        logging.error(f'expected at least 2 message directories in {dspPath}')
        return
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
        "--loglevel",
        str(args.loglevel),
    ]
    logging.debug("+ " + " ".join(cmd))
    output = subprocess.check_output(cmd)
    data = json.loads(output)
    n = int(data['n_hex'], 16)
    e = int(data['e_hex'], 16)
    if (n < 2):
        logging.info(f'no large GCD found for {dspPath}')
        return
    try:
        logging.info(f'found large GCD for {dspPath}')
        rsa_key = RSA.construct((n, e))
        if args.output_format == 'PEM':
            keyPEM = rsa_key.exportKey(format='PEM')
            print('PEM:', keyPEM.decode('utf-8'))
        else:
            keyDER = rsa_key.exportKey(format='DER')
            keyDER_base64 = binascii.b2a_base64(keyDER).decode('utf-8')
            print('DER:', keyDER_base64)
    except ValueError as e:
        logging.error(f'ValueError: {e}')
        return


def read_and_resolve_worker():
    while True:
        dspPath = dsp_directory_queue.get()
        call_solver_and_process_result(dspPath)
        dsp_directory_queue.task_done()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('rootdir')
    parser.add_argument('--debug', action="store_const", dest="loglevel", const=logging.DEBUG, default=logging.INFO)
    parser.add_argument('--output-format', type=str, default='DER', choices=['DER', 'PEM'])
    parser.add_argument('--threads', type=int, default=1)
    args = parser.parse_args()
    rootdir = args.rootdir

    logging.root.name = os.path.basename(__file__)
    logging.basicConfig(level=args.loglevel, format='%(name)s: %(levelname)s: %(message)s')
    for d in subdirs(rootdir):
        domainPath = os.path.join(rootdir, d)
        for s in subdirs(domainPath):
            dspPath = os.path.join(domainPath, s)
            logging.debug(f'queuing {dspPath}')
            dsp_directory_queue.put(dspPath)

    for _i in range(args.threads):
        logging.debug(f'starting thread {_i}')
        t_in = threading.Thread(target=read_and_resolve_worker)
        t_in.start()

    dsp_directory_queue.join()
