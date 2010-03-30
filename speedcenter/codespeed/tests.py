# -*- coding: utf-8 -*-
from django.test import TestCase
from datetime import datetime
from django.test.client import Client
from codespeed.models import Benchmark, Revision, Interpreter, Environment, Result
from django.core.urlresolvers import reverse

class AddResultTest(TestCase):
    def setUp(self):
        self.path = reverse('codespeed.views.addresult')
        self.client = Client()
        self.e = Environment(name='bigdog', cpu='Core 2 Duo 8200')
        self.e.save()
        self.cdate = datetime.today()
        self.data = {
                'revision_number': '23232',
                'revision_project': 'pypy',
                'interpreter_name': 'pypy-c',
                'interpreter_coptions': 'gc=Böhm',
                'benchmark_name': 'Richards',
                'environment': 'bigdog',
                'result_value': 456,
                'result_date': self.cdate,
        }        
    def test_add_default_result(self):
        """
        Add result data using default options
        """
        response = self.client.post(self.path, self.data)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.content, "Result data saved succesfully")
        e = Environment.objects.get(name='bigdog')        
        b = Benchmark.objects.get(name='Richards')
        self.assertEquals(b.benchmark_type, "C")
        self.assertEquals(b.units, "seconds")
        self.assertEquals(b.lessisbetter, True)
        r = Revision.objects.get(number='23232', project='pypy')
        i = Interpreter.objects.get(name='pypy-c', coptions='gc=Böhm')
        self.assertTrue(Result.objects.get(
            value=456,
            date=self.cdate,
            revision=r,
            interpreter=i,
            benchmark=b,
            environment=e
        ))
    
    def test_add_non_default_result(self):
        """
        Add result data with non-default options
        """
        modified_data = self.data
        modified_data['benchmark_type'] = "O"
        modified_data['units'] = "fps"
        modified_data['lessisbetter'] = False
        modified_data['std_dev'] = 1.11111
        modified_data['max'] = 2
        modified_data['min'] = 1.0
        response = self.client.post(self.path, modified_data)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.content, "Result data saved succesfully")
        e = Environment.objects.get(name='bigdog')        
        b = Benchmark.objects.get(name='Richards')
        self.assertEquals(b.benchmark_type, "O")
        self.assertEquals(b.units, "fps")
        self.assertEquals(b.lessisbetter, False)
        r = Revision.objects.get(number='23232', project='pypy')
        i = Interpreter.objects.get(name='pypy-c', coptions='gc=Böhm')
        
        res = Result.objects.get(
            value=456,
            date=self.cdate,
            revision=r,
            interpreter=i,
            benchmark=b,
            environment=e
        )
        self.assertEquals(res.std_dev, 1.11111)
        self.assertEquals(res.val_max, 2)
        self.assertEquals(res.val_min, 1)

    def test_bad_environment(self):
        """
        Add result associated with non-existing environment
        """
        bad_name = 'bigdog1'
        self.data['environment'] = bad_name
        response = self.client.post(self.path, self.data)
        self.assertEquals(response.status_code, 404)
        self.assertEquals(response.content, "Environment " + bad_name + " not found")
        self.data['environment'] = 'bigdog'
    
    def test_empty_argument(self):
        """
        Make POST request with an empty argument.
        """
        for key in self.data:
            backup = self.data[key]
            self.data[key] = ""
            response = self.client.post(self.path, self.data)
            self.assertEquals(response.status_code, 400)
            self.assertEquals(response.content, 'Key "' + key + '" empty in request')
            self.data[key] = backup
    
    def test_missing_argument(self):
        """
        Make POST request with a missing argument.
        """
        for key in self.data:
            backup = self.data[key]
            del(self.data[key])
            response = self.client.post(self.path, self.data)
            self.assertEquals(response.status_code, 400)
            self.assertEquals(response.content, 'Key "' + key + '" missing from request')
            self.data[key] = backup
