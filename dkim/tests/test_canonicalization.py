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

from dkim.canonicalization import (
    CanonicalizationPolicy,
    InvalidCanonicalizationPolicyError,
    Simple,
    Relaxed,
    )


class BaseCanonicalizationTest(unittest.TestCase):

    def assertCanonicalForm(self, expected, input):
        self.assertEqual(expected, self.func(expected))
        self.assertEqual(expected, self.func(input))


class TestSimpleAlgorithmHeaders(BaseCanonicalizationTest):

    func = staticmethod(Simple.canonicalize_headers)

    def test_untouched(self):
        test_headers = [(b'Foo  ', b'bar\r\n'), (b'Foo', b'baz\r\n')]
        self.assertCanonicalForm(
            test_headers,
            test_headers)


class TestSimpleAlgorithmBody(BaseCanonicalizationTest):

    func = staticmethod(Simple.canonicalize_body)

    def test_strips_trailing_empty_lines_from_body(self):
        self.assertCanonicalForm(
            b'Foo  \tbar    \r\n',
            b'Foo  \tbar    \r\n\r\n')

    def test_adds_crlf(self):
        self.assertCanonicalForm(
            b'Foo bar\r\n',
            b'Foo bar')

    def test_empty_body(self):
        self.assertCanonicalForm(
            b'\r\n',
            b'')

    def test_single_crlf_body(self):
        self.assertCanonicalForm(
            b'\r\n',
            b'\r\n')

    def test_multiple_crlf_body(self):
        self.assertCanonicalForm(
            b'\r\n',
            b'\r\n\r\n')


class TestRelaxedAlgorithmHeaders(BaseCanonicalizationTest):

    func = staticmethod(Relaxed.canonicalize_headers)

    def test_lowercases_names(self):
        self.assertCanonicalForm(
            [(b'foo', b'Bar\r\n'), (b'baz', b'Foo\r\n')],
            [(b'Foo', b'Bar\r\n'), (b'BaZ', b'Foo\r\n')])

    def test_unfolds_values(self):
        self.assertCanonicalForm(
            [(b'foo', b'Bar baz\r\n')],
            [(b'Foo', b'Bar\r\n baz\r\n')])

    def test_wsp_compresses_values(self):
        self.assertCanonicalForm(
            [(b'foo', b'Bar baz\r\n')],
            [(b'Foo', b'Bar \t baz\r\n')])

    def test_wsp_strips(self):
        self.assertCanonicalForm(
            [(b'foo', b'Bar baz\r\n')],
            [(b'Foo  ', b'   Bar \t baz   \r\n')])


class TestRelaxedAlgorithmBody(BaseCanonicalizationTest):

    func = staticmethod(Relaxed.canonicalize_body)

    def test_strips_trailing_wsp(self):
        self.assertCanonicalForm(
            b'Foo\r\nbar\r\n',
            b'Foo  \t\r\nbar\r\n')

    def test_wsp_compresses(self):
        self.assertCanonicalForm(
            b'Foo bar\r\n',
            b'Foo  \t  bar\r\n')

    def test_strips_trailing_empty_lines(self):
        self.assertCanonicalForm(
            b'Foo\r\nbar\r\n',
            b'Foo\r\nbar\r\n\r\n\r\n')

    def test_adds_crlf(self):
        self.assertCanonicalForm(
            b'Foo bar\r\n',
            b'Foo bar')

    def test_empty_body(self):
        self.assertCanonicalForm(
            b'',
            b'')

    def test_single_crlf_body(self):
        self.assertCanonicalForm(
            b'',
            b'\r\n')

    def test_multiple_crlf_body(self):
        self.assertCanonicalForm(
            b'',
            b'\r\n\r\n')


class TestCanonicalizationPolicyFromCValue(unittest.TestCase):

    def assertAlgorithms(self, header_algo, body_algo, c_value):
        p = CanonicalizationPolicy.from_c_value(c_value)
        self.assertEqual(
            (header_algo, body_algo),
            (p.header_algorithm, p.body_algorithm))

    def assertValueDoesNotParse(self, c_value):
        self.assertRaises(
            InvalidCanonicalizationPolicyError,
            CanonicalizationPolicy.from_c_value, c_value)

    def test_both_default_to_simple(self):
        self.assertAlgorithms(Simple, Simple, None)

    def test_relaxed_headers(self):
        self.assertAlgorithms(Relaxed, Simple, b'relaxed')

    def test_relaxed_body(self):
        self.assertAlgorithms(Simple, Relaxed, b'simple/relaxed')

    def test_relaxed_both(self):
        self.assertAlgorithms(Relaxed, Relaxed, b'relaxed/relaxed')

    def test_explict_simple_both(self):
        self.assertAlgorithms(Simple, Simple, b'simple/simple')

    def test_corruption_is_ignored(self):
        self.assertValueDoesNotParse(b'')
        self.assertValueDoesNotParse(b'simple/simple/simple')
        self.assertValueDoesNotParse(b'relaxed/stressed')
        self.assertValueDoesNotParse(b'worried')


class TestCanonicalizationPolicyToCValue(unittest.TestCase):

    def assertCValue(self, c_value, header_algo, body_algo):
        self.assertEqual(
            c_value,
            CanonicalizationPolicy(header_algo, body_algo).to_c_value())

    def test_both_simple(self):
        self.assertCValue(b'simple/simple', Simple, Simple)

    def test_relaxed_body(self):
        self.assertCValue(b'simple/relaxed', Simple, Relaxed)

    def test_both_relaxed(self):
        self.assertCValue(b'relaxed/relaxed', Relaxed, Relaxed)

    def test_relaxed_headers(self):
        self.assertCValue(b'relaxed/simple', Relaxed, Simple)


def test_suite():
    from unittest import TestLoader
    return TestLoader().loadTestsFromName(__name__)
