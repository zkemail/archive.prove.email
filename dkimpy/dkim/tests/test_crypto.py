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

import base64
import binascii
import hashlib
import unittest

from dkim.crypto import (
    DigestTooLargeError,
    UnparsableKeyError,
    EMSA_PKCS1_v1_5_encode,
    int2str,
    parse_pem_private_key,
    parse_public_key,
    RSASSA_PKCS1_v1_5_sign,
    RSASSA_PKCS1_v1_5_verify,
    str2int,
    )
from dkim.tests.test_dkim import read_test_data
from dkim.util import parse_tag_value


# These are extracted from dkim/tests/data/test.private.
TEST_KEY_MODULUS = int(
    '160190232090260054474895273563294777865179886824815261110923286158270437'
    '657769966074370477716411064825849317279563494735400250019233722215662302'
    '997403060159149904218292658425241195497467863155064737257198115261596066'
    '733086923624062366294295557722551666415445482671442053150678674937682352'
    '837105556539434741981')
TEST_KEY_PUBLIC_EXPONENT = 65537
TEST_KEY_PRIVATE_EXPONENT = int(
    '219642251791061057038224045690185219631125389170665415924249912174530136'
    '074693824121380763959239792563755125360354847443780863736947713174228520'
    '489900956461640273471526152019568303807247290486052565153701534491987040'
    '131529720476525111651818771481293273124837542067061293644354088836358900'
    '29771161475005043329')
TEST_KEY_PRIME1 = int(
    '127343333492908149956322715568115237787784712176275919666517073343689103'
    '280591709737233188193431204382936008602497360201661766158158969883295914'
    '16266272177')
TEST_KEY_PRIME2 = int(
    '125793967926229270607412639516115399484604596465353856808629588968254772'
    '302339293254103556785310783521521266982500068526354237606773478050287350'
    '33316975853')
TEST_KEY_EXPONENT1 = int(
    '971401692373919639404678505179789291960987093676634885925231250693661495'
    '080125935714710587508461815572290443270923375888685273287584323569222368'
    '5450962737')
TEST_KEY_EXPONENT2 = int(
    '405135004809332318340885085107137607293826268763328174261828392259785080'
    '028911220030572618988900118679333717167345003034279703551607153395397272'
    '3014807045')
TEST_KEY_COEFFICIENT = int(
    '933140693852464192207530806898449261372116224159220632563973880414444021'
    '989007318611849609226428922185905596238131661588470844906391982906126973'
    '1282880267')
TEST_PK = {
    'version': 0,
    'modulus': TEST_KEY_MODULUS,
    'publicExponent': TEST_KEY_PUBLIC_EXPONENT,
    'privateExponent': TEST_KEY_PRIVATE_EXPONENT,
    'prime1': TEST_KEY_PRIME1,
    'prime2': TEST_KEY_PRIME2,
    'exponent1': TEST_KEY_EXPONENT1,
    'exponent2': TEST_KEY_EXPONENT2,
    'coefficient': TEST_KEY_COEFFICIENT,
}


class TestStrIntConversion(unittest.TestCase):

    def test_str2int(self):
        self.assertEqual(1234, str2int(b'\x04\xd2'))

    def test_int2str(self):
        self.assertEqual(b'\x04\xd2', int2str(1234))

    def test_int2str_with_length(self):
        self.assertEqual(b'\x00\x00\x04\xd2', int2str(1234, 4))

    def test_int2str_fails_on_negative(self):
        self.assertRaises(AssertionError, int2str, -1)


class TestParseKeys(unittest.TestCase):

    def test_parse_pem_private_key(self):
        key = parse_pem_private_key(read_test_data('test.private'))
        self.assertEqual(key, TEST_PK)

    def test_parse_public_key(self):
        data = read_test_data('test.txt')
        key = parse_public_key(base64.b64decode(parse_tag_value(data)[b'p']))
        self.assertEqual(key['modulus'], TEST_KEY_MODULUS)
        self.assertEqual(key['publicExponent'], TEST_KEY_PUBLIC_EXPONENT)
        try:
          data = read_test_data('test_bad.txt')
          key = parse_public_key(base64.b64decode(parse_tag_value(data)[b'p']))
        except UnparsableKeyError: return
        self.fail("failed to reject invalid public key")


class TestEMSA_PKCS1_v1_5(unittest.TestCase):

    def test_encode_sha256(self):
        hash = hashlib.sha256(b'message')
        self.assertEqual(
            b'\x00\x01\xff\xff\xff\xff\xff\xff\xff\xff\x00'
            b'010\x0d\x06\x09\x60\x86\x48\x01\x65\x03\x04\x02\x01\x05\x00\x04'
            b' ' + hash.digest(),
            EMSA_PKCS1_v1_5_encode(hash, 62))

    def test_encode_sha1(self):
        hash = hashlib.sha1(b'message')
        self.assertEqual(
            b'\x00\x01\xff\xff\xff\xff\xff\xff\xff\xff\x00'
            b'0!0\x09\x06\x05\x2b\x0e\x03\x02\x1a\x05\x00\x04\x14'
            + hash.digest(),
            EMSA_PKCS1_v1_5_encode(hash, 46))

    def test_encode_forbids_too_short(self):
        # PKCS#1 requires at least 8 bytes of padding, so there must be
        # at least that much space.
        hash = hashlib.sha1(b'message')
        self.assertRaises(
            DigestTooLargeError,
            EMSA_PKCS1_v1_5_encode, hash, 45)


class TestRSASSA(unittest.TestCase):

    def setUp(self):
        self.key = parse_pem_private_key(read_test_data('test.private'))
        self.hash = hashlib.sha1(self.test_digest)

    test_digest = b'0123456789abcdef0123'
    test_signature = binascii.unhexlify(
        b'cc8d3647d64dd3bc12984947a27bdfbb565041fcc9db781afb4b60d29d288d8d60d'
        b'e9e1916d6f81569c3e72af442538dd6aecb50a6de9a14565fdd679c46ff7842482e'
        b'15e5aa078549621b6f12ca8cd57ecfad95b18e53581e131c6c3c7cd01cb153adeb4'
        b'39d2d6ab8b215b19be0e69ef490885004a474eb26d747a219693e8c')

    def test_sign_and_verify(self):
        signature = RSASSA_PKCS1_v1_5_sign(self.hash, TEST_PK)
        self.assertEqual(self.test_signature, signature)
        self.assertTrue(
            RSASSA_PKCS1_v1_5_verify(
                self.hash, signature, TEST_PK))

    def test_invalid_signature(self):
        invalid_key = TEST_PK.copy()
        invalid_key['modulus'] += 1
        self.assertFalse(
            RSASSA_PKCS1_v1_5_verify(
                self.hash, self.test_signature, invalid_key))


def test_suite():
    from unittest import TestLoader
    return TestLoader().loadTestsFromName(__name__)
