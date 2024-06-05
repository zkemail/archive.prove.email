dkimpy - DKIM (DomainKeys Identified Mail)
https://launchpad.net/dkimpy/

Friendly fork of:
http://hewgill.com/pydkim/

# INTRODUCTION

dkimpy is a library that implements DKIM (DomainKeys Identified Mail) email
signing and verification.  Basic DKIM requirements are defined in RFC 6376:

https://tools.ietf.org/html/rfc6376

# VERSION

This is dkimpy 1.1.6.

# REQUIREMENTS

Dependencies will be automatically included for normal DKIM usage.  The
extras_requires feature 'ed25519' will add the dependencies needed for signing
and verifying using the new DCRUP ed25519-sha256 algorithm.  The
extras_requires feature 'ARC' will add the extra dependencies needed for ARC.
Similarly, extras_requires feature 'asyncio' will add the extra dependencies
needed for asyncio.

 - Python 3.x >= 3.5.  Recent versions have not been on python3 < 3.4, but
   may still work on earlier python3 versions.
 - dnspython or py3dns. dnspython is preferred if both are present and
   installed to satisfy the DNS module requirement if neither are installed.
 - authres.  Needed for ARC.
 - PyNaCl.  Needed for use of ed25519 capability.
 - aiodns.  Needed for asycnio (Requires python3.5 or later)

# INSTALLATION

This package includes a scripts and man pages.  For those to be installed when
installing using setup.py, the following incantation is required because
setuptools developers decided not being able to do this by default is a
feature:

```python3 setup.py install --single-version-externally-managed --record=/dev/null```

# DOCUMENTATION

An online version of the package documentation for the most recent release can
be found at:

https://pymilter.org/pydkim/

# TESTING

To run dkimpy's test suite:

```PYTHONPATH=. python3 dkim```

or

```python3 test.py```

or

```PYTHONPATH=. python3 -m unittest dkim.tests.test_suite```


Alternatively, if you have testrepository installed:

```testr init```

```testr run```

You should install all optional dependencies required for the test suite, e.g.
by creating a virtualenv and using:

```pip install -e '.[testing]'```

The included ARC tests are very limited.  The primary testing method for ARC
is using the ARC test suite: https://github.com/ValiMail/arc_test_suite

As of 0.6.0, all tests pass for both python2.7 and python3. The test suite
 ships with test runners for dkimpy.  After downloading the test suite, you
 can run the signing and validation tests like this:

```python3 ./testarc.py sign runners/arcsigntest.py```
```python3 ./testarc.py validate runners/arcverifytest.py```

As ov version 1.1.0, python2.7 is no longer supported.

# USAGE

The dkimpy library offers one module called dkim. The sign() function takes an
RFC822 formatted message, along with some signing options, and returns a
DKIM-Signature header line that can be prepended to the message. The verify()
function takes an RFC822 formatted message, and returns True or False depending
on whether the signature verifies correctly.  There is also a DKIM class which
can be used to perform these functions in a more modern way.

In version 0.9.0, the default set of header fields that are oversigned was
changed from 'from', 'subject', 'date' to 'from' to reduce fragility of
signatures.  To restore the previous behavior, you can add them back after
instantiating your DKIM class using the add_frozen function as shown in the
following example:

```python
>>> dkim = DKIM()
>>> dkim.add_frozen((b'date',b'subject'))
>>> [text(x) for x in sorted(dkim.frozen_sign)]
['date', 'from', 'subject']
```

## DKIM RSA MODERNIZATION (RFC 8301)

RFC8301 updated DKIM requirements in two ways:

1.  It set the minimum valid RSA key size to 1024 bits.
2.  It removed use of rsa-sha1.

As of version 0.7, the dkimpy defaults largely support these requirements.

It is possible to override the minimum key size to a lower value, but this is
strongly discouraged.  As of 2018, keys much smaller than the minimum are not
difficult to factor.

