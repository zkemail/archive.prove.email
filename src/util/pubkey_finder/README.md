This directory contains tools for finding the public RSA keys from pairs of email messages which are signed with the same private key.

## Setup

### Install Python dependencies

```bash
pip3 install pycryptodome
pip3 install gmpy2
```

## Find public RSA keys from en email archive

These commands extract signed data (canonicalized headers) and signatures from each message in an email archive,
and searches for public RSA keys for pairs of messages with the same DKIM domain and selector.

Load mbox files and extract signed data and signatures to corresponding .datasig files:

```bash
python3 extract_signed_data.py --mbox-files inbox1.mbox inbox2.mbox
```

Find public RSA keys from the .datasig files

```bash
python3 find_public_keys.py --datasig-files inbox1.mbox.datasig inbox2.mbox.datasig
```

Run `python3 extract_signed_data.py --help` and `python3 find_public_keys.py --help` for more information.
