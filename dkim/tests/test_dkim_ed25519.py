# This software is provided 'as-is', without any express or implied
# warranty.  In no event will the author be held liable for any damages
# arising from the use of this software.
#
# Permission is granted to anyone to use this software for any purpose,
# including commercial applications, and to alter it and redistribute it
# freely, subject to the following restrictions:
#
# 1. The origin of this software must not be misrepresented; you must not
#    claim that you wrote the original software. If you use this software
#    in a product, an acknowledgment in the product documentation would be
#    appreciated but is not required.
# 2. Altered source versions must be plainly marked as such, and must not be
#    misrepresented as being the original software.
# 3. This notice may not be removed or altered from any source distribution.
#
# Copyright (c) 2011 William Grant <me@williamgrant.id.au>
# Copyright (c) 2018 Scott Kitterman <scott@kitterman.com>

import email
import os.path
import unittest
import time

import dkim


def read_test_data(filename):
    """Get the content of the given test data file.

    The files live in dkim/tests/data.
    """
    path = os.path.join(os.path.dirname(__file__), 'data', filename)
    with open(path, 'rb') as f:
        return f.read()


class TestFold(unittest.TestCase):

    def test_short_line(self):
        self.assertEqual(
            b"foo", dkim.fold(b"foo"))

    def test_long_line(self):
        # The function is terribly broken, not passing even this simple
        # test.
        self.assertEqual(
            b"foo" * 24 + b"\r\n foo", dkim.fold(b"foo" * 25))