The code for rsa-sha1 signing and verification is retained, but not used for
signing by default.  Future releases will raise warnings and then errors when
verifying rsa-sha1 signatures.  There are still some significant users of
rsa-sha1 signatures, so operationally it's premature to disable verification
of rsa-sha1.

## ED25519 (RFC 8463) SUPPORT

As of version 0.7, experimental signing and verifying of DKIM Ed25519
signatures is supported as described in draft-ietf-dcrup-dkim-crypto:

https://datatracker.ietf.org/doc/draft-ietf-dcrup-dkim-crypto/

The RFC that documents ed25519 DKIM signatures, RFC 8463, has been released
and dkimpy 0.7 and later are aligned to its requirements.  As of 0.8, ed25519
need not be considered experimental.  The dkimpy implementation has
successfully interoperated with three other implementations and the technical
parameters for ed25519-sha256 are defined and stable.

To install from pypi with the required optional depenencies, use the ed25519
option:

```pip install -e '.[ed25519]'```

## DKIM SCRIPTS

Three helper programs are also supplied: dknewkey, dkimsign and
dkimverify

dknewkey is s script that produces private and public key pairs suitable
for use with DKIM.  Note that the private key file format used for ed25519 is
not standardized (there is no standard) and is unique to dkimpy.  Creation of
keys should be done in a secure environment.  If an unauthorized entity gains
access to current private keys they can generate signed email that will pass
DKIM checkes and will be difficult to repudiate.

dkimsign is a filter that reads an RFC822 message on standard input, and
writes the same message on standard output with a DKIM-Signature line
prepended. The signing options are specified on the command line:

dkimsign selector domain privatekeyfile [identity]

The identity is optional and defaults to "@domain".

dkimverify reads an RFC822 message on standard input, and returns with exit
code 0 if the signature verifies successfully. Otherwise, it returns with exit
code 1. 

## ARC (Authenticated Receive Chain)

As of version 0.6.0, dkimpy provides experimental support for ARC (Authenticated
Received Chain).  See RFC 8617 for the current version of ARC:

https://tools.ietf.org/html/rfc8617

In addition to arcsign and arcverify, the dkim module now provides
arc_sign and arc_verify functions as well as an ARC class.

If an invalid authentication results header field is included in the set for
ARC, it is ignored and no error is raised.

Both DKIM ed25519 and ARC are now considered stable (no longer experimantal).

## ASYNC SUPPORT

As of version 1.0, an alternative to dkim.verify for use in an async
environment is provied.  It requires aiodns, https://pypi.org/project/aiodns/.
Here is a simple example of dkim.verify_async usage:

```python
>>> sys.stdin = sys.stdin.detach()
>>>
>>> async def main():
>>>     res = await dkim.verify_async(message)
>>>     return res
>>>
>>> if __name__ == "__main__":
>>>     res = asyncio.run(main())
```

This feature requires python3.5 or newer.

If aiodns is available, the async functions will be used.  To avoide async
when aiodns is availale, set dkim.USE_ASYNC = False.

## TLSRPT (TLS Report)

As of version 1.0, the RFC 8460 tlsrpt service type is supported:

https://tools.ietf.org/html/rfc8460

A non-tlsrpt signed with a key record with s=tlsrpt won't verify.  Since the
service type (s=) is optional in the DKIM public key record, it is not
required by RFC 8460.  When checking for a tlsrpt signature, set the tlsrpt=
flag when verifying the signature:

```python
>>> res = dkim.verify(smessage, tlsrpt='strict')
```

If tlsrpt='strict', only public key records with s=tlsrpt will be considered
valid.  If set to tlsrpt=True, the service type is not required, but other
RFC 8460 requirements are applied.

# LIMITATIONS

Dkimpy will correctly sign/verify messages with ASCII or UTF-8 content.
Messages that contain other types of content will not verify correctly.  It
does not yet implement RFC 8616, Email Authentication for Internationalized
Mail.

# FEEDBACK

Bug reports may be submitted to the bug tracker for the dkimpy project on
launchpad.
