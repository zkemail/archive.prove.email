## Extract signed data from an mbox file

```bash
python3 mbox_extract_signatures.py MBOX_FILE OUTPUT_DIR
```

This command extracts signed data and signatures from each message in an mbox file and puts it a directory structure:

```
output_dir/domainX/selectorY/messageZ/data
output_dir/domainX/selectorY/messageZ/data.sig
...
```

## Find RSA keys from signed data

This command finds RSA keys from signed data and signatures in the directory structure created by `mbox_extract_signatures.py`.

```bash
./solve_msg_pairs.py OUTPUT_DIR
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

## Using Docker

### Install

```bash
docker pull sagemath/sagemath
```

### Run

```bash
docker build --tag sagemath .
docker run --mount type=bind,source=$(pwd),target=/app --workdir=/app sagemath:latest sage sigs2rsa.py FILE1 FILE2
```

## Using Apt packages (Ubuntu 23.10)

### Install

```bash
sudo apt install sagemath

# see https://stackoverflow.com/a/77705060/961254

curl \
-O https://mirror.enzu.com/ubuntu/pool/universe/s/singular/libsingular4-dev-common_4.3.1-p3+ds-1_all.deb \
-O https://mirror.enzu.com/ubuntu/pool/universe/s/singular/libsingular4-dev_4.3.1-p3+ds-1_amd64.deb \
-O https://mirror.enzu.com/ubuntu/pool/universe/s/singular/libsingular4m3n0_4.3.1-p3+ds-1_amd64.deb \
-O https://mirror.enzu.com/ubuntu/pool/universe/s/singular/singular-data_4.3.1-p3+ds-1_all.deb \
-O https://mirror.enzu.com/ubuntu/pool/universe/s/singular/singular-modules_4.3.1-p3+ds-1_amd64.deb \
-O https://mirror.enzu.com/ubuntu/pool/universe/s/singular/singular-ui_4.3.1-p3+ds-1_amd64.deb \
-O https://mirror.enzu.com/ubuntu/pool/universe/s/singular/singular_4.3.1-p3+ds-1_amd64.deb \


sudo dpkg -i libsingular4-dev-common_4.3.1-p3+ds-1_all.deb \
libsingular4-dev_4.3.1-p3+ds-1_amd64.deb \
libsingular4m3n0_4.3.1-p3+ds-1_amd64.deb \
singular-data_4.3.1-p3+ds-1_all.deb \
singular-modules_4.3.1-p3+ds-1_amd64.deb \
singular-ui_4.3.1-p3+ds-1_amd64.deb \
singular_4.3.1-p3+ds-1_amd64.deb

sudo apt-mark hold \
libsingular4-dev-common \
libsingular4-dev \
libsingular4m3n0 \
singular-data \
singular-modules \
singular-ui \
singular

rm -f libsingular4-dev-common_4.3.1-p3+ds-1_all.deb \
libsingular4-dev_4.3.1-p3+ds-1_amd64.deb \
libsingular4m3n0_4.3.1-p3+ds-1_amd64.deb \
singular-data_4.3.1-p3+ds-1_all.deb \
singular-modules_4.3.1-p3+ds-1_amd64.deb \
singular-ui_4.3.1-p3+ds-1_amd64.deb \
singular_4.3.1-p3+ds-1_amd64.deb
```

### Run

```bash
sage sigs2rsa.py FILE1 FILE2
```
