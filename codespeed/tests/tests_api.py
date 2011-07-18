# -*- coding: utf-8 -*-

"""
Tests related to RESTful API
"""

from datetime import datetime
import copy, json
import unittest

from django import test
from django.test.client import Client
from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib.auth.models import User
from codespeed.models import (Project, Benchmark, Revision, Branch,
                              Executable, Environment, Result, Report)
from codespeed import settings as default_settings


class FixtureTestCase(test.TestCase):
    fixtures = ["gettimeline_unittest.json"]


class EnvironmentTest(FixtureTestCase):
    """Test Environment() API
    """

    def setUp(self):
        self.env1_data = dict(
            name="env1",
            cpu="cpu1",
            memory="48kB",
            os="ZX Spectrum OS",
            kernel="2.6.32"
        )
        self.env1 = Environment(**self.env1_data)
        self.env1.save()
        self.env2_data = dict(
            name="env2",
            cpu="z80",
            memory="64kB",
            os="ZX Spectrum OS",
            kernel="2.6.32"
        )
        self.client = Client()
        super(FixtureTestCase, self).setUp()

    def test_dual_core(self):
        response = self.client.get('/api/v1/environment/1/')
        self.assertEquals(response.status_code, 200)
        self.assertEqual(json.loads(response.content)['name'], "Dual Core")

    def test_env1(self):
        response = self.client.get('/api/v1/environment/%s/' % (self.env1.id,))
        self.assertEquals(response.status_code, 200)
        for k in self.env1_data.keys():
            self.assertEqual(
                json.loads(response.content)[k], getattr(self.env1, k))

    def test_env2_post(self):
        response = self.client.post('/api/v1/environment/',
                                    data=json.dumps(self.env2_data),
                                    content_type='application/json')
        self.assertEquals(response.status_code, 201)
        response = self.client.get('/api/v1/environment/3/')
        for k, v in self.env2_data.items():
            self.assertEqual(
                json.loads(response.content)[k], v)

    def test_env2_put(self):
        modified_data = copy.deepcopy(self.env2_data)
        modified_data['name'] = "env2.2"
        modified_data['memory'] = "128kB"
        response = self.client.put('/api/v1/environment/3/',
                                    data=json.dumps(modified_data),
                                    content_type='application/json')
        self.assertEquals(response.status_code, 201)
        response = self.client.get('/api/v1/environment/3/')
        for k, v in modified_data.items():
            self.assertEqual(
                json.loads(response.content)[k], v)

    def test_env2_delete(self):
        response = self.client.delete('/api/v1/environment/3/',
                                    content_type='application/json')
        self.assertEquals(response.status_code, 410)

        response = self.client.get('/api/v1/environment/3/')
        self.assertEquals(response.status_code, 410)

#def suite():
#    suite = unittest.TestSuite()
#    suite.addTest(EnvironmentTest())
#    return suite


class UserTest(FixtureTestCase):
    """Test api user related stuff
    """
    def setUp(self):
        self.api_user = User.objects.create_user(
            'api', 'api@null.com', 'password')
        self.api_user.save()

    def test_has_apikey(self):
        self.assertTrue(hasattr(self.api_user, 'api_key'))

