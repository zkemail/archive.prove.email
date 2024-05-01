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

## Find public RSA keys from en email archive

This command extracts signed data (canonicalized headers) and signatures from each message in an email archive,
and searches for public RSA keys for pairs of messages with the same DKIM domain and selector.

Example:

```bash
python3 find_public_keys.py inbox.mbox --debug --threads=1
```

Run `python3 find_public_keys.py --help` for more information.
