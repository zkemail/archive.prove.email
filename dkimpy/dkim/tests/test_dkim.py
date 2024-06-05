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

    def test_linesep(self):
        self.assertEqual(
            b"foo" * 24 + b"\n foo", dkim.fold(b"foo" * 25, linesep=b"\n"))



class TestSignAndVerify(unittest.TestCase):
    """End-to-end signature and verification tests."""

    def setUp(self):
        self.message = read_test_data("test.message")
        self.message3 = read_test_data("rfc6376.msg")
        self.message4 = read_test_data("rfc6376.signed.msg")
        self.message5 = read_test_data("rfc6376.signed.rsa.msg")
        self.message6 = read_test_data("test.message.baddomain")
        self.message7 = read_test_data("rfc6376.w1258.msg")
        self.key = read_test_data("test.private")
        self.rfckey = read_test_data("rfc8032_7_1.key")

    def dnsfunc(self, domain, timeout=5):
        sample_dns = """\
k=rsa; s=email;\
p=MFwwDQYJKoZIhvcNAQEBBQADSwAwSAJBANmBe10IgY+u7h3enWTukkqtUD5PR52T\
b/mPfjC0QJTocVBq6Za/PlzfV+Py92VaCak19F4WrbVTK5Gg5tW220MCAwEAAQ=="""

        _dns_responses = {
          'example._domainkey.canonical.com.': sample_dns,
          'test._domainkey.example.com.': read_test_data("test.txt"),
          '20120113._domainkey.gmail.com.': """k=rsa; \
p=MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA1Kd87/UeJjenpabgbFwh\
+eBCsSTrqmwIYYvywlbhbqoo2DymndFkbjOVIPIldNs/m40KF+yzMn1skyoxcTUGCQ\
s8g3FgD2Ap3ZB5DekAo5wMmk4wimDO+U8QzI3SD07y2+07wlNWwIt8svnxgdxGkVbb\
hzY8i+RQ9DpSVpPbF7ykQxtKXkv/ahW3KjViiAH+ghvvIhkx4xYSIc9oSwVmAl5Oct\
MEeWUwg8Istjqz8BZeTWbf41fbNhte7Y+YqZOwq1Sd0DbvYAD9NOZK9vlfuac0598H\
Y+vtSBczUiKERHv1yRbcaQtZFh5wtiRrN04BLUTD21MycBX5jYchHjPY/wIDAQAB"""
        }
        try:
            domain = domain.decode('ascii')
        except UnicodeDecodeError:
            return None
        self.assertTrue(domain in _dns_responses,domain)
        return _dns_responses[domain]

    def dnsfunc2(self, domain, timeout=5):
        sample_dns = """\
k=rsa; \
p=MFwwDQYJKoZIhvcNAQEBBQADSwAwSAJBANmBe10IgY+u7h3enWTukkqtUD5PR52T\
b/mPfjC0QJTocVBq6Za/PlzfV+Py92VaCak19F4WrbVTK5Gg5tW220MCAwEAAQ=="""

        _dns_responses = {
          'example._domainkey.canonical.com.': sample_dns,
          'test._domainkey.example.com.': read_test_data("test2.txt"),
          '20120113._domainkey.gmail.com.': """\
p=MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA1Kd87/UeJjenpabgbFwh\
+eBCsSTrqmwIYYvywlbhbqoo2DymndFkbjOVIPIldNs/m40KF+yzMn1skyoxcTUGCQ\
s8g3FgD2Ap3ZB5DekAo5wMmk4wimDO+U8QzI3SD07y2+07wlNWwIt8svnxgdxGkVbb\
hzY8i+RQ9DpSVpPbF7ykQxtKXkv/ahW3KjViiAH+ghvvIhkx4xYSIc9oSwVmAl5Oct\
MEeWUwg8Istjqz8BZeTWbf41fbNhte7Y+YqZOwq1Sd0DbvYAD9NOZK9vlfuac0598H\
Y+vtSBczUiKERHv1yRbcaQtZFh5wtiRrN04BLUTD21MycBX5jYchHjPY/wIDAQAB"""
        }
        try:
            domain = domain.decode('ascii')
        except UnicodeDecodeError:
            return None
        self.assertTrue(domain in _dns_responses,domain)
        return _dns_responses[domain]

    def dnsfunc3(self, domain, timeout=5):
        sample_dns = """\
k=rsa; \
p=MFwwDQYJKoZIhvcNAQEBBQADSwAwSAJBANmBe10IgY+u7h3enWTukkqtUD5PR52T\
b/mPfjC0QJTocVBq6Za/PlzfV+Py92VaCak19F4WrbVTK5Gg5tW220MCAwEAAQ=="""

        _dns_responses = {
          'example._domainkey.canonical.com.': sample_dns,
          'test._domainkey.example.com.': read_test_data("badversion.txt"),
          '20120113._domainkey.gmail.com.': """\
p=MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA1Kd87/UeJjenpabgbFwh\
+eBCsSTrqmwIYYvywlbhbqoo2DymndFkbjOVIPIldNs/m40KF+yzMn1skyoxcTUGCQ\
s8g3FgD2Ap3ZB5DekAo5wMmk4wimDO+U8QzI3SD07y2+07wlNWwIt8svnxgdxGkVbb\
hzY8i+RQ9DpSVpPbF7ykQxtKXkv/ahW3KjViiAH+ghvvIhkx4xYSIc9oSwVmAl5Oct\
MEeWUwg8Istjqz8BZeTWbf41fbNhte7Y+YqZOwq1Sd0DbvYAD9NOZK9vlfuac0598H\
Y+vtSBczUiKERHv1yRbcaQtZFh5wtiRrN04BLUTD21MycBX5jYchHjPY/wIDAQAB"""
        }
        try:
            domain = domain.decode('ascii')
        except UnicodeDecodeError:
            return None
        self.assertTrue(domain in _dns_responses,domain)
        return _dns_responses[domain]

    def dnsfunc4(self, domain, timeout=5):
        sample_dns = """\
k=rsa; \
p=MFwwDQYJKoZIhvcNAQEBBQADSwAwSAJBANmBe10IgY+u7h3enWTukkqtUD5PR52T\
b/mPfjC0QJTocVBq6Za/PlzfV+Py92VaCak19F4WrbVTK5Gg5tW220MCAwEAAQ=="""

        _dns_responses = {
          'example._domainkey.canonical.com.': sample_dns,
          'test._domainkey.example.com.': read_test_data("badk.txt"),
          '20120113._domainkey.gmail.com.': """\
p=MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA1Kd87/UeJjenpabgbFwh\
+eBCsSTrqmwIYYvywlbhbqoo2DymndFkbjOVIPIldNs/m40KF+yzMn1skyoxcTUGCQ\
s8g3FgD2Ap3ZB5DekAo5wMmk4wimDO+U8QzI3SD07y2+07wlNWwIt8svnxgdxGkVbb\
hzY8i+RQ9DpSVpPbF7ykQxtKXkv/ahW3KjViiAH+ghvvIhkx4xYSIc9oSwVmAl5Oct\
MEeWUwg8Istjqz8BZeTWbf41fbNhte7Y+YqZOwq1Sd0DbvYAD9NOZK9vlfuac0598H\
Y+vtSBczUiKERHv1yRbcaQtZFh5wtiRrN04BLUTD21MycBX5jYchHjPY/wIDAQAB"""
        }
        try:
            domain = domain.decode('ascii')
        except UnicodeDecodeError:
            return None
        self.assertTrue(domain in _dns_responses,domain)
        return _dns_responses[domain]

    def dnsfunc5(self, domain, timeout=5):
        sample_dns = """\
k=rsa; \
p=MFwwDQYJKoZIhvcNAQEBBQADSwAwSAJBANmBe10IgY+u7h3enWTukkqtUD5PR52T\
b/mPfjC0QJTocVBq6Za/PlzfV+Py92VaCak19F4WrbVTK5Gg5tW220MCAwEAAQ=="""

        _dns_responses = {
          'example._domainkey.canonical.com.': sample_dns,
          'test._domainkey.football.example.com.': read_test_data("test.txt"),
          'brisbane._domainkey.football.example.com.': """v=DKIM1; k=ed25519; \
p=11qYAYKxCrfVS/7TyWQHOg7hcvPapiMlrwIaaPcHURo="""
        }
        try:
            domain = domain.decode('ascii')
        except UnicodeDecodeError:
            return None
        self.assertTrue(domain in _dns_responses,domain)
        return _dns_responses[domain]

    def dnsfunc6(self, domain, timeout=5):
        sample_dns = """\
k=rsa; \
p=MFwwDQYJKoZIhvNAQEBBQADSwAwSAJBANmBe10IgY+u7h3enWTukkqtUD5PR52T\
b/mPfjC0QJTocVBq6Za/PlzfV+Py92VaCak19F4WrbVTK5Gg5tW220MCAwEAAQ=="""

        _dns_responses = {
          'test._domainkey.football.example.com.': sample_dns,
          'brisbane._domainkey.football.example.com.': """v=DKIM1; k=ed25519; \
p=11qYAYKxCrfVS/7TyWQHOg7hcvPapiMlrwIaaPcHURo="""
        }
        try:
            domain = domain.decode('ascii')
        except UnicodeDecodeError:
            return None
        self.assertTrue(domain in _dns_responses,domain)
        return _dns_responses[domain]

    def dnsfunc7(self, domain, timeout=5):
        sample_dns = """\
k=rsa; s=email;\
p=MFwwDQYJKoZIhvcNAQEBBQADSwAwSAJBANmBe10IgY+u7h3enWTukkqtUD5PR52T\
b/mPfjC0QJTocVBq6Za/PlzfV+Py92VaCak19F4WrbVTK5Gg5tW220MCAwEAAQ=="""

        _dns_responses = {
          'test._domainkey.legitimate.com(.attacker.com.': read_test_data("test.txt"),
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
                    self.message, b"test", b"example.com", self.key,
                    canonicalize=(header_algo, body_algo))
                res = dkim.verify(sig + self.message, dnsfunc=self.dnsfunc)
                self.assertTrue(res)

    def test_verifies_nosig(self):
        # A message without signature does not verify.
        res = dkim.verify(self.message, dnsfunc=self.dnsfunc)
        self.assertFalse(res)

    def test_double_verifies(self):
        # A message also containing a ed25519 signature verifies after being signed with rsa.
        for header_algo in (b"simple", b"relaxed"):
            for body_algo in (b"simple", b"relaxed"):
                sig = dkim.sign(
                    self.message3, b"test", b"football.example.com", self.key,
                    canonicalize=(header_algo, body_algo), signature_algorithm=b'rsa-sha256')
                res = dkim.verify(sig + self.message3, dnsfunc=self.dnsfunc5)
                self.assertTrue(res)

    def test_double_previous_verifies(self):
        # A message previously signed using both rsa and ed25519 verifies after being signed.
        for header_algo in (b"simple", b"relaxed"):
            for body_algo in (b"simple", b"relaxed"):
                sig = dkim.sign(
                    self.message3, b"test", b"football.example.com", self.key,
                    canonicalize=(header_algo, body_algo), signature_algorithm=b'rsa-sha256')
                d = dkim.DKIM(self.message4)
                res = d.verify(dnsfunc=self.dnsfunc5)
                self.assertTrue(res)
    def test_non_utf8(self):
        # A message with Windows-1258 encoding is signed and verifies.
        for header_algo in (b"simple", b"relaxed"):
            for body_algo in (b"simple", b"relaxed"):
                sig = dkim.sign(
                    self.message7, b"test", b"football.example.com", self.key,
                    canonicalize=(header_algo, body_algo), signature_algorithm=b'rsa-sha256')
                d = dkim.DKIM(self.message7)
                res = d.verify(dnsfunc=self.dnsfunc5)
                # As of 1.1.0 this won't verify, but at least we don't crash.  FIXME
                self.assertFalse(res)

    def test_catch_bad_key(self):
        # Raise correct error for defective public key.
        d = dkim.DKIM(self.message5)
        res = d.verify(dnsfunc=self.dnsfunc6)
        self.assertFalse(res)

    def test_verifies_lflinesep(self):
        # A message verifies after being signed.
        for header_algo in (b"simple", b"relaxed"):
            for body_algo in (b"simple", b"relaxed"):
                sig = dkim.sign(
                    self.message, b"test", b"example.com", self.key,
                    canonicalize=(header_algo, body_algo), linesep=b"\n")
                res = dkim.verify(sig + self.message, dnsfunc=self.dnsfunc)
                self.assertFalse(b'\r\n' in sig)
                self.assertTrue(res)

    def test_implicit_k(self):
        # A message verifies after being signed when k= tag is not provided.
        for header_algo in (b"simple", b"relaxed"):
            for body_algo in (b"simple", b"relaxed"):
                sig = dkim.sign(
                    self.message, b"test", b"example.com", self.key,
                    canonicalize=(header_algo, body_algo))
                res = dkim.verify(sig + self.message, dnsfunc=self.dnsfunc2)
                self.assertTrue(res)

    def test_bad_version(self):
        # A error is detected if a bad version is used.
        for header_algo in (b"simple", b"relaxed"):
            for body_algo in (b"simple", b"relaxed"):
                sig = dkim.sign(
                    self.message, b"test", b"example.com", self.key,
                    canonicalize=(header_algo, body_algo))
                res = dkim.verify(sig + self.message, dnsfunc=self.dnsfunc3)
                self.assertFalse(res)

    def test_unknown_k(self):
        # A error is detected if an unknown algorithm is in the k= tag.
        for header_algo in (b"simple", b"relaxed"):
            for body_algo in (b"simple", b"relaxed"):
                sig = dkim.sign(
                    self.message, b"test", b"example.com", self.key,
                    canonicalize=(header_algo, body_algo))
                res = dkim.verify(sig + self.message, dnsfunc=self.dnsfunc4)
                self.assertFalse(res)

    def test_invalid_domain_sign(self):
        # RFC6376 says domain can be Alpha, Num, - only.
        sig = dkim.sign(
            self.message, b"test", b"legitimate.com(.attacker.com", self.key)
        res = dkim.verify(sig + self.message, dnsfunc=self.dnsfunc7)
        self.assertFalse(res)

    def test_invalid_domain_verify(self):
        # RFC6376 says domain can be Alpha, Num, - only.
        res = dkim.verify(self.message6, dnsfunc=self.dnsfunc7)
        self.assertFalse(res)

    def test_simple_signature(self):
        # A message verifies after being signed with SHOULD headers
        for header_algo in (b"simple", b"relaxed"):
             for body_algo in (b"simple", b"relaxed"):
                sig = dkim.sign(
                    self.message, b"test", b"example.com", self.key,
                    canonicalize=(header_algo, body_algo),
                    include_headers=(b'from',) + dkim.DKIM.SHOULD)
                res = dkim.verify(sig + self.message, dnsfunc=self.dnsfunc)
                self.assertTrue(res)

    def test_string_include(self):
        # A message can be signed when the include_headers is string
        for header_algo in (b"simple", b"relaxed"):
             for body_algo in (b"simple", b"relaxed"):
                sig = dkim.sign(
                    self.message, b"test", b"example.com", self.key,
                    canonicalize=(header_algo, body_algo),
                    include_headers=('from',) )
                res = dkim.verify(sig + self.message, dnsfunc=self.dnsfunc)
                self.assertTrue(res)

    def test_add_body_length(self):
        sig = dkim.sign(
            self.message, b"test", b"example.com", self.key, length=True)
        msg = email.message_from_string(self.message.decode('utf-8'))
        self.assertIn('; l=%s' % len(msg.get_payload() + '\n'), sig.decode('utf-8'))
        res = dkim.verify(sig + self.message, dnsfunc=self.dnsfunc)
        self.assertTrue(res)

    def test_altered_body_fails(self):
        # An altered body fails verification.
        for header_algo in (b"simple", b"relaxed"):
            for body_algo in (b"simple", b"relaxed"):
                sig = dkim.sign(
                    self.message, b"test", b"example.com", self.key)
                res = dkim.verify(
                    sig + self.message + b"foo", dnsfunc=self.dnsfunc)
                self.assertFalse(res)

    def test_l_verify(self):
        # Sign with l=, add text, should verify
        for header_algo in (b"simple", b"relaxed"):
            for body_algo in (b"simple", b"relaxed"):
                sig = dkim.sign(
                    self.message, b"test", b"example.com", self.key,
                    canonicalize=(header_algo, body_algo), length=True)
                self.message += b'added more text\n'
                res = dkim.verify(sig + self.message, dnsfunc=self.dnsfunc)
                self.assertTrue(res)

    def test_present(self):
        # Test DKIM.present().
        d = dkim.DKIM(self.message,signature_algorithm=b'rsa-sha256')
        present = d.present()
        self.assertFalse(present)
        sig = d.sign(b"test", b"example.com", self.key)
        signed = sig + self.message
        d2 = dkim.DKIM(signed)
        present = d2.present()
        self.assertTrue(present)

    def test_badly_encoded_domain_fails(self):
        # Domains should be ASCII. Bad ASCII causes verification to fail.
        sig = dkim.sign(self.message, b"test", b"example.com\xe9", self.key)
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
To: scottk@example.com
Subject: this is my
    test message
