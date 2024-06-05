import unittest
import doctest
import dkim
from dkim.tests import test_suite
from dkim.tests.test_arc import test_suite as arc_test_suite
import logging

doctest.testmod(dkim)
unittest.TextTestRunner().run(test_suite())
unittest.TextTestRunner().run(arc_test_suite())