class TestSignAndVerify(unittest.TestCase):
    """End-to-end signature and verification tests."""

    def setUp(self):
        self.message = read_test_data("ed25519test.msg")
        self.message2 = read_test_data("ed25519test2.msg")
        self.message3 = read_test_data("rfc6376.msg")
        self.message4 = read_test_data("rfc6376.signed.msg")
        self.key = read_test_data("ed25519test.key")
        self.rfckey = read_test_data("rfc8032_7_1.key")

    def dnsfunc(self, domain, timeout=5):
        sample_dns = """\
k=ed25519; \
p=yi50DjK5O9pqbFpNHklsv9lqaS0ArSYu02qp1S0DW1Y="""

        _dns_responses = {
          'example._domainkey.canonical.com.': sample_dns,
          'test._domainkey.example.net.': """v=DKIM1; k=ed25519; \
p=yi50DjK5O9pqbFpNHklsv9lqaS0ArSYu02qp1S0DW1Y=""",
          'sed._domainkey.test.ex.': read_test_data("eximtest.dns"),
          'brisbane._domainkey.football.example.com.': """v=DKIM1; k=ed25519; \
p=11qYAYKxCrfVS/7TyWQHOg7hcvPapiMlrwIaaPcHURo="""
        }
        try:
            domain = domain.decode('ascii')
        except UnicodeDecodeError:
            return None
        self.assertTrue(domain in _dns_responses,domain)
        return _dns_responses[domain]

    def test_verifies(self):
        # A message verifies after being signed.
        for header_algo in (b"simple", b"relaxed"):
            for body_algo in (b"simple", b"relaxed"):
                sig = dkim.sign(
                    self.message, b"test", b"example.net", self.key,
                    canonicalize=(header_algo, body_algo), signature_algorithm=b'ed25519-sha256')
                res = dkim.verify(sig + self.message, dnsfunc=self.dnsfunc)
                self.assertTrue(res)

    def test_rfc8032_verifies(self):
        # A message using RFC 8032 sample keys verifies after being signed.
        for header_algo in (b"simple", b"relaxed"):
            for body_algo in (b"simple", b"relaxed"):
                sig = dkim.sign(
                    self.message3, b"brisbane", b"football.example.com", self.rfckey,
                    canonicalize=(header_algo, body_algo), signature_algorithm=b'ed25519-sha256')
                res = dkim.verify(sig + self.message3, dnsfunc=self.dnsfunc)
                self.assertTrue(res)

    def test_rfc8032_previous_verifies(self):
        # A message previously signed using RFC 8032 sample keys verifies after being signed.
        for header_algo in (b"simple", b"relaxed"):
            for body_algo in (b"simple", b"relaxed"):
                sig = dkim.sign(
                    self.message3, b"brisbane", b"football.example.com", self.rfckey,
                    canonicalize=(header_algo, body_algo), signature_algorithm=b'ed25519-sha256')
                d = dkim.DKIM(self.message4)
                res = d.verify(dnsfunc=self.dnsfunc)
                self.assertTrue(res)

    def test_simple_signature(self):
        # A message verifies after being signed with SHOULD headers
        for header_algo in (b"simple", b"relaxed"):
             for body_algo in (b"simple", b"relaxed"):
                sig = dkim.sign(
                    self.message, b"test", b"example.net", self.key,
                    canonicalize=(header_algo, body_algo),
                    include_headers=(b'from',) + dkim.DKIM.SHOULD,
                    signature_algorithm=b'ed25519-sha256')
                res = dkim.verify(sig + self.message, dnsfunc=self.dnsfunc)
                self.assertTrue(res)

    def test_verify_third_party(self):
        # Message signed by prototype Exim implementation
        res = dkim.verify(self.message2, dnsfunc=self.dnsfunc)
        self.assertTrue(res)

    def test_add_body_length(self):
        sig = dkim.sign(
            self.message, b"test", b"example.net", self.key, length=True,
                signature_algorithm=b'ed25519-sha256')
        msg = email.message_from_string(self.message.decode('utf-8'))
        self.assertIn('; l=%s' % len(msg.get_payload() + '\n'), sig.decode('utf-8'))
        res = dkim.verify(sig + self.message, dnsfunc=self.dnsfunc)
        self.assertTrue(res)

    def test_altered_body_fails(self):
        # An altered body fails verification.
        for header_algo in (b"simple", b"relaxed"):
            for body_algo in (b"simple", b"relaxed"):
                sig = dkim.sign(
                    self.message, b"test", b"example.net", self.key,
                    signature_algorithm=b'ed25519-sha256')
                res = dkim.verify(
                    sig + self.message + b"foo", dnsfunc=self.dnsfunc)
                self.assertFalse(res)

    def test_badly_encoded_domain_fails(self):
        # Domains should be ASCII. Bad ASCII causes verification to fail.
        sig = dkim.sign(self.message, b"test", b"example.net\xe9", self.key,
            signature_algorithm=b'ed25519-sha256')
        res = dkim.verify(sig + self.message, dnsfunc=self.dnsfunc)
        self.assertFalse(res)

    def test_dkim_signature_canonicalization(self):
      # <https://bugs.launchpad.net/ubuntu/+source/pydkim/+bug/587783>
      # Relaxed-mode header signing is wrong
      # <https://bugs.launchpad.net/dkimpy/+bug/939128>
      # Simple-mode signature header verification is wrong
      # (should ignore FWS anywhere in signature tag: b=)
      sample_msg = b"""\
From: mbp@canonical.com
To: scottk@example.net
Subject: this is my
    test message
""".replace(b'\n', b'\r\n')

      sample_privkey = b"""\
fL+5V9EquCZAovKik3pA6Lk9zwCzoEtjIuIqK9ZXHHA=\
"""

      sample_pubkey = """\
yi50DjK5O9pqbFpNHklsv9lqaS0ArSYu02qp1S0DW1Y=\
"""

      for header_mode in [dkim.Relaxed, dkim.Simple]:

        dkim_header = dkim.sign(sample_msg, b'example', b'canonical.com',
            sample_privkey, canonicalize=(header_mode, dkim.Relaxed),
            signature_algorithm=b'ed25519-sha256')
        # Folding dkim_header affects b= tag only, since dkim.sign folds
        # sig_value with empty b= before hashing, and then appends the
        # signature.  So folding dkim_header again adds FWS to
        # the b= tag only.  This should be ignored even with
        # simple canonicalization.
        # http://tools.ietf.org/html/rfc4871#section-3.5
        signed = dkim.fold(dkim_header) + sample_msg
        result = dkim.verify(signed,dnsfunc=self.dnsfunc)
        self.assertTrue(result)
        dkim_header = dkim.fold(dkim_header)
        # use a tab for last fold to test tab in FWS bug
        pos = dkim_header.rindex(b'\r\n ')
        dkim_header = dkim_header[:pos]+b'\r\n\t'+dkim_header[pos+3:]
        result = dkim.verify(dkim_header + sample_msg,
                dnsfunc=self.dnsfunc)
        self.assertTrue(result)

    def test_extra_headers(self):
        # <https://bugs.launchpad.net/dkimpy/+bug/737311>
        # extra headers above From caused failure
        #message = read_test_data("test_extra.message")
        message = read_test_data("message.mbox")
        for header_algo in (b"simple", b"relaxed"):
            for body_algo in (b"simple", b"relaxed"):
                d = dkim.DKIM(message)
                # bug requires a repeated header to manifest
                d.should_not_sign.remove(b'received')
                sig = d.sign(b"test", b"example.net", self.key,
                    signature_algorithm=b'ed25519-sha256',
                    include_headers=d.all_sign_headers(),
                    canonicalize=(header_algo, body_algo))
                dv = dkim.DKIM(sig + message)
                res = dv.verify(dnsfunc=self.dnsfunc)
                self.assertEqual(d.include_headers,dv.include_headers)
                s = dkim.select_headers(d.headers,d.include_headers)
                sv = dkim.select_headers(dv.headers,dv.include_headers)
                self.assertEqual(s,sv)
                self.assertTrue(res)

    def test_multiple_from_fails(self):
        # <https://bugs.launchpad.net/dkimpy/+bug/644046>
        # additional From header fields should cause verify failure
        hfrom = b'From: "Resident Evil" <sales@spammer.com>\r\n'
        h,b = self.message.split(b'\n\n',1)
        for header_algo in (b"simple", b"relaxed"):
            for body_algo in (b"simple", b"relaxed"):
                sig = dkim.sign(
                    self.message, b"test", b"example.net", self.key,
                    signature_algorithm=b'ed25519-sha256')
                # adding an unknown header still verifies
                h1 = h+b'\r\n'+b'X-Foo: bar'
                message = b'\n\n'.join((h1,b))
                res = dkim.verify(sig+message, dnsfunc=self.dnsfunc)
                self.assertTrue(res)
                # adding extra from at end should not verify
                h1 = h+b'\r\n'+hfrom.strip()
                message = b'\n\n'.join((h1,b))
                res = dkim.verify(sig+message, dnsfunc=self.dnsfunc)
                self.assertFalse(res)
                # add extra from in front should not verify either
                h1 = hfrom+h
                message = b'\n\n'.join((h1,b))
                res = dkim.verify(sig+message, dnsfunc=self.dnsfunc)
                self.assertFalse(res)

    def test_no_from_fails(self):
        # Body From is mandatory to be in the message and mandatory to sign
        sigerror = False
        sig = ''
        message = read_test_data('test_nofrom.message')
        selector = 'test'
        domain = 'example.net'
        identity = None
        try:
            sig = dkim.sign(message, selector, domain,
                read_test_data('ed25519test.key'), identity = identity,
                signature_algorithm=b'ed25519-sha256')
        except dkim.ParameterError as x:
            sigerror = True
        self.assertTrue(sigerror)

    def test_validate_signature_fields(self):
      sig = {b'v': b'1',
      b'a': b'ed25519-sha256',
      b'b': b'K/UUOt8lCtgjp3kSTogqBm9lY1Yax/NwZ+bKm39/WKzo5KYe3L/6RoIA/0oiDX4kO\n \t Qut49HCV6ZUe6dY9V5qWBwLanRs1sCnObaOGMpFfs8tU4TWpDSVXaNZAqn15XVW0WH\n \t EzOzUfVuatpa1kF4voIgSbmZHR1vN3WpRtcTBe/I=',
      b'bh': b'n0HUwGCP28PkesXBPH82Kboy8LhNFWU9zUISIpAez7M=',
      b'c': b'simple/simple',
      b'd': b'kitterman.com',
      b'i': b'scott@Kitterman.com',
      b'h': b'From:To:Subject:Date:Cc:MIME-Version:Content-Type:\n \t Content-Transfer-Encoding:Message-Id',
      b's': b'2007-00',
      b't': b'1299525798'}
      dkim.validate_signature_fields(sig)
      # try new version
      sigVer = sig.copy()
      sigVer[b'v'] = 2
      self.assertRaises(dkim.ValidationError, dkim.validate_signature_fields, sigVer)
      # try with x
      sigX = sig.copy()
      sigX[b'x'] = b'1399525798'
      dkim.validate_signature_fields(sig)
      # try with late t
      sigX[b't'] = b'1400000000'
      self.assertRaises(dkim.ValidationError, dkim.validate_signature_fields, sigX)
      # try without t
      now = int(time.time())
      sigX[b'x'] = str(now+400000).encode('ascii')
      dkim.validate_signature_fields(sigX)
      # try when expired a day ago
      sigX[b'x'] = str(now - 24*3600).encode('ascii')
      self.assertRaises(dkim.ValidationError, dkim.validate_signature_fields, sigX)


def test_suite():
    from unittest import TestLoader
    return TestLoader().loadTestsFromName(__name__)
