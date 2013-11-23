# -*- coding: utf-8 -*-
import os
import re
import unittest

from django.utils.importlib import import_module

loadTestsFromModule = unittest.defaultTestLoader.loadTestsFromModule

DEFAULT_TESTFILE_PATTERN = re.compile(r'^[a-zA-Z0-9].*\.py')


def get_suite(*names, **kwargs):
    '''Creates (or updates) a ``TestSuite`` consisting of the tests under one or
    more modules.

    See http://djangosnippets.org/snippets/1972/

    This is useful for splitting a Django ``tests.py`` module into multiple test
    modules under a ``tests`` directory without having to import them manually
    in ``tests/__init__.py``. All you have to write in ``tests/__init__.py`` is::

        from ... import get_suite

        # django.test looks for a function named suite that returns a TestSuite
        suite = lambda: get_suite(__name__)

    This creates a suite consisting of all ``TestCase`` instances defined under
    any ``test_.*py`` module under ``tests``.

    :param names: One or more module or package names to be added in the suite.
        For module names, the respective module's TestCases are loaded. For package
        names, the TestCases of all modules in the package directory satisfying
        ``is_test_module`` are loaded.
    :keyword is_test_module: Determines whether a file is a test module. It can
        be a callable ``f(filename)`` or a regular expression (string or compiled)
        that test module file names should ``match()``.
    :keyword suite: If given, update this suite instead of creating a new one.
    '''

    suite = kwargs.get('suite') or unittest.TestSuite()
    # determine is_test_module
    is_test_module = kwargs.get('is_test_module', DEFAULT_TESTFILE_PATTERN)
    if isinstance(is_test_module, basestring):  # look for exact match
        is_test_module = re.compile(is_test_module + '$').match
    elif hasattr(is_test_module, 'match'):
        is_test_module = is_test_module.match
    # determine the test modules to be added in the suite and import them
    modules = set()
    for name in names:
        package = import_module(name)
        # if it's a single module just add it
        if os.path.splitext(os.path.basename(package.__file__))[0] != '__init__':
            modules.add(package)
        else: # otherwise it's a package; add all test modules under the dir
            modules.update(
                import_module('.' + os.path.splitext(f)[0], package=name)
                for f in os.listdir(os.path.dirname(package.__file__))
                if is_test_module(f))
    # add the modules to the suite
    for module in modules:
        # copied from django.test.simple.build_suite
        if hasattr(module, 'suite'):
            # if module has a suite() method, use it
            suite.addTest(module.suite())
        else: # otherwise build the test suite ourselves.
            suite.addTest(loadTestsFromModule(module))
    return suite

suite = lambda: get_suite(__name__)
