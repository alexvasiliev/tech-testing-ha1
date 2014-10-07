#!/usr/bin/env python2.7

import os
import sys
import unittest

source_dir = os.path.join(os.path.dirname(__file__), 'source')
sys.path.insert(0, source_dir)

from tests.test_utils import UtilsTestCase
from tests.test_init import InitTestCase


if __name__ == '__main__':
    suite = unittest.TestSuite((
        unittest.makeSuite(UtilsTestCase),
        unittest.makeSuite(InitTestCase),
    ))
    result = unittest.TextTestRunner().run(suite)
    sys.exit(not result.wasSuccessful())
