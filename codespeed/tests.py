# -*- coding: utf-8 -*-
from datetime import datetime
from time import sleep
import copy, json

from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse
from django.conf import settings
from codespeed.models import (Project, Benchmark, Revision, Branch,
    Executable, Environment, Result, Report)
from codespeed import settings as default_settings


class AddResultTest(TestCase):
    def setUp(self):
        self.path = reverse('codespeed.views.add_result')
        self.client = Client()
        self.e = Environment(name='Dual Core', cpu='Core 2 Duo 8200')
        self.e.save()
        temp = datetime.today()
        self.cdate = datetime(
            temp.year, temp.month, temp.day, temp.hour, temp.minute, temp.second)
        self.data = {
                'commitid': '23',
                'branch': 'default',
                'project': 'MyProject',
                'executable': 'myexe O3 64bits',
                'benchmark': 'float',
                'environment': 'Dual Core',
                'result_value': 456,
        }

    def test_add_correct_result(self):
        """Add correct result data"""
        response = self.client.post(self.path, self.data)
        
        # Check that we get a success response
        self.assertEquals(response.status_code, 202)
        self.assertEquals(response.content, "Result data saved succesfully")
        
        # Check that the data was correctly saved
        e = Environment.objects.get(name='Dual Core')
        b = Benchmark.objects.get(name='float')
        self.assertEquals(b.benchmark_type, "C")
        self.assertEquals(b.units, "seconds")
        self.assertEquals(b.lessisbetter, True)
        p = Project.objects.get(name='MyProject')
        branch = Branch.objects.get(name='default', project=p)
        r = Revision.objects.get(commitid='23', branch=branch)
        i = Executable.objects.get(name='myexe O3 64bits')
        res = Result.objects.get(
            revision=r,
            executable=i,
            benchmark=b,
            environment=e
        )
        self.assertTrue(res.value, 456)

    def test_add_non_default_result(self):
        """Add result data with non-mandatory options"""
        modified_data = copy.deepcopy(self.data)
        modified_data['result_date'] = self.cdate
        modified_data['revision_date'] = self.cdate
        sleep(1.5)#ensure current date changes
        modified_data['std_dev']     = 1.11111
        modified_data['max']         = 2
        modified_data['min']         = 1.0
        response = self.client.post(self.path, modified_data)
        self.assertEquals(response.status_code, 202)
        self.assertEquals(response.content, "Result data saved succesfully")
        e = Environment.objects.get(name='Dual Core')
        p = Project.objects.get(name='MyProject')
        branch = Branch.objects.get(name='default', project=p)
        r = Revision.objects.get(commitid='23', branch=branch)

        # Tweak the resolution down to avoid failing over very slight differences:
        self.assertEquals(
            r.date.replace(microsecond=0), self.cdate.replace(microsecond=0))

        i = Executable.objects.get(name='myexe O3 64bits')
        b = Benchmark.objects.get(name='float')
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
        """Should return 400 when environment does not exist"""
        bad_name = '10 Core'
        self.data['environment'] = bad_name
        response = self.client.post(self.path, self.data)
        self.assertEquals(response.status_code, 400)
        self.assertEquals(response.content, "Environment " + bad_name + " not found")
        self.data['environment'] = 'Dual Core'

    def test_empty_argument(self):
        """Should respond 400 when a POST request has an empty argument"""
        for key in self.data:
            backup = self.data[key]
            self.data[key] = ""
            response = self.client.post(self.path, self.data)
            self.assertEquals(response.status_code, 400)
            self.assertEquals(
                response.content, 'Value for key "' + key + '" empty in request')
            self.data[key] = backup

    def test_missing_argument(self):
        """Should respond 400 when a POST request is missing an argument"""
        for key in self.data:
            backup = self.data[key]
            del(self.data[key])
            response = self.client.post(self.path, self.data)
            self.assertEquals(response.status_code, 400)
            self.assertEquals(
                response.content, 'Key "' + key + '" missing from request')
            self.data[key] = backup

    def test_report_is_not_created(self):
        '''Should not create a report when adding a single result'''
        response = self.client.post(self.path, self.data)
        number_of_reports = len(Report.objects.all())
        # After adding one result for one revision, there should be no reports
        self.assertEquals(number_of_reports, 0)

    def test_report_is_created(self):
        '''Should create a report when adding a result for two revisions'''
        response = self.client.post(self.path, self.data)
        
        modified_data = copy.deepcopy(self.data)
        modified_data['commitid'] = "23233"
        response = self.client.post(self.path, modified_data)
        number_of_reports = len(Report.objects.all())
        # After adding a result for a second revision, a report should be created
        self.assertEquals(number_of_reports, 1)


