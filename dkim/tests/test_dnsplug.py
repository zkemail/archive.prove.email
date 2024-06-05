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
# Copyright (c) 2017 Valimail Inc
# Contact: Gene Shuman <gene@valimail.com>
# Copyright (c) 2019 Scott Kitterman <scott@kitterman.com>

import unittest
import sys
try:
    import dkim.dnsplug
except ImportError:
    # Need to not error out so we can test aiodns properly
    pass


class TestDNSPlug(unittest.TestCase):
    
    def test_get_txt(self):
        try:
            dkim.dnsplug._get_txt = {"in": "out"}.get
            res = dkim.dnsplug.get_txt(b"in")
        except NameError: # We may be testing aiodns, so we don't care
            res = b"out"
        self.assertEqual(res, b"out")


def test_suite():
    from unittest import TestLoader
    return TestLoader().loadTestsFromName(__name__)
