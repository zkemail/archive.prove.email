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
# Copyright (c) 2018 Scott Kitterman <scott@kitterman.com>

import unittest


def test_suite():
    from dkim.tests import (
        test_canonicalization,
        test_crypto,
        test_dkim,
        test_dkim_ed25519,
        test_dkim_rsavariants,
        test_dkim_tlsrpt,
        test_util,
        test_arc,
        test_dnsplug,
        test_dkim_generate,
        )
    modules = [
        test_canonicalization,
        test_crypto,
        test_dkim,
        test_dkim_ed25519,
        test_dkim_rsavariants,
        test_dkim_tlsrpt,
        test_util,
        test_arc,
        test_dnsplug,
        test_dkim_generate,
        ]
    suites = [x.test_suite() for x in modules]
    return unittest.TestSuite(suites)
