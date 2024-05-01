This repository contains a proof of concept for determining the public RSA key from a pair of email messages which are signed with the same private key.

## Setup

Start by cloning this repository and navigating to the repository root directory.

```bash
git clone --recurse-submodules https://github.com/foolo/sigs2rsa.git
cd sigs2rsa
```

### Build the Docker image

```bash
docker build --tag sagemath .
```

### Install Python dependencies

```bash
pip3 install pycryptodome
```

## Extract signed data from an mbox file

Example:

```bash
python3 mbox_extract_signatures.py inbox.mbox mbox_exracted_dir
```

Run `python3 mbox_extract_signatures.py --help` for more information.

This command extracts signed data (canonicalized headers) and signatures from each message in an mbox file and puts it a directory structure:

```
data_dir/domainX/selectorY/messageZ/data
data_dir/domainX/selectorY/messageZ/data.sig
...
```

## Find public RSA keys from data and signatures

This command finds public RSA keys from signed data and signatures of pairs of messages in the directory structure created by `mbox_extract_signatures.py`.

Example:

```bash
python3 solve_msg_pairs.py mbox_exracted_dir --debug --threads 4 --output-format=DER
```

Run `python3 solve_msg_pairs.py --help` for more information.

Example output:

```
solve_msg_pairs.py: DEBUG: queuing mbox_yahoo/service.comms.yahoo.net/ep1
solve_msg_pairs.py: DEBUG: starting thread 0
solve_msg_pairs.py: INFO: processing mbox_yahoo/service.comms.yahoo.net/ep1
solve_msg_pairs.py: DEBUG: + docker run --rm --mount type=bind,source=/home/olof/checkout/zk/reconstr_rsa,target=/app --workdir=/app sagemath:latest sage sigs2rsa.py mbox_yahoo/service.comms.yahoo.net/ep1/1/data mbox_yahoo/service.comms.yahoo.net/ep1/2/data --loglevel 10
sigs2rsa.py: DEBUG: solving for hashfn=openssl_sha256, e=65537
sigs2rsa.py: DEBUG: sage.all.gcd cpu time=18.360299
sigs2rsa.py: DEBUG: removing small prime factor 2
sigs2rsa.py: DEBUG: result n=(1024 bit number)
solve_msg_pairs.py: INFO: found large GCD for mbox_yahoo/service.comms.yahoo.net/ep1
DER: MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDcDXY0US14pjNIvn7nDbRpzmuIHp0Uq75Zv3+3rTNoJVDgP8//HCo/9Xb3BttLwL8J7sMVHQ0SHsG27X8SYdViDFwAcLSYu6q5wTTaRKO80UUbIVM6YLKcdo9uPd2XyfvmxdcIth2ZMHC6HIVesvfDnf3K0asuP07jtYJK0Zdn4QIDAQAB
```
