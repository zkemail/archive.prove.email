This repository contains a proof of concept for determining the public RSA key from a pair of email messages which are signed with the same private key.

## Setup

### Build the Docker image

```bash
docker build --tag sagemath .
```

### Install Python dependencies

```bash
pip3 install pycryptodome
```

## Extract signed data from an mbox file

```bash
python3 mbox_extract_signatures.py MBOX_FILE DATA_DIR
```

This command extracts signed data (canonicalized headers) and signatures from each message in an mbox file and puts it a directory structure:

```
data_dir/domainX/selectorY/messageZ/data
data_dir/domainX/selectorY/messageZ/data.sig
...
```

## Find public RSA keys from data and signatures

This command finds public RSA keys from signed data and signatures of pairs of messages in the directory structure created by `mbox_extract_signatures.py`.

```bash
python3 solve_msg_pairs.py DATA_DIR
```

Example output:

```
processing mbox_yahoo/service.comms.yahoo.net/ep1
+ docker run --rm --mount type=bind,source=/home/olof/checkout/zk/reconstr_rsa,target=/app --workdir=/app sagemath:latest sage sigs2rsa.py mbox_yahoo/service.comms.yahoo.net/ep1/1/data mbox_yahoo/service.comms.yahoo.net/ep1/2/data
sage.all.gcd cpu time=18.420908999999998
removing small prime factor 2
hashfn=openssl_sha256, n=(1024 bit number), e=65537
found large GCD for mbox_yahoo/service.comms.yahoo.net/ep1
PEM: -----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDcDXY0US14pjNIvn7nDbRpzmuI
Hp0Uq75Zv3+3rTNoJVDgP8//HCo/9Xb3BttLwL8J7sMVHQ0SHsG27X8SYdViDFwA
cLSYu6q5wTTaRKO80UUbIVM6YLKcdo9uPd2XyfvmxdcIth2ZMHC6HIVesvfDnf3K
0asuP07jtYJK0Zdn4QIDAQAB
-----END PUBLIC KEY-----
DER: MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDcDXY0US14pjNIvn7nDbRpzmuIHp0Uq75Zv3+3rTNoJVDgP8//HCo/9Xb3BttLwL8J7sMVHQ0SHsG27X8SYdViDFwAcLSYu6q5wTTaRKO80UUbIVM6YLKcdo9uPd2XyfvmxdcIth2ZMHC6HIVesvfDnf3K0asuP07jtYJK0Zdn4QIDAQAB
```
