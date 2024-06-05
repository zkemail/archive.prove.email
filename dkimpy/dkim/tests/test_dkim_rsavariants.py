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


class TestSignAndVerify(unittest.TestCase):
    """End-to-end signature and verification tests."""

    def setUp(self):
        self.message = read_test_data("test.message")
        self.key1024 = read_test_data("1024_testkey.key")
        self.key2048 = read_test_data("2048_testkey.key")
        self.key2048PKCS8 = read_test_data("2048_testkey_PKCS8.key")

    def dnsfunc(self, domain, timeout=5):
        _dns_responses = {
          'test._domainkey.example.com.': read_test_data("1024_testkey_wo_markers.pub.txt"),
          'test2._domainkey.example.com.': read_test_data("1024_testkey_wo_markers.pub.rsa.txt"),
          'test3._domainkey.example.com.': read_test_data("2048_testkey_wo_markers.pub.txt"),
          'test4._domainkey.example.com.': read_test_data("2048_testkey_wo_markers.pub.rsa.txt"),
          'test5._domainkey.example.com.': read_test_data("2048_testkey_PKCS8.key.pub.txt")
        }
        try:
            domain = domain.decode('ascii')
        except UnicodeDecodeError:
            return None
        self.assertTrue(domain in _dns_responses,domain)
        return _dns_responses[domain]

    def test_verifies_SubjectPublicKeyInfo1024(self):
        # A message verifies after being signed.
        for header_algo in (b"simple", b"relaxed"):
            for body_algo in (b"simple", b"relaxed"):
                sig = dkim.sign(
                    self.message, b"test", b"example.com", self.key1024,
                    canonicalize=(header_algo, body_algo))
                res = dkim.verify(sig + self.message, dnsfunc=self.dnsfunc)
                self.assertTrue(res)

    def test_verifies_RSAPublicKey1024(self):
        # A message verifies after being signed.
        for header_algo in (b"simple", b"relaxed"):
            for body_algo in (b"simple", b"relaxed"):
                sig = dkim.sign(
                    self.message, b"test2", b"example.com", self.key1024,
                    canonicalize=(header_algo, body_algo))
                res = dkim.verify(sig + self.message, dnsfunc=self.dnsfunc)
                self.assertTrue(res)


    def test_verifiesSubjectPublicKeyInfo2048(self):
        # A message verifies after being signed.
        for header_algo in (b"simple", b"relaxed"):
            for body_algo in (b"simple", b"relaxed"):
                sig = dkim.sign(
                    self.message, b"test3", b"example.com", self.key2048,
                    canonicalize=(header_algo, body_algo))
                res = dkim.verify(sig + self.message, dnsfunc=self.dnsfunc)
                self.assertTrue(res)


    def test_verifiesRSAPublicKey2048(self):
        # A message verifies after being signed.
        for header_algo in (b"simple", b"relaxed"):
            for body_algo in (b"simple", b"relaxed"):
                sig = dkim.sign(
                    self.message, b"test4", b"example.com", self.key2048,
                    canonicalize=(header_algo, body_algo))
                res = dkim.verify(sig + self.message, dnsfunc=self.dnsfunc)
                self.assertTrue(res)


    def test_verifies_RSAPublicKey2048PKCS8(self):
        #A message verifies after being signed (with PKCS8 private key)
        for header_algo in (b"simple", b"relaxed"):
            for body_algo in (b"simple", b"relaxed"):
                sig = dkim.sign(
                    self.message, b"test5", b"example.com", self.key2048PKCS8,
                    canonicalize=(header_algo, body_algo))
                res = dkim.verify(sig + self.message, dnsfunc=self.dnsfunc)
                self.assertTrue(res)

def test_suite():
    from unittest import TestLoader
    return TestLoader().loadTestsFromName(__name__)
