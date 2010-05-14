# -*- coding: utf-8 -*-
from django.test import TestCase
from datetime import datetime
from django.test.client import Client
from codespeed.models import Project, Benchmark, Revision, Executable, Environment, Result
from django.core.urlresolvers import reverse
import copy, json

class AddResultTest(TestCase):
    def setUp(self):
        self.path = reverse('codespeed.views.addresult')
        self.client = Client()
        self.e = Environment(name='bigdog', cpu='Core 2 Duo 8200')
        self.e.save()
        temp = datetime.today()
        self.cdate = datetime(temp.year, temp.month, temp.day, temp.hour, temp.minute, temp.second)
        self.data = {
                'commitid': '23232',
                'project': 'pypy',
                'executable_name': 'pypy-c',
                'benchmark': 'Richards',
                'environment': 'bigdog',
                'result_value': 456,
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
        p = Project.objects.get(name='pypy')
        r = Revision.objects.get(commitid='23232', project=p)
        i = Executable.objects.get(name='pypy-c', coptions='')
        res = Result.objects.get(
            revision=r,
            executable=i,
            benchmark=b,
            environment=e
        )
        self.assertTrue(res.value, 456)
        resdate = res.date.strftime("%Y%m%dT%H%M%S")
        selfdate = self.cdate.strftime("%Y%m%dT%H%M%S")
        self.assertTrue(resdate, selfdate)
        
    def test_add_non_default_result(self):
        """
        Add result data with non-default options
        """
        modified_data = copy.deepcopy(self.data)
        modified_data['executable_coptions'] = 'gc=Böhm'
        modified_data['benchmark_type'] = "O"
        modified_data['units'] = "fps"
        modified_data['lessisbetter'] = False
        modified_data['result_date'] = self.cdate
        modified_data['std_dev'] = 1.11111
        modified_data['max'] = 2
        modified_data['min'] = 1.0
        response = self.client.post(self.path, modified_data)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.content, "Result data saved succesfully")
        e = Environment.objects.get(name='bigdog')    
        p = Project.objects.get(name='pypy')
        r = Revision.objects.get(commitid='23232', project=p)
        self.assertEquals(r.date, self.cdate)
        i = Executable.objects.get(name='pypy-c', coptions='gc=Böhm')
        b = Benchmark.objects.get(name='Richards')
        res = Result.objects.get(
            revision=r,
            executable=i,
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

class Timeline(TestCase):
    fixtures = ["multi_project_host.json"]
    
    def setUp(self):
        self.client = Client()
    
    def test_gettimelinedata(self):
        """Test that gettimelinedata returns correct timeline data
        """
        path = reverse('codespeed.views.gettimelinedata')
        data = {
            "executables": "1,2,6",
            "baseline": "true",
            "benchmark": "ai",
            "host": "bigdog",
            "revisions": 16
        }
        response = self.client.get(path, data)
        responsedata = json.loads(response.content)
        self.assertEquals(responsedata['error'], "None", "there should be no errors")
        self.assertEquals(len(responsedata['timelines']), 1, "there should be 1 benchmark")
        self.assertEquals(len(responsedata['timelines'][0]['executables']), 2, "there should be 2 timelines")
        self.assertEquals(len(responsedata['timelines'][0]['executables']['1']), 16, "There are 16 datapoints")
        self.assertEquals(responsedata['timelines'][0]['executables']['1'][4], ['2010-04-14 19:55:18', 0.433843383789, 0.0099517018942000008, '73755'], "Wrong data")
