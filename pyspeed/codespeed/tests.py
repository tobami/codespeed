# -*- coding: utf-8 -*-
"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""

from django.test import TestCase
import urllib, urllib2
import simplejson
from datetime import datetime

class AddResultTest(TestCase):
    def test_add_result(self):
        """
        Add result data
        """
        data = {
            'revision_number': '23232',
            'revision_project': 'pypy',
            'interpreter_name': 'pypy-c',
            'interpreter_coptions': 'gc=Boehm',
            'benchmark_name': 'Richards',
            'environment': 1,
            'result_key': 'total',
            'result_value': 456,
            'result_date': datetime.today(),
        }
        params = urllib.urlencode(data)
        f = urllib2.urlopen('http://localhost:8000/pypy/result/add/', params)
        data = f.read()
        print "Server response:", data
        f.close()

