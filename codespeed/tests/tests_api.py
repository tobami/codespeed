# -*- coding: utf-8 -*-

"""
Tests related to RESTful API
"""

from datetime import datetime
import copy, json
import unittest

from django import test
from django.test.client import Client
from django.http import HttpRequest
from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib.auth.models import User
from tastypie.models import ApiKey, create_api_key
from tastypie.http import HttpUnauthorized
from tastypie.authentication import Authentication, ApiKeyAuthentication
from codespeed.models import (Project, Benchmark, Revision, Branch,
                              Executable, Environment, Result, Report)
from codespeed import settings as default_settings


class FixtureTestCase(test.TestCase):
    fixtures = ["gettimeline_unittest.json"]

    def setUp(self):
        self.api_user = User.objects.create_user(
            username='apiuser', email='api@foo.bar', password='password')
        self.api_user.save()


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
        super(EnvironmentTest, self).setUp()

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


class UserTest(FixtureTestCase):
    """Test api user related stuff
    """

    def test_has_apikey(self):
        self.assertTrue(hasattr(self.api_user, 'api_key'))


class ApiKeyAuthenticationTestCase(FixtureTestCase):

    def setUp(self):
        super(ApiKeyAuthenticationTestCase, self).setUp()
        ApiKey.objects.all().delete()

    def test_is_authenticated(self):
        auth = ApiKeyAuthentication()
        request = HttpRequest()

        # Simulate sending the signal.
        user = User.objects.get(username='apiuser')
        create_api_key(User, instance=user, created=True)

        # No username/api_key details should fail.
        self.assertEqual(isinstance(auth.is_authenticated(request), HttpUnauthorized), True)

        # Wrong username details.
        request.GET['username'] = 'foo'
        self.assertEqual(isinstance(auth.is_authenticated(request), HttpUnauthorized), True)

        # No api_key.
        request.GET['username'] = 'daniel'
        self.assertEqual(isinstance(auth.is_authenticated(request), HttpUnauthorized), True)

        # Wrong user/api_key.
        request.GET['username'] = 'daniel'
        request.GET['api_key'] = 'foo'
        self.assertEqual(isinstance(auth.is_authenticated(request), HttpUnauthorized), True)

        # Correct user/api_key.
        user = User.objects.get(username='apiuser')
        request.GET['username'] = 'apiuser'
        request.GET['api_key'] = user.api_key.key
        self.assertEqual(auth.is_authenticated(request), True)


#def suite():
#    suite = unittest.TestSuite()
#    suite.addTest(EnvironmentTest())
#    return suite


