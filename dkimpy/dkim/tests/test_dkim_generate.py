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
# Copyright (c) 2022 Adrien Precigout <dev@asdrip.fr>

import os.path
import tempfile
import unittest

import dkim
import dkim.dknewkey as dknewkey

def read_data(path):
    """Get the content of the given test data file."""

    with open(path, 'rb') as f:
        return f.read()


class TestSignAndVerify(unittest.TestCase):
    """End-to-end signature and verification tests with a generated key."""

    def setUp(self):
        message_dir = os.path.join(os.path.dirname(__file__), 'data', "test.message")
        self.message = read_data(message_dir)
        self.ed25519_dns_key_file = ""
        self.rsa_dns_key_file = ""
    

    def test_generate_verifies_new_RSA_key(self):
        #Create temporary dir
        tmpdir = tempfile.TemporaryDirectory()
        keydir = tmpdir.name
        rsa_key_file = os.path.join(keydir, "dkim.rsa.key")
        self.rsa_dns_key_file = os.path.join(keydir, "dkim.rsa.key.pub.txt")
        #Generate a rsa key
        dknewkey.GenRSAKeys(rsa_key_file, False)
        dknewkey.ExtractRSADnsPublicKey(rsa_key_file, self.rsa_dns_key_file, False)
        #Load the key
        rsakey = read_data(rsa_key_file)
        #Test signature with the newely generated key  
        for header_algo in (b"simple", b"relaxed"):
            for body_algo in (b"simple", b"relaxed"):
                sig = dkim.sign(
                    self.message, b"test", b"example.com", rsakey,
                    canonicalize=(header_algo, body_algo))
                res = dkim.verify(sig + self.message, dnsfunc=self.dnsfuncRSA)
                self.assertTrue(res)
        tmpdir.cleanup()


    def test_generate_verifies_Ed25519_key(self):
        #Create temporary dir
        tmpdir = tempfile.TemporaryDirectory()
        keydir = tmpdir.name
        ed25519_key_file = os.path.join(keydir, "dkim.ed25519.key")
        self.ed25519_dns_key_file = os.path.join(keydir, "dkim.ed25519.key.pub.txt")
        #Generate a ed25519 key
        pkt = dknewkey.GenEd25519Keys(ed25519_key_file, False)
        dknewkey.ExtractEd25519PublicKey(self.ed25519_dns_key_file, pkt, False)
        #Load the key
        ed25519key = read_data(ed25519_key_file)
        #Test signature with the newely generated key 
        for header_algo in (b"simple", b"relaxed"):
            for body_algo in (b"simple", b"relaxed"):
                sig = dkim.sign(
                    self.message, b"test1", b"example.com", ed25519key,
                    signature_algorithm=b'ed25519-sha256',
                    canonicalize=(header_algo, body_algo))
                res = dkim.verify(sig + self.message, dnsfunc=self.dnsfuncED25519)
                self.assertTrue(res)
        tmpdir.cleanup()


    def dnsfuncRSA(self, domain, timeout=5):
        _dns_responses = {
            'test._domainkey.example.com.': read_data(self.rsa_dns_key_file),
        }
        try:
            domain = domain.decode('ascii')
        except UnicodeDecodeError:
            return None
        self.assertTrue(domain in _dns_responses,domain)
        return _dns_responses[domain]

    def dnsfuncED25519(self, domain, timeout=5):
        _dns_responses = {
            'test1._domainkey.example.com.': read_data(self.ed25519_dns_key_file),
        }
        try:
            domain = domain.decode('ascii')
        except UnicodeDecodeError:
            return None
        self.assertTrue(domain in _dns_responses,domain)
        return _dns_responses[domain]

   

def test_suite():
    from unittest import TestLoader
    return TestLoader().loadTestsFromName(__name__)
