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
k=rsa; s=email;\
p=MFwwDQYJKoZIhvcNAQEBBQADSwAwSAJBANmBe10IgY+u7h3enWTukkqtUD5PR52T\
b/mPfjC0QJTocVBq6Za/PlzfV+Py92VaCak19F4WrbVTK5Gg5tW220MCAwEAAQ=="""

        _dns_responses = {
          'example._domainkey.canonical.com.': sample_dns,
          'test._domainkey.example.com.': read_test_data("test_tlsrpt.txt"),
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




    def test_ignores_tlsrptsvc(self):
        # A non-tlsrpt signed with a key record with s=tlsrpt shouldn't verify.
        for header_algo in (b"simple", b"relaxed"):
            for body_algo in (b"simple", b"relaxed"):
                sig = dkim.sign(
                    self.message, b"test", b"example.com", self.key,
                    canonicalize=(header_algo, body_algo))
                res = dkim.verify(sig + self.message, dnsfunc=self.dnsfunc6)
                self.assertFalse(res)

    def test_tlsrpt_with_strict_tlsrptsvc(self):
        # A tlsrpt signed with a key record with s=tlsrpt should verify with tlsrpt='strict'.
        for header_algo in (b"simple", b"relaxed"):
            for body_algo in (b"simple", b"relaxed"):
                sig = dkim.sign(
                    self.message, b"test", b"example.com", self.key,
                    canonicalize=(header_algo, body_algo))
                res = dkim.verify(sig + self.message, dnsfunc=self.dnsfunc6, tlsrpt='strict')
                self.assertTrue(res)

    def test_tlsrpt_with_tlsrptsvc(self):
        # A tlsrpt signed with a key record with s=tlsrpt should verify.
        for header_algo in (b"simple", b"relaxed"):
            for body_algo in (b"simple", b"relaxed"):
                sig = dkim.sign(
                    self.message, b"test", b"example.com", self.key,
                    canonicalize=(header_algo, body_algo))
                res = dkim.verify(sig + self.message, dnsfunc=self.dnsfunc6, tlsrpt=True)
                self.assertTrue(res)

    def test_tlsrpt_with_strict_no_tlsrptsvc(self):
        # A tlsrpt signed with a key record without s=tlsrpt not tlsrpt='strict' should not verify.
        for header_algo in (b"simple", b"relaxed"):
            for body_algo in (b"simple", b"relaxed"):
                sig = dkim.sign(
                    self.message, b"test", b"example.com", self.key,
                    canonicalize=(header_algo, body_algo))
                res = dkim.verify(sig + self.message, dnsfunc=self.dnsfunc, tlsrpt='strict')
                self.assertFalse(res)

    def test_tlsrpt_with_no_tlsrptsvc(self):
        # A tlsrpt signed with a key record without s=tlsrpt and tlsrpt=True should verify.
        for header_algo in (b"simple", b"relaxed"):
            for body_algo in (b"simple", b"relaxed"):
                sig = dkim.sign(
                    self.message, b"test", b"example.com", self.key,
                    canonicalize=(header_algo, body_algo))
                res = dkim.verify(sig + self.message, dnsfunc=self.dnsfunc, tlsrpt=True)
                self.assertTrue(res)

    def test_tlsrpt_ignore_l_verify(self):
        # For a tlsrpt, ignore l= on verify
        for header_algo in (b"simple", b"relaxed"):
            for body_algo in (b"simple", b"relaxed"):
                sig = dkim.sign(
                    self.message, b"test", b"example.com", self.key,
                    canonicalize=(header_algo, body_algo), length=True)
                self.message += b'added more text'
                res = dkim.verify(sig + self.message, dnsfunc=self.dnsfunc, tlsrpt=True)
                self.assertFalse(res)

    def test_tlsrpt_ignore_l_sign(self):
        # For a tlsrpt, don't add l= when signing tlsrpt
        for header_algo in (b"simple", b"relaxed"):
            for body_algo in (b"simple", b"relaxed"):
                sig = dkim.sign(
                    self.message, b"test", b"example.com", self.key,
                    canonicalize=(header_algo, body_algo), length=True, tlsrpt=True)
                self.message += b'added more text'
                res = dkim.verify(sig + self.message, dnsfunc=self.dnsfunc)
                self.assertFalse(res)


def test_suite():
    from unittest import TestLoader
    return TestLoader().loadTestsFromName(__name__)
