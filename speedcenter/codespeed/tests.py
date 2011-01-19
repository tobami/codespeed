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
                'executable': 'pypy-c',
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
        i = Executable.objects.get(name='pypy-c')
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
        
        # reduce precision of r.data to allow test to pass
        self.assertEquals(r.date.replace(microsecond=0), self.cdate)
        i = Executable.objects.get(name='pypy-c')
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

class AddResultsTest(AddResultTest):
    def setUp(self):
        self.path = reverse('codespeed.views.addresults')
        self.client = Client()
        self.e = Environment(name='bigdog', cpu='Core 2 Duo 8200')
        self.e.save()
        temp = datetime.today()
        self.cdate = datetime(temp.year, temp.month, temp.day, temp.hour, temp.minute, temp.second)
        
        self.data = {'items':
            [  {'commitid':    '123',
                'project':     'pypy',
                'executable':  'pypy-c',
                'benchmark':   'Richards1',
                'environment': 'bigdog',
                'result_value': 456,},
               {'commitid':    '456',
                'project':     'pypy',
                'executable':  'pypy-c',
                'benchmark':   'Richards2',
                'environment': 'bigdog',
                'result_value': 457,},
               {'commitid':    '789',
                'project':     'pypy',
                'executable':  'pypy-c',
                'benchmark':   'Richards3',
                'environment': 'bigdog',
                'result_value': 458,}] }

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
        r = Revision.objects.get(commitid='123', project=p)
        i = Executable.objects.get(name='pypy-c')
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
        
        r = Revision.objects.get(commitid='456', project=p)
        res = Result.objects.get(
            revision=r,
            executable=i,
            benchmark=b,
            environment=e
        )
        self.assertTrue(res.value, 457)
        
        r = Revision.objects.get(commitid='789', project=p)
        res = Result.objects.get(
            revision=r,
            executable=i,
            benchmark=b,
            environment=e
        )
        self.assertTrue(res.value, 458)
        

    def test_bad_environment(self):
        """
        Add result associated with non-existing environment.
        Only change one item in the list.
        """
        response = self.client.post(self.path, self.data)
        print response
        
        
        data = self.data['items'][0]
        bad_name = 'bigdog1'
        data['environment'] = bad_name
        response = self.client.post(self.path, self.data)
        self.assertEquals(response.status_code, 404)
        self.assertEquals(response.content, "Environment " + bad_name + " not found")
        data['environment'] = 'bigdog'

    def test_empty_argument(self):
        """
        Make POST request with an empty argument.
        Only change one item in the list.
        """
        data = self.data['items'][1]
        for key in data:
            backup = data[key]
            data[key] = ""
            response = self.client.post(self.path, self.data)
            self.assertEquals(response.status_code, 400)
            self.assertEquals(response.content, 'Key "' + key + '" empty in request')
            data[key] = backup

    def test_missing_argument(self):
        """
        Make POST request with a missing argument.
        Only change one item in the list.
        """
        data = self.data['items'][2]
        for key in data:
            backup = data[key]
            del(data[key])
            response = self.client.post(self.path, self.data)
            self.assertEquals(response.status_code, 400)
            self.assertEquals(response.content, 'Key "' + key + '" missing from request')
            data[key] = backup


class Timeline(TestCase):
    fixtures = ["pypy.json"]
    
    def setUp(self):
        self.client = Client()
    
    def test_gettimelinedata(self):
        """Test that gettimelinedata returns correct timeline data
        """
        path = reverse('codespeed.views.gettimelinedata')
        data = {
            "exe": "1,2",
            "base": "2+35",
            "ben": "ai",
            "env": "tannit",
            "revs": 16
        }
        response = self.client.get(path, data)
        responsedata = json.loads(response.content)
        self.assertEquals(responsedata['error'], "None", "there should be no errors")
        self.assertEquals(len(responsedata['timelines']), 1, "there should be 1 benchmark")
        self.assertEquals(len(responsedata['timelines'][0]['executables']), 2, "there should be 2 timelines")
        self.assertEquals(len(responsedata['timelines'][0]['executables']['1']), 16, "There are 16 datapoints")
        self.assertEquals(responsedata['timelines'][0]['executables']['1'][4], [u'2010-06-17 18:57:39', 0.404776086807, 0.011496530978, u'75443'], "Wrong data returned: ")