""".replace(b'\n', b'\r\n')

      sample_privkey = b"""\
-----BEGIN RSA PRIVATE KEY-----
MIIBOwIBAAJBANmBe10IgY+u7h3enWTukkqtUD5PR52Tb/mPfjC0QJTocVBq6Za/
PlzfV+Py92VaCak19F4WrbVTK5Gg5tW220MCAwEAAQJAYFUKsD+uMlcFu1D3YNaR
EGYGXjJ6w32jYGJ/P072M3yWOq2S1dvDthI3nRT8MFjZ1wHDAYHrSpfDNJ3v2fvZ
cQIhAPgRPmVYn+TGd59asiqG1SZqh+p+CRYHW7B8BsicG5t3AiEA4HYNOohlgWan
8tKgqLJgUdPFbaHZO1nDyBgvV8hvWZUCIQDDdCq6hYKuKeYUy8w3j7cgJq3ih922
2qNWwdJCfCWQbwIgTY0cBvQnNe0067WQIpj2pG7pkHZR6qqZ9SE+AjNTHX0CIQCI
Mgq55Y9MCq5wqzy141rnxrJxTwK9ABo3IAFMWEov3g==
-----END RSA PRIVATE KEY-----
"""

      sample_pubkey = """\
-----BEGIN PUBLIC KEY-----
MFwwDQYJKoZIhvcNAQEBBQADSwAwSAJBANmBe10IgY+u7h3enWTukkqtUD5PR52T
b/mPfjC0QJTocVBq6Za/PlzfV+Py92VaCak19F4WrbVTK5Gg5tW220MCAwEAAQ==
-----END PUBLIC KEY-----
"""

      for header_mode in [dkim.Relaxed, dkim.Simple]:

        dkim_header = dkim.sign(sample_msg, b'example', b'canonical.com',
            sample_privkey, canonicalize=(header_mode, dkim.Relaxed))
        # Folding dkim_header affects b= tag only, since dkim.sign folds
        # sig_value with empty b= before hashing, and then appends the
        # signature.  So folding dkim_header again adds FWS to
        # the b= tag only.  This should be ignored even with
        # simple canonicalization.
        # http://tools.ietf.org/html/rfc4871#section-3.5
        signed = dkim.fold(dkim_header) + sample_msg
        result = dkim.verify(signed,dnsfunc=self.dnsfunc,
                minkey=512)
        self.assertTrue(result)
        dkim_header = dkim.fold(dkim_header)
        # use a tab for last fold to test tab in FWS bug
        pos = dkim_header.rindex(b'\r\n ')
        dkim_header = dkim_header[:pos]+b'\r\n\t'+dkim_header[pos+3:]
        result = dkim.verify(dkim_header + sample_msg,
                dnsfunc=self.dnsfunc, minkey=512)
        self.assertTrue(result)

    def test_degenerate_folding(self):
        # <http://bugs.debian.org/cgi-bin/bugreport.cgi?bug=711751>
        # degenerate folding is ugly but legal
        message = read_test_data("test2.message")
        dv = dkim.DKIM(message)
        res = dv.verify(dnsfunc=self.dnsfunc)
        self.assertTrue(res)

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
                sig = d.sign(b"test", b"example.com", self.key,
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
                    self.message, b"test", b"example.com", self.key)
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
        domain = 'example.com'
        identity = None
        try:
            sig = dkim.sign(message, selector, domain, read_test_data('test.private'), identity = identity)
        except dkim.ParameterError as x:
            sigerror = True
        self.assertTrue(sigerror)

    def test_validate_signature_fields(self):
      sig = {b'v': b'1',
      b'a': b'rsa-sha256',
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