class AddJSONResultsTest(TestCase):
    def setUp(self):
        self.path = reverse('codespeed.views.add_json_results')
        self.client = Client()
        self.e = Environment(name='bigdog', cpu='Core 2 Duo 8200')
        self.e.save()
        temp = datetime.today()
        self.cdate = datetime(
            temp.year, temp.month, temp.day, temp.hour, temp.minute, temp.second)
        
        self.data = [
            {'commitid': '123',
            'project': 'pypy',
            'branch': 'default',
            'executable': 'pypy-c',
            'benchmark': 'Richards',
            'environment': 'bigdog',
            'result_value': 456,},
            {'commitid': '456',
            'project': 'pypy',
            'branch': 'default',
            'executable': 'pypy-c',
            'benchmark': 'Richards',
            'environment': 'bigdog',
            'result_value': 457,},
            {'commitid': '456',
            'project': 'pypy',
            'branch': 'default',
            'executable': 'pypy-c',
            'benchmark': 'Richards2',
            'environment': 'bigdog',
            'result_value': 34,},
            {'commitid': '789',
            'project': 'pypy',
            'branch': 'default',
            'executable': 'pypy-c',
            'benchmark': 'Richards',
            'environment': 'bigdog',
            'result_value': 458,},
        ]

    def test_add_correct_results(self):
        """Should add all results when the request data is valid"""
        response = self.client.post(self.path, {'json' : json.dumps(self.data)})

        # Check that we get a success response
        self.assertEquals(response.status_code, 202)
        self.assertEquals(response.content, "All result data saved successfully")

        # Check that the data was correctly saved
        e = Environment.objects.get(name='bigdog')
        b = Benchmark.objects.get(name='Richards')
        self.assertEquals(b.benchmark_type, "C")
        self.assertEquals(b.units, "seconds")
        self.assertEquals(b.lessisbetter, True)
        p = Project.objects.get(name='pypy')
        branch = Branch.objects.get(name='default', project=p)
        r = Revision.objects.get(commitid='123', branch=branch)
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
        
        r = Revision.objects.get(commitid='456', branch=branch)
        res = Result.objects.get(
            revision=r,
            executable=i,
            benchmark=b,
            environment=e
        )
        self.assertTrue(res.value, 457)

        r = Revision.objects.get(commitid='789', branch=branch)
        res = Result.objects.get(
            revision=r,
            executable=i,
            benchmark=b,
            environment=e
        )
        self.assertTrue(res.value, 458)

    def test_bad_environment(self):
        """Add result associated with non-existing environment.
           Only change one item in the list.
        """
        data = self.data[0]
        bad_name = 'bigdog1'
        data['environment'] = bad_name
        response = self.client.post(self.path, {'json' : json.dumps(self.data)})

        self.assertEquals(response.status_code, 400)
        self.assertEquals(response.content, "Environment " + bad_name + " not found")
        data['environment'] = 'bigdog'

    def test_empty_argument(self):
        '''Should return 400 when making a request with an empty argument'''
        data = self.data[1]
        for key in data:
            backup = data[key]
            data[key] = ""
            response = self.client.post(self.path,
                        {'json' : json.dumps(self.data)})
            self.assertEquals(response.status_code, 400)
            self.assertEquals(response.content, 'Value for key "' + key + '" empty in request')
            data[key] = backup

    def test_missing_argument(self):
        '''Should return 400 when making a request with a missing argument'''
        data = self.data[2]
        for key in data:
            backup = data[key]
            del(data[key])
            response = self.client.post(self.path,
                        {'json' : json.dumps(self.data)})
            self.assertEquals(response.status_code, 400)
            self.assertEquals(response.content, 'Key "' + key + '" missing from request')
            data[key] = backup

    def test_report_is_created(self):
        '''Should create a report when adding json results for two revisions
        plus a third revision with one result less than the last one'''
        response = self.client.post(self.path, {'json' : json.dumps(self.data)})

        # Check that we get a success response
        self.assertEquals(response.status_code, 202)

        number_of_reports = len(Report.objects.all())
        # After adding 4 result for 3 revisions, only 2 reports should be created
        # The third revision will need an extra result for Richards2 in order
        # to trigger report creation
        self.assertEquals(number_of_reports, 1)


class Timeline(TestCase):
    fixtures = ["gettimeline_unittest.json"]

    def setUp(self):
        self.client = Client()

    def test_fixture(self):
        """Test the loaded fixture data
        """
        env = Environment.objects.filter(name="Dual Core")
        self.assertEquals(len(env), 1)
        benchmarks = Benchmark.objects.filter(name="float")
        self.assertEquals(len(benchmarks), 1)
        self.assertEquals(benchmarks[0].units, "seconds")
        results = benchmarks[0].results.all()
        self.assertEquals(len(results), 8)

    def test_gettimelinedata(self):
        """Test that gettimelinedata returns correct timeline data
        """
        path = reverse('codespeed.views.gettimelinedata')
        data = {
            "exe":  "1,2",
            "base": "2+4",
            "ben":  "float",
            "env":  "Dual Core",
            "revs": 2
        }
        response = self.client.get(path, data)
        self.assertEquals(response.status_code, 200)
        responsedata = json.loads(response.content)
        self.assertEquals(
            responsedata['error'], "None", "there should be no errors")
        self.assertEquals(
            len(responsedata['timelines']), 1, "there should be 1 benchmark")
        self.assertEquals(
            len(responsedata['timelines'][0]['branches']['default']),
            2,
            "there should be 2 timelines")
        self.assertEquals(
            len(responsedata['timelines'][0]['branches']['default']['1']),
            2,
            "There are 2 datapoints")
        self.assertEquals(
            responsedata['timelines'][0]['branches']['default']['1'][1],
            [u'2011-04-13 17:04:22', 2000.0, 1.11111, u'2', u'default'],
            "Wrong data returned: ")


class CodespeedSettings(TestCase):
    """Test codespeed.settings
    """

    def setUp(self):
        self.cs_setting_keys = [key for key in dir(default_settings) if key.isupper()]

    def test_website_name(self):
        """See if WEBSITENAME is set
        """
        self.assertTrue(default_settings.WEBSITE_NAME)
        self.assertEqual(default_settings.WEBSITE_NAME, 'MySpeedSite',
                         "Change codespeed settings in project.settings")

    def test_keys_in_settings(self):
        """Check that all settings attributes from codespeed.settings exist
        in django.conf.settings
        """
        for k in self.cs_setting_keys:
            self.assertTrue(hasattr(settings, k))

    def test_settings_attributes(self):
        """Check if all settings from codespeed.settings equals
        django.conf.settings
        """
        for k in self.cs_setting_keys:
            self.assertEqual(getattr(settings, k), getattr(default_settings, k))

