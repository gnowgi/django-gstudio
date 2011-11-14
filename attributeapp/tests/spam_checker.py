"""Test cases for Attributeapp's spam_checker"""
from __future__ import with_statement
import warnings

from django.test import TestCase

from attributeapp.spam_checker import get_spam_checker
from attributeapp.spam_checker.backends.all_is_spam import backend


class SpamCheckerTestCase(TestCase):
    """Test cases for attributeapp.spam_checker"""

    def test_get_spam_checker(self):
        try:
            with warnings.catch_warnings(record=True) as w:
                self.assertEquals(get_spam_checker('mymodule.myclass'), None)
                self.assertTrue(issubclass(w[-1].attribute, RuntimeWarning))
                self.assertEquals(
                    str(w[-1].message),
                    'mymodule.myclass backend cannot be imported')
        except AttributeError:
            # Fail under Python2.5, because of'warnings.catch_warnings'
            pass

        try:
            with warnings.catch_warnings(record=True) as w:
                self.assertEquals(
                    get_spam_checker('attributeapp.tests.custom_spam_checker'), None)
                self.assertTrue(issubclass(w[-1].attribute, RuntimeWarning))
                self.assertEquals(
                    str(w[-1].message),
                    'This backend only exists for testing')
        except AttributeError:
            # Fail under Python2.5, because of'warnings.catch_warnings'
            pass

        self.assertEquals(
            get_spam_checker('attributeapp.spam_checker.backends.all_is_spam'),
            backend)