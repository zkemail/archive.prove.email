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

import unittest

from dkim.util import (
    DuplicateTag,
    InvalidTagSpec,
    parse_tag_value,
    get_linesep,
    )


class TestParseTagValue(unittest.TestCase):
    """Tag=Value parsing tests."""

    def test_single(self):
        self.assertEqual(
            {b'foo': b'bar'},
            parse_tag_value(b'foo=bar'))

    def test_trailing_separator_ignored(self):
        self.assertEqual(
            {b'foo': b'bar'},
            parse_tag_value(b'foo=bar;'))

    def test_multiple(self):
        self.assertEqual(
            {b'foo': b'bar', b'baz': b'foo'},
            parse_tag_value(b'foo=bar;baz=foo'))

    def test_value_with_equals(self):
        self.assertEqual(
            {b'foo': b'bar', b'baz': b'foo=bar'},
            parse_tag_value(b'foo=bar;baz=foo=bar'))

    def test_whitespace_is_stripped(self):
        self.assertEqual(
            {b'foo': b'bar', b'baz': b'f oo=bar'},
            parse_tag_value(b'   foo  \t= bar;\tbaz=  f oo=bar  '))

    def test_missing_value_is_an_error(self):
        self.assertRaises(
            InvalidTagSpec, parse_tag_value, b'foo=bar;baz')

    def test_duplicate_tag_is_an_error(self):
        self.assertRaises(
            DuplicateTag, parse_tag_value, b'foo=bar;foo=baz')

    def test_trailing_whitespace(self):
      hval = b'''v=1; a=rsa-sha256; d=facebookmail.com; s=s1024-2011-q2; c=relaxed/simple;
          q=dns/txt; i=@facebookmail.com; t=1308078492;
          h=From:Subject:Date:To:MIME-Version:Content-Type;
          bh=+qPyCOiDQkusTPstCoGjimgDgeZbUaJWIr1mdE6RFxk=;
          b=EUmDmdnAsNtjSEHGHNTa8PXgGaEUtOVezagmninX5Bs/Q26R9r3AMgawyUSKkbHp
          /bQZU6QPZfdvmLMPdIWCQPo8SP+gsz4dpox2efO61DlvgYaxBRhwFedAW9LjYhQc
          3KzW0yB9JHwiDCw1EioVkv+OMHhAYzoIypA0bQyi2bc=;
  '''
      sig = parse_tag_value(hval)
      self.assertEqual(sig[b't'],b'1308078492')
      self.assertEqual(len(sig),11)


class TestGetLineSep(unittest.TestCase):
    """Line seperator probing tests."""

    def test_default(self):
        self.assertEqual(
            b'\r\n',
            get_linesep(b'abc'))

    def test_withcrlf(self):
        self.assertEqual(
            b'\r\n',
            get_linesep(b'abc\r\n'))

    def test_withlf(self):
        self.assertEqual(
            b'\n',
            get_linesep(b'abc\n'))

    def test_toosmall(self):
        self.assertEqual(
            b'\r\n',
            get_linesep(b'a'))


def test_suite():
    from unittest import TestLoader
    return TestLoader().loadTestsFromName(__name__)
