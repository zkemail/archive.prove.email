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
#
# This has been modified from the original software.
# Copyright (c) 2016 Google, Inc.
# Contact: Brandon Long <blong@google.com>

import os.path
import unittest
import time

import dkim


def read_test_data(filename):
    """Get the content of the given test data file.
    """
    path = os.path.join(os.path.dirname(__file__), 'data', filename)
    with open(path, 'rb') as f:
        return f.read()


class TestSignAndVerify(unittest.TestCase):
    """End-to-end signature and verification tests."""

    def setUp(self):
        self.message = read_test_data("test.message")
        self.key = read_test_data("test.private")

    def dnsfunc(self, domain, timeout=5):
        sample_dns = """\
k=rsa; \
p=MFwwDQYJKoZIhvcNAQEBBQADSwAwSAJBANmBe10IgY+u7h3enWTukkqtUD5PR52T\
b/mPfjC0QJTocVBq6Za/PlzfV+Py92VaCak19F4WrbVTK5Gg5tW220MCAwEAAQ=="""

        _dns_responses = {
          'example._domainkey.canonical.com.': sample_dns,
          'test._domainkey.example.com.': read_test_data("test.txt"),
          # dnsfunc returns empty if no txt record
          'missing._domainkey.example.com.': '',
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

    def test_signs_and_verifies(self):
        # A message verifies after being signed
        self.maxDiff = None
        sig_lines = dkim.arc_sign(
            self.message, b"test", b"example.com", self.key, b"lists.example.org", timestamp="12345")

        expected_sig = [b'ARC-Seal: i=1; cv=none; a=rsa-sha256; d=example.com; s=test; t=12345;\r\n b=MBw2+L1/4PuYWJlt1tZlDtbOvyfbyH2t2N6DinFV/BIaB2LqbDKTYjXXk9HuuK1/qEkTd\r\n TxCYScIrtVO7pFbGiSawMuLatVzHNCqTURa1zBTXr2mKW1hgdmrtMMUcMVCYxr1AJpu6IYX\r\n VMIoOAn7tIDdO0VLokK6FnIXTWEAplQ=\r\n', b'ARC-Message-Signature: i=1; a=rsa-sha256; c=relaxed/relaxed;\r\n d=example.com; s=test; t=12345; h=message-id : date : from : to :\r\n subject : from; bh=wE7NXSkgnx9PGiavN4OZhJztvkqPDlemV3OGuEnLwNo=;\r\n b=a0f6qc3k9eECTSR155A0TQS+LjqPFWfI/brQBA83EUz00SNxj1wmWykvs1hhBVeM0r1kE\r\n Qc6CKbzRYaBNSiFj4q8JBpRIujLz1qLyGmPuAI6ddu/Z/1hQxgpVcp/odmI1UMV2R+d+yQ7\r\n tUp3EQxF/GYNt22rV4rNmDmANZVqJ90=\r\n', b'ARC-Authentication-Results: i=1; lists.example.org; arc=none;\r\n  spf=pass smtp.mfrom=jqd@d1.example;\r\n  dkim=pass (1024-bit key) header.i=@d1.example;\r\n  dmarc=pass\r\n']
        self.assertEqual(expected_sig, sig_lines)

        (cv, res, reason) = dkim.arc_verify(b''.join(sig_lines) + self.message, dnsfunc=self.dnsfunc)
        self.assertEqual(cv, dkim.CV_Pass)

    def test_fails_h_in_as(self):
        # ARC 4.1.3, h= not allowed in AS
        self.maxDiff = None
        sig_lines = [b'ARC-Seal: i=1; cv=none; a=rsa-sha256; d=example.com; s=test; t=12345;\r\n h=message-id : date : from : to : subject : from;\r\n b=mIurIuLl0/wAxWhA4DBS1wsUE15IBnmJ7o3sH15hIuesdD4smz1cCLXVhRtxQE\r\n rVtVLv4OgNCgdFsB5zbSOUao2bSSYP6y0BGyCWvr+hU4tai5axIc1Kfwbtv/0Mqg\r\n waiGJPreOAAeZOJ4vPfdaAbSXlN5MI4PHW89U82FSIBKI=\r\n', b'ARC-Message-Signature: i=1; a=rsa-sha256; c=relaxed/relaxed;\r\n d=example.com; s=test; t=12345; h=message-id :\r\n date : from : to : subject : from;\r\n bh=wE7NXSkgnx9PGiavN4OZhJztvkqPDlemV3OGuEnLwNo=;\r\n b=a0f6qc3k9eECTSR155A0TQS+LjqPFWfI/brQBA83EUz00SNxj\r\n 1wmWykvs1hhBVeM0r1kEQc6CKbzRYaBNSiFj4q8JBpRIujLz1qL\r\n yGmPuAI6ddu/Z/1hQxgpVcp/odmI1UMV2R+d+yQ7tUp3EQxF/GY\r\n Nt22rV4rNmDmANZVqJ90=\r\n', b'ARC-Authentication-Results: i=1; lists.example.org; arc=none;\r\n  spf=pass smtp.mfrom=jqd@d1.example;\r\n  dkim=pass (1024-bit key) header.i=@d1.example;\r\n  dmarc=pass\r\n']

        (cv, res, reason) = dkim.arc_verify(b''.join(sig_lines) + self.message, dnsfunc=self.dnsfunc)
        self.assertEqual(cv, dkim.CV_Fail)



def test_suite():
    from unittest import TestLoader
    return TestLoader().loadTestsFromName(__name__)
