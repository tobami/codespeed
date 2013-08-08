# -*- coding: utf-8 -*-

"""
Tests related to RESTful API
"""
from datetime import datetime
import copy
import json
import logging
import unittest

from django import test
from django.db.utils import IntegrityError
from django.test.client import Client
from django.http import HttpRequest
from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib.auth.models import User, Permission
from tastypie.authorization import (Authorization, ReadOnlyAuthorization,
                                    DjangoAuthorization)
from tastypie.exceptions import ImmediateHttpResponse, Unauthorized
from tastypie.models import ApiKey, create_api_key
from tastypie.http import HttpUnauthorized
from tastypie.authentication import ApiKeyAuthentication

from codespeed.api import EnvironmentResource, ProjectResource
from codespeed.models import (Project, Benchmark, Revision, Branch,
                              Executable, Environment, Result, Report)
from codespeed.api import ResultBundle
from codespeed import settings as default_settings


class FixtureTestCase(test.TestCase):
    fixtures = ["gettimeline_unittest.json"]

    def setUp(self):
        self.api_user = User.objects.create_user(
            username='apiuser', email='api@foo.bar', password='password')
        self.api_user.save()
        self.api_user.user_permissions.clear()
        john_doe = User.objects.create_user(
            username='johndoe', email='api@foo.bar', password='password')
        john_doe.save()
        authorization = 'ApiKey {0}:{1}'.format(self.api_user.username,
                                                self.api_user.api_key.key)
        self.post_auth = {'HTTP_AUTHORIZATION': authorization}

    def generic_test_authorized(self, method, request, function_list, function_detail):
        bundle = self.resource.build_bundle(request=request)
        bundle.request.method = method
        self.assertTrue(function_detail(self.resource.get_object_list(bundle.request)[0],
            bundle))

    def generic_test_unauthorized(self, method, request, function_list, function_detail):
        bundle = self.resource.build_bundle(request=request)
        bundle.request.method = method
        self.assertRaises(Unauthorized, function_detail,
            self.resource.get_object_list(bundle.request)[0], bundle)




class ApiKeyAuthenticationTestCase(FixtureTestCase):

    def setUp(self):
        super(ApiKeyAuthenticationTestCase, self).setUp()
        ApiKey.objects.all().delete()
        self.auth = ApiKeyAuthentication()
        self.request = HttpRequest()

        # Simulate sending the signal.
        user = User.objects.get(username='apiuser')
        create_api_key(User, instance=user, created=True)

    def test_is_not_authenticated(self):
        """Should return HttpUnauthorized when incorrect credentials are given"""
        # No username/api_key details
        self.assertEqual(isinstance(
            self.auth.is_authenticated(self.request), HttpUnauthorized), True)

        # Wrong username details.
        self.request.GET['username'] = 'foo'
        self.assertEqual(isinstance(
            self.auth.is_authenticated(self.request), HttpUnauthorized), True)

        # No api_key.
        self.request.GET['username'] = 'daniel'
        self.assertEqual(isinstance(
            self.auth.is_authenticated(self.request), HttpUnauthorized), True)

        # Wrong user/api_key.
        self.request.GET['username'] = 'daniel'
        self.request.GET['api_key'] = 'foo'
        self.assertEqual(isinstance(
            self.auth.is_authenticated(self.request), HttpUnauthorized), True)

    def test_is_authenticated(self):
        """Should correctly authenticate when using an existing user and key"""
        # Correct user/api_key.
        user = User.objects.get(username='apiuser')
        self.request.GET['username'] = 'apiuser'
        self.request.GET['api_key'] = user.api_key.key
        self.assertEqual(self.auth.is_authenticated(self.request), True)


class UserTest(FixtureTestCase):
    """Test api user related stuff"""

    def test_has_apikey(self):
        """User() should have an api key attr that was generated automatically."""
        self.assertTrue(hasattr(self.api_user, 'api_key'))

    def test_len_apikey(self):
        """Should have api user key with a non-zero length."""
        self.assertTrue(len(self.api_user.api_key.key) >= 1)

    def test_is_authenticated_header(self):
        """Taken from tastypie test suite to ensure api key is generated for
        new users correctly and tastypie is installed correctly.
        """
        auth = ApiKeyAuthentication()
        request = HttpRequest()

        # Simulate sending the signal.
        john_doe = User.objects.get(username='johndoe')

        # No username/api_key details should fail.
        self.assertEqual(isinstance(auth.is_authenticated(request), HttpUnauthorized), True)

        # Wrong username details.
        request.META['HTTP_AUTHORIZATION'] = 'foo'
        self.assertEqual(isinstance(auth.is_authenticated(request), HttpUnauthorized), True)

        # No api_key.
        request.META['HTTP_AUTHORIZATION'] = 'ApiKey daniel'
        self.assertEqual(isinstance(auth.is_authenticated(request), HttpUnauthorized), True)

        # Wrong user/api_key.
        request.META['HTTP_AUTHORIZATION'] = 'ApiKey daniel:pass'
        self.assertEqual(isinstance(auth.is_authenticated(request), HttpUnauthorized), True)

        # Correct user/api_key.
        john_doe = User.objects.get(username='johndoe')
        request.META['HTTP_AUTHORIZATION'] = 'ApiKey johndoe:%s' % john_doe.api_key.key
        self.assertEqual(auth.is_authenticated(request), True)

        # Capitalization shouldn't matter.
        john_doe = User.objects.get(username='johndoe')
        request.META['HTTP_AUTHORIZATION'] = 'aPiKeY johndoe:%s' % john_doe.api_key.key
        self.assertEqual(auth.is_authenticated(request), True)

    def test_api_key(self):
        """User should be authenticated by it's api key."""
        auth = ApiKeyAuthentication()
        request = HttpRequest()
        authorization = 'ApiKey %s:%s' % (self.api_user.username,
                                          self.api_user.api_key.key)
        request.META['HTTP_AUTHORIZATION'] = authorization
        self.assertEqual(auth.is_authenticated(request), True)


class EnvironmentDjangoAuthorizationTestCase(FixtureTestCase):
    """Test Environment() API"""

    def setUp(self):
        super(EnvironmentDjangoAuthorizationTestCase, self).setUp()
        self.add = Permission.objects.get_by_natural_key(
            'add_environment', 'codespeed', 'environment')
        self.change = Permission.objects.get_by_natural_key(
            'change_environment', 'codespeed', 'environment')
        self.delete = Permission.objects.get_by_natural_key(
            'delete_environment', 'codespeed', 'environment')
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
        env_db1 = Environment.objects.get(id=1)
        self.env_db1_data = dict(
            [(k, getattr(env_db1, k)) for k in self.env1_data.keys()]
        )
        self.client = Client()
        self.resource = EnvironmentResource()
        self.auth = self.resource._meta.authorization

    def test_no_perms(self):
        """User() should have only GET permission"""
        # sanity check: user has no permissions
        self.assertFalse(self.api_user.get_all_permissions())

        request = HttpRequest()
        request.method = 'GET'
        request.user = self.api_user


        # with no permissions, api is read-only
        self.generic_test_authorized('GET',request, self.auth.read_list,
            self.auth.read_detail)

        for method, function_list, function_detail in \
        (('POST',self.auth.create_list, self.auth.create_detail),
         ('PUT',self.auth.update_list, self.auth.update_detail), 
         ('DELETE',self.auth.delete_list, self.auth.delete_detail)):
            self.generic_test_unauthorized(method, request, function_list,
                                           function_detail)

    def test_add_perm(self):
        """User() should have add permission granted."""
        request = HttpRequest()
        request.user = self.api_user

        # give add permission
        request.user.user_permissions.add(self.add)

        self.generic_test_authorized('POST',request, self.auth.create_list,
            self.auth.create_detail)

    def test_change_perm(self):
        """User() should have change permission granted."""
        request = HttpRequest()
        request.user = self.api_user

        # give change permission
        request.user.user_permissions.add(self.change)

        self.generic_test_authorized('PUT',request, self.auth.update_list,
            self.auth.update_detail)

    def test_delete_perm(self):
        """User() should have delete permission granted."""
        request = HttpRequest()
        request.user = self.api_user

        # give delete permission
        request.user.user_permissions.add(self.delete)
        
        self.generic_test_authorized('DELETE',request, self.auth.delete_list,
            self.auth.delete_detail)

    def test_all(self):
        """User() should have add, change, delete permissions granted."""
        request = HttpRequest()
        request.user = self.api_user

        request.user.user_permissions.add(self.add)
        request.user.user_permissions.add(self.change)
        request.user.user_permissions.add(self.delete)

        for method, function_list, function_detail in \
        (('GET',self.auth.read_list, self.auth.read_detail),
         ('OPTIONS',self.auth.read_list, self.auth.read_detail),
         ('HEAD',self.auth.read_list, self.auth.read_detail),
         ('POST',self.auth.create_list, self.auth.create_detail),
         ('PUT',self.auth.update_list, self.auth.update_detail), 
         ('PATCH',self.auth.read_list, self.auth.read_detail), 
         ('PATCH',self.auth.update_list, self.auth.update_detail), 
         ('PATCH',self.auth.delete_list, self.auth.delete_detail), 
         ('DELETE',self.auth.delete_list, self.auth.delete_detail)):
            self.generic_test_authorized(method, request, function_list,
                                           function_detail)


    def test_patch_perms(self):
        """User() should have patch (add, change, delete) permissions granted."""
        request = HttpRequest()
        request.user = self.api_user
        request.method = 'PATCH'

        # Not enough.
        request.user.user_permissions.add(self.add)
        self.generic_test_unauthorized('PATCH', request, self.auth.update_list,
            self.auth.update_detail)
        self.generic_test_unauthorized('PATCH', request, self.auth.delete_list,
            self.auth.delete_detail)

        # Still not enough.
        request.user.user_permissions.add(self.change)
        self.generic_test_unauthorized('PATCH', request, self.auth.delete_list,
            self.auth.delete_detail)

        # Much better.
        request.user.user_permissions.add(self.delete)
        # Nuke the perm cache. :/
        del request.user._perm_cache
        self.generic_test_authorized('PATCH', request, self.auth.delete_list,
            self.auth.delete_detail)

    def test_unrecognized_method(self):
        """User() should not have the permission to call non-existent method."""
        request = HttpRequest()
        self.api_user.user_permissions.clear()
        request.user = self.api_user

        # Check a non-existent HTTP method.
        request.method = 'EXPLODE'
        self.generic_test_unauthorized('EXPLODE', request, self.auth.update_list,
            self.auth.update_detail)

    def test_get_environment(self):
        """Should get an environment when given an existing ID"""
        response = self.client.get(
            '/api/v1/environment/1/?username={0}&api_key={1}'.format(
                self.api_user.username, self.api_user.api_key.key))
        self.assertEquals(response.status_code, 200)
        self.assertEqual(json.loads(response.content)['name'], "Dual Core")

    def test_get_non_existing_environment(self):
        """Should return 404 when given a non existing environment ID"""
        response = self.client.get(
            '/api/v1/environment/999/?username={0}&api_key={1}'.format(
                self.api_user.username, self.api_user.api_key.key))
        self.assertEquals(response.status_code, 404)

    def test_get_environment_all_fields(self):
        """Should get all fields for an environment"""
        response = self.client.get(
            '/api/v1/environment/{0}/?username={1}&api_key={2}'.format(
                self.env1.pk, self.api_user.username, self.api_user.api_key.key)
        )
        self.assertEquals(response.status_code, 200)
        for k in self.env1_data.keys():
            self.assertEqual(
                json.loads(response.content)[k], getattr(self.env1, k))

    def test_post(self):
        """Should save a new environment"""
        request = HttpRequest()
        request.user = self.api_user

        request.user.user_permissions.add(self.add)
        request.user.user_permissions.add(self.change)
        request.user.user_permissions.add(self.delete)

        response = self.client.post('/api/v1/environment/',
                                    data=json.dumps(self.env2_data),
                                    content_type='application/json')
        self.assertEquals(response.status_code, 401)
        response = self.client.post('/api/v1/environment/',
                                    data=json.dumps(self.env2_data),
                                    content_type='application/json',
                                    **self.post_auth)
        self.assertEquals(response.status_code, 201)
        id = response['Location'].rsplit('/', 2)[-2]
        #response = self.client.get('/api/v1/environment/{0}/'.format(id))
        response = self.client.get(
            '/api/v1/environment/{0}/?username={1}&api_key={2}'.format(
                id, self.api_user.username, self.api_user.api_key.key)
        )
        for k, v in self.env2_data.items():
            self.assertEqual(
                json.loads(response.content)[k], v)
        response = self.client.delete('/api/v1/environment/{0}/'.format(id),
                                    content_type='application/json',
                                    **self.post_auth)
        self.assertEquals(response.status_code, 204)

    def test_put(self):
        """Should modify an existing environment"""
        modified_data = copy.deepcopy(self.env_db1_data)
        modified_data['name'] = "env2.2"
        modified_data['memory'] = "128kB"
        response = self.client.put('/api/v1/environment/1/',
                                   data=json.dumps(modified_data),
                                   content_type='application/json',
                                   **self.post_auth)
        self.assertEquals(response.status_code, 401)

        request = HttpRequest()
        request.user = self.api_user
        request.user.user_permissions.add(self.change)

        response = self.client.put('/api/v1/environment/1/',
                                   data=json.dumps(modified_data),
                                   content_type='application/json',
                                   **self.post_auth)
        self.assertEquals(response.status_code, 204)
        response = self.client.get('/api/v1/environment/1/')
        response = self.client.get(
            '/api/v1/environment/1/?username={0}&api_key={1}'.format(
                self.api_user.username, self.api_user.api_key.key)
        )
        for k, v in modified_data.items():
            self.assertEqual(
                json.loads(response.content)[k], v)

    def test_delete(self):
        """Should delete an environment"""
        response = self.client.get(
            '/api/v1/environment/1/?username={0}&api_key={1}'.format(
                self.api_user.username, self.api_user.api_key.key))
        self.assertEquals(response.status_code, 200)
        # from fixture
        response = self.client.delete('/api/v1/environment/1/',
                                      content_type='application/json',
                                      **self.post_auth)
        self.assertEquals(response.status_code, 401)

        request = HttpRequest()
        request.user = self.api_user
        request.user.user_permissions.add(self.delete)
        response = self.client.delete('/api/v1/environment/1/',
                                      content_type='application/json',
                                      **self.post_auth)
        self.assertEquals(response.status_code, 204)

        response = self.client.get(
            '/api/v1/environment/1/?username={0}&api_key={1}'.format(
                self.api_user.username, self.api_user.api_key.key))
        self.assertEquals(response.status_code, 404)

        # from just created data
        response = self.client.get(
            '/api/v1/environment/{0}/?username={1}&api_key={2}'.format(
                self.env1.pk, self.api_user.username, self.api_user.api_key.key)
        )
        self.assertEquals(response.status_code, 200)
        response = self.client.delete(
            '/api/v1/environment/{0}/'.format(self.env1.id),
            content_type='application/json',
            **self.post_auth
        )
        self.assertEquals(response.status_code, 204)

        response = self.client.get(
            '/api/v1/environment/{0}/?username={1}&api_key={2}'.format(
                self.env1.pk, self.api_user.username, self.api_user.api_key.key)
        )
        self.assertEquals(response.status_code, 404)


class ProjectTest(FixtureTestCase):
    """Test Project() API"""

    def setUp(self):
        super(ProjectTest, self).setUp()
        self.add = Permission.objects.get_by_natural_key(
            'add_project', 'codespeed', 'project')
        self.change = Permission.objects.get_by_natural_key(
            'change_project', 'codespeed', 'project')
        self.delete = Permission.objects.get_by_natural_key(
            'delete_project', 'codespeed', 'project')
        self.project_data = dict(
            name="PyPy",
            repo_type="M",
            repo_path="ssh://hg@bitbucket.org/pypy/pypy",
            repo_user="fridolin",
            repo_pass="secret",
        )
        self.project_data2 = dict(
            name="project alpha",
            repo_type="M",
            repo_path="ssh://hg@bitbucket.org/pypy/pypy",
            repo_user="alpha",
            repo_pass="beta",
            )
        self.project = Project(**self.project_data)
        self.project.save()
        self.client = Client()
        self.resource = ProjectResource()
        self.auth = self.resource._meta.authorization

    def test_all(self):
        """User should have all permissions granted."""
        request = HttpRequest()
        request.user = self.api_user

        request.user.user_permissions.add(self.add)
        request.user.user_permissions.add(self.change)
        request.user.user_permissions.add(self.delete)

        for method, function_list, function_detail in \
        (('GET',self.auth.read_list, self.auth.read_detail),
         ('OPTIONS',self.auth.read_list, self.auth.read_detail),
         ('HEAD',self.auth.read_list, self.auth.read_detail),
         ('POST',self.auth.create_list, self.auth.create_detail),
         ('PUT',self.auth.update_list, self.auth.update_detail), 
         ('PATCH',self.auth.read_list, self.auth.read_detail), 
         ('PATCH',self.auth.update_list, self.auth.update_detail), 
         ('PATCH',self.auth.delete_list, self.auth.delete_detail), 
         ('DELETE',self.auth.delete_list, self.auth.delete_detail)):
            self.generic_test_authorized(method, request, function_list,
                                           function_detail)
    def test_get_project(self):
        """Should get an existing project"""
        response = self.client.get('/api/v1/project/{0}/'.format(
            self.project.id,))
        self.assertEquals(response.status_code, 200)
        self.assertEqual(json.loads(response.content)['name'], "{0}".format(
            self.project_data['name']))

    def test_get_project_all_fields(self):
        """Should get all fields for a project"""
        response = self.client.get('/api/v1/project/%s/' % (self.project.id,))
        self.assertEquals(response.status_code, 200)
        for k in self.project_data.keys():
            self.assertEqual(
                json.loads(response.content)[k], getattr(self.project, k))

    def test_post(self):
        """Should save a new project"""
        request = HttpRequest()
        request.user = self.api_user

        request.user.user_permissions.add(self.add)
        request.user.user_permissions.add(self.change)
        request.user.user_permissions.add(self.delete)

        response = self.client.post('/api/v1/project/',
                                    data=json.dumps(self.project_data2),
                                    content_type='application/json')
        self.assertEquals(response.status_code, 401)
        response = self.client.post('/api/v1/project/',
                                    data=json.dumps(self.project_data2),
                                    content_type='application/json',
                                    **self.post_auth)
        self.assertEquals(response.status_code, 201)
        id = response['Location'].rsplit('/', 2)[-2]
        response = self.client.get(
            '/api/v1/project/{0}/?username={1}&api_key={2}'.format(
                self.project.id, self.api_user.username, self.api_user.api_key.key)
        )
        for k, v in self.project_data.items():
            self.assertEqual(
                json.loads(response.content)[k], v)

    def test_delete(self):
        """Should delete an project"""
        response = self.client.delete('/api/v1/project/{0}/'.format(
            self.project.id,), content_type='application/json')
        self.assertEquals(response.status_code, 401)

        request = HttpRequest()
        request.user = self.api_user
        request.user.user_permissions.add(self.delete)
        response = self.client.delete(
            '/api/v1/project/{0}/'.format(self.project.id,),
            content_type='application/json',
            **self.post_auth
        )
        self.assertEquals(response.status_code, 204)
        response = self.client.get('/api/v1/project/{0}/'.format(
            self.project.id,)
        )
        self.assertEquals(response.status_code, 404)


class ExecutableTest(FixtureTestCase):
    """Test Executable() API"""

    def setUp(self):
        self.data = dict(name="Fibo", description="Fibonacci the Lame",)
        # project is a ForeignKey and is not added automatically by tastypie
        self.project = Project.objects.get(pk=1)
        self.executable = Executable(project=self.project, **self.data)
        self.executable.save()
        self.client = Client()
        super(ExecutableTest, self).setUp()

    def test_get_executable(self):
        """Should get an existing executable"""
        response = self.client.get('/api/v1/executable/{0}/'.format(
            self.executable.id,))
        self.assertEquals(response.status_code, 200)
        self.assertEqual(json.loads(response.content)['name'], "{0}".format(
            self.data['name']))

    def test_get_executable_all_fields(self):
        """Should get all fields for an executable"""
        response = self.client.get('/api/v1/executable/%s/' % (
            self.executable.id,))
        self.assertEquals(response.status_code, 200)
        for k in self.data.keys():
            self.assertEqual(
                json.loads(response.content)[k], self.data[k])

    def test_post(self):
        """Should save a new executable"""
        modified_data = copy.deepcopy(self.data)
        modified_data['name'] = 'nbody'
        modified_data['project'] = '/api/v1/project/{0}/'.format(self.project.pk)
        response = self.client.post('/api/v1/executable/',
                                    data=json.dumps(modified_data),
                                    content_type='application/json')
        self.assertEquals(response.status_code, 201)
        response = self.client.get('/api/v1/executable/{0}/'.format(
            self.executable.id))
        response_data = json.loads(response.content)
        for k, v in self.data.items():
            self.assertEqual(response_data[k], v)
        executable = Executable.objects.get(pk=int(response_data['id']))
        self.assertEquals(executable.project, self.project)

    def test_delete(self):
        """Should delete an project"""
        response = self.client.delete('/api/v1/executable/{0}/'.format(
            self.executable.id,), content_type='application/json')
        self.assertEquals(response.status_code, 204)

        response = self.client.get('/api/v1/executable/{0}/'.format(
            self.executable.id,))

    def test_nonexistent(self):
        """Requesting an environment that doesn't exist should return a 404"""
        response = self.client.get('/api/v1/environment/3333333/')
        self.assertEquals(response.status_code, 404)


class BranchTest(FixtureTestCase):
    """Test Branch() API"""

    def setUp(self):
        super(BranchTest, self).setUp()
        self.add = Permission.objects.get_by_natural_key(
            'add_branch', 'codespeed', 'branch')
        self.change = Permission.objects.get_by_natural_key(
            'change_branch', 'codespeed', 'branch')
        self.delete = Permission.objects.get_by_natural_key(
            'delete_branch', 'codespeed', 'branch')
        self.branch1 = Branch.objects.get(pk=1)
        self.project_data = dict(
            name="PyPy",
            repo_type="M",
            repo_path="ssh://hg@bitbucket.org/pypy/pypy",
            repo_user="fridolin",
            repo_pass="secret",
            )
        self.project = Project(**self.project_data)
        self.project.save()
        self.branch2_data = dict(
            name="master2",
            project='/api/v1/project/{0}/'.format(self.project.id)
        )
        self.client = Client()

    def test_get_branch(self):
        """Should get an existing branch"""
        response = self.client.get('/api/v1/branch/1/')
        self.assertEquals(response.status_code, 200)
        self.assertEqual(json.loads(response.content)['name'], "default")
        self.assertEqual(json.loads(response.content)['project'],
                         "/api/v1/project/1/")

    def test_get_branch_all_fields(self):
        """Should get all fields for an branch"""
        response = self.client.get('/api/v1/branch/%s/' % (self.branch1.id,))
        self.assertEquals(response.status_code, 200)
        self.assertEquals(json.loads(response.content)['name'],
                          self.branch1.name)
        self.assertEquals(json.loads(response.content)['project'],
                          '/api/v1/project/1/')
        self.assertEquals(json.loads(response.content)['resource_uri'],
                          '/api/v1/branch/%s/' % (self.branch1.id,))

    def test_post(self):
        """Should save a new branch"""
        request = HttpRequest()
        request.user = self.api_user

        request.user.user_permissions.add(self.add)
        request.user.user_permissions.add(self.delete)

        modified_data = copy.deepcopy(self.branch2_data)
        response = self.client.post('/api/v1/branch/',
                                    data=json.dumps(modified_data),
                                    content_type='application/json')
        self.assertEquals(response.status_code, 401)
        response = self.client.post('/api/v1/branch/',
                                    data=json.dumps(modified_data),
                                    content_type='application/json',
                                    **self.post_auth)
        self.assertEquals(response.status_code, 201)
        id = response['Location'].rsplit('/', 2)[-2]
        response = self.client.get('/api/v1/branch/{0}/'.format(id))
        for k, v in self.branch2_data.items():
            self.assertEqual(
                json.loads(response.content)[k], v)
        response = self.client.delete('/api/v1/branch/{0}/'.format(id),
                                      content_type='application/json',
                                      **self.post_auth)
        self.assertEquals(response.status_code, 204)

    def test_put(self):
        """Should modify an existing environment"""
        request = HttpRequest()
        request.user = self.api_user
        request.user.user_permissions.add(self.change)

        modified_data = copy.deepcopy(self.branch2_data)
        modified_data['name'] = "tip"
        response = self.client.put('/api/v1/branch/1/',
                                   data=json.dumps(modified_data),
                                   content_type='application/json')
        self.assertEquals(response.status_code, 401)
        response = self.client.put('/api/v1/branch/1/',
                                   data=json.dumps(modified_data),
                                   content_type='application/json',
                                   **self.post_auth)
        self.assertEquals(response.status_code, 204)
        response = self.client.get('/api/v1/branch/1/')
        for k, v in modified_data.items():
            self.assertEqual(
                json.loads(response.content)[k], v)

    def test_delete(self):
        """Should delete a branch"""
        request = HttpRequest()
        request.user = self.api_user
        request.user.user_permissions.add(self.delete)

        response = self.client.get('/api/v1/branch/1/')
        self.assertEquals(response.status_code, 200)
        # from fixture
        response = self.client.delete('/api/v1/branch/1/',
                                      content_type='application/json')
        self.assertEquals(response.status_code, 401)
        response = self.client.delete('/api/v1/branch/1/',
                                      content_type='application/json',
                                      **self.post_auth)
        self.assertEquals(response.status_code, 204)

        response = self.client.get('/api/v1/branch/1/')
        self.assertEquals(response.status_code, 404)


class RevisionTest(FixtureTestCase):
    """Test Revision() API"""

    def setUp(self):
        super(RevisionTest, self).setUp()
        self.add = Permission.objects.get_by_natural_key(
            'add_revision', 'codespeed', 'revision')
        self.change = Permission.objects.get_by_natural_key(
            'change_revision', 'codespeed', 'revision')
        self.delete = Permission.objects.get_by_natural_key(
            'delete_revision', 'codespeed', 'revision')
        DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S'
        self.branch1 = Branch.objects.get(pk=1)
        self.project1 = Project.objects.get(pk=1)
        self.revision1_data = dict(
            commitid="2a6306432e973cdcfd324e81169bb8029d47b736",
            tag="tag",
            date=datetime.now(),
            message="Commit message\n  - all bugs fixed\n  - code 130% faster",
            project=self.project1,
            author="Alan T. <alan@localhost>",
            branch=self.branch1,
        )
        self.revision1 = Revision(**self.revision1_data)
        self.revision1.save()
        self.revision2_data = dict(
            commitid="4d3bea3cffe4edcd7d70fc46c5e19474cc4bd012",
            tag="v1.0",
            date=datetime.now().strftime(DATETIME_FORMAT),
            message="Commit message\n  - cleanup\n  - all FIXMEs removed",
            project='/api/v1/project/{0}/'.format(self.project1.id),
            author="Chuck N. <chuck@localhost>",
            branch='/api/v1/branch/{0}/'.format(self.branch1.id),
        )
        self.client = Client()

    def test_get_revision(self):
        """Should get an existing revision"""
        response = self.client.get('/api/v1/revision/1/')
        self.assertEquals(response.status_code, 200)
        self.assertEqual(json.loads(response.content)['commitid'], "1")
        self.assertEqual(json.loads(response.content)['project'],
                         "/api/v1/project/1/")

    def test_get_revision_all_fields(self):
        """Should get all fields for a revision"""
        response = self.client.get('/api/v1/revision/%s/' % (self.revision1.id,))
        self.assertEquals(response.status_code, 200)
        self.assertEquals(json.loads(response.content)['commitid'],
                          self.revision1.commitid)
        self.assertEquals(json.loads(response.content)['project'],
                          '/api/v1/project/%s/' % (self.project1.pk))
        self.assertEquals(json.loads(response.content)['branch'],
                          '/api/v1/branch/%s/' % (self.branch1.pk))
        self.assertEquals(json.loads(response.content)['tag'],
                          self.revision1_data['tag'])
        self.assertEquals(json.loads(response.content)['message'],
                          self.revision1_data['message'])

    def test_post(self):
        """Should save a new revision"""
        request = HttpRequest()
        request.user = self.api_user

        request.user.user_permissions.add(self.add)
        request.user.user_permissions.add(self.change)
        request.user.user_permissions.add(self.delete)

        modified_data = copy.deepcopy(self.revision2_data)
        response = self.client.post('/api/v1/revision/',
                                    data=json.dumps(modified_data),
                                    content_type='application/json')
        self.assertEquals(response.status_code, 401)
        response = self.client.post('/api/v1/revision/',
                                    data=json.dumps(modified_data),
                                    content_type='application/json',
                                    **self.post_auth)
        self.assertEquals(response.status_code, 201)
        id = response['Location'].rsplit('/', 2)[-2]
        response = self.client.get('/api/v1/revision/{0}/'.format(id))
        for k, v in self.revision2_data.items():
            self.assertEqual(
                json.loads(response.content)[k], v)
        response = self.client.delete('/api/v1/revision/{0}/'.format(id),
                                      content_type='application/json',
                                      **self.post_auth)
        self.assertEquals(response.status_code, 204)

    def test_put(self):
        """Should modify an existing revision"""
        request = HttpRequest()
        request.user = self.api_user

        request.user.user_permissions.add(self.add)
        request.user.user_permissions.add(self.change)
        request.user.user_permissions.add(self.delete)

        modified_data = copy.deepcopy(self.revision2_data)
        modified_data['tag'] = "v0.9.1"
        response = self.client.put('/api/v1/revision/1/',
                                   data=json.dumps(modified_data),
                                   content_type='application/json')
        self.assertEquals(response.status_code, 401)
        response = self.client.put('/api/v1/revision/1/',
                                   data=json.dumps(modified_data),
                                   content_type='application/json',
                                   **self.post_auth)
        self.assertEquals(response.status_code, 204)
        response = self.client.get('/api/v1/revision/1/')
        for k, v in modified_data.items():
            self.assertEqual(
                json.loads(response.content)[k], v)

    def test_delete(self):
        """Should delete a revision"""
        request = HttpRequest()
        request.user = self.api_user

        request.user.user_permissions.add(self.delete)

        response = self.client.get('/api/v1/revision/1/')
        self.assertEquals(response.status_code, 200)
        # from fixture
        response = self.client.delete('/api/v1/revision/1/',
                                      content_type='application/json')
        self.assertEquals(response.status_code, 401)
        response = self.client.delete('/api/v1/revision/1/',
                                      content_type='application/json',
                                      **self.post_auth)
        self.assertEquals(response.status_code, 204)

        response = self.client.get('/api/v1/revision/1/')
        self.assertEquals(response.status_code, 404)


class ExecutableTest(FixtureTestCase):
    """Test Executable() API"""

    def setUp(self):
        super(ExecutableTest, self).setUp()

        self.add = Permission.objects.get_by_natural_key(
            'add_executable', 'codespeed', 'executable')
        self.change = Permission.objects.get_by_natural_key(
            'change_executable', 'codespeed', 'executable')
        self.delete = Permission.objects.get_by_natural_key(
            'delete_executable', 'codespeed', 'executable')

        self.executable1 = Executable.objects.get(pk=1)
        self.project1 = Project.objects.get(pk=1)
        self.executable2_data = dict(
            name="sleep",
            description="Sleep benchmark",
            project='/api/v1/project/{0}/'.format(self.project1.id),
        )
        self.client = Client()

    def test_get_executable(self):
        """Should get an existing executable"""
        response = self.client.get('/api/v1/executable/1/')
        self.assertEquals(response.status_code, 200)
        self.assertEqual(json.loads(response.content)['name'],
                         'myexe O3 64bits')
        self.assertEqual(json.loads(response.content)['project'],
                         "/api/v1/project/1/")

    def test_get_executable_all_fields(self):
        """Should get all fields for an executable"""
        response = self.client.get('/api/v1/executable/{0}/'.format(
            self.executable1.id,))
        self.assertEquals(response.status_code, 200)
        self.assertEquals(json.loads(response.content)['name'],
                          self.executable1.name)
        self.assertEquals(json.loads(response.content)['project'],
                          '/api/v1/project/%s/' % (self.project1.pk))
        self.assertEquals(json.loads(response.content)['description'],
                          self.executable1.description)

    def test_post(self):
        """Should save a new executable"""
        request = HttpRequest()
        request.user = self.api_user

        request.user.user_permissions.add(self.add)

        modified_data = copy.deepcopy(self.executable2_data)
        response = self.client.post('/api/v1/executable/',
                                    data=json.dumps(modified_data),
                                    content_type='application/json')
        self.assertEquals(response.status_code, 401)
        response = self.client.post('/api/v1/executable/',
                                    data=json.dumps(modified_data),
                                    content_type='application/json',
                                    **self.post_auth)
        self.assertEquals(response.status_code, 201)
        id = response['Location'].rsplit('/', 2)[-2]
        response = self.client.get('/api/v1/executable/{0}/'.format(id))
        for k, v in self.executable2_data.items():
            self.assertEqual(
                json.loads(response.content)[k], v)
        request.user.user_permissions.add(self.delete)
        response = self.client.delete('/api/v1/executable/{0}/'.format(id),
                                      content_type='application/json',
                                      **self.post_auth)
        self.assertEquals(response.status_code, 204)

    def test_put(self):
        """Should modify an existing environment"""
        request = HttpRequest()
        request.user = self.api_user

        request.user.user_permissions.add(self.add)
        request.user.user_permissions.add(self.change)
        request.user.user_permissions.add(self.delete)

        modified_data = copy.deepcopy(self.executable2_data)
        modified_data['name'] = "django"
        response = self.client.put('/api/v1/executable/1/',
                                   data=json.dumps(modified_data),
                                   content_type='application/json')
        self.assertEquals(response.status_code, 401)
        response = self.client.put('/api/v1/executable/1/',
                                   data=json.dumps(modified_data),
                                   content_type='application/json',
                                   **self.post_auth)
        self.assertEquals(response.status_code, 204)
        response = self.client.get('/api/v1/executable/1/')
        for k, v in modified_data.items():
            self.assertEqual(
                json.loads(response.content)[k], v)

    def test_delete(self):
        """Should delete a executable"""
        request = HttpRequest()
        request.user = self.api_user

        request.user.user_permissions.add(self.delete)

        response = self.client.get('/api/v1/executable/1/')
        self.assertEquals(response.status_code, 200)
        # from fixture
        response = self.client.delete('/api/v1/executable/1/',
                                      content_type='application/json')
        self.assertEquals(response.status_code, 401)
        response = self.client.delete('/api/v1/executable/1/',
                                      content_type='application/json',
                                      **self.post_auth)
        self.assertEquals(response.status_code, 204)

        response = self.client.get('/api/v1/executable/1/')
        self.assertEquals(response.status_code, 404)


class BenchmarkTest(FixtureTestCase):
    """Test Benchmark() API"""

    def setUp(self):
        super(BenchmarkTest, self).setUp()
        self.add = Permission.objects.get_by_natural_key(
            'add_benchmark', 'codespeed', 'benchmark')
        self.change = Permission.objects.get_by_natural_key(
            'change_benchmark', 'codespeed', 'benchmark')
        self.delete = Permission.objects.get_by_natural_key(
            'delete_benchmark', 'codespeed', 'benchmark')
        self.benchmark1 = Benchmark.objects.get(pk=1)
        self.benchmark2_data = dict(
            name="sleep",
            benchmark_type='C',
            description='fast faster fastest',
            units_title='Time',
            units='seconds',
            lessisbetter=True,
            default_on_comparison=True,
        )
        self.benchmark2 = Benchmark(**self.benchmark2_data)
        self.benchmark2.save()
        self.client = Client()

    def test_get_benchmark(self):
        """Should get an existing benchmark"""
        response = self.client.get('/api/v1/benchmark/1/')
        self.assertEquals(response.status_code, 200)
        self.assertEqual(json.loads(response.content)['name'],
                         'float')
        self.assertEqual(json.loads(response.content)['units'],
                         "seconds")

    def test_get_benchmark_all_fields(self):
        """Should get all fields for an benchmark"""
        response = self.client.get('/api/v1/benchmark/{0}/'.format(
            self.benchmark2.id,))
        self.assertEquals(response.status_code, 200)
        for k, v in self.benchmark2_data.items():
            self.assertEqual(json.loads(response.content)[k], v)

    def test_post(self):
        """Should save a new benchmark"""
        request = HttpRequest()
        request.user = self.api_user

        request.user.user_permissions.add(self.add)

        modified_data = copy.deepcopy(self.benchmark2_data)
        modified_data['name'] = 'wake'
        response = self.client.post('/api/v1/benchmark/',
                                    data=json.dumps(modified_data),
                                    content_type='application/json')
        self.assertEquals(response.status_code, 401)
        response = self.client.post('/api/v1/benchmark/',
                                    data=json.dumps(modified_data),
                                    content_type='application/json',
                                    **self.post_auth
        )
        self.assertEquals(response.status_code, 201)
        id = response['Location'].rsplit('/', 2)[-2]
        response = self.client.get('/api/v1/benchmark/{0}/'.format(id))
        for k, v in modified_data.items():
            self.assertEqual(
                json.loads(response.content)[k], v)
        request.user.user_permissions.add(self.delete)
        response = self.client.delete('/api/v1/benchmark/{0}/'.format(id),
                                      content_type='application/json',
                                      **self.post_auth)
        self.assertEquals(response.status_code, 204)

    def test_put(self):
        """Should modify an existing benchmark"""
        request = HttpRequest()
        request.user = self.api_user

        request.user.user_permissions.add(self.add)
        request.user.user_permissions.add(self.change)
        request.user.user_permissions.add(self.delete)

        modified_data = copy.deepcopy(self.benchmark2_data)
        modified_data['name'] = "django"
        response = self.client.put('/api/v1/benchmark/1/',
                                   data=json.dumps(modified_data),
                                   content_type='application/json')
        self.assertEquals(response.status_code, 401)
        response = self.client.put('/api/v1/benchmark/1/',
                                   data=json.dumps(modified_data),
                                   content_type='application/json',
                                   **self.post_auth)
        self.assertEquals(response.status_code, 204)
        response = self.client.get('/api/v1/benchmark/1/')
        for k, v in modified_data.items():
            self.assertEqual(
                json.loads(response.content)[k], v)

    def test_delete(self):
        """Should delete a benchmark"""
        request = HttpRequest()
        request.user = self.api_user

        request.user.user_permissions.add(self.delete)
        response = self.client.get('/api/v1/benchmark/1/')
        self.assertEquals(response.status_code, 200)
        # from fixture
        response = self.client.delete('/api/v1/benchmark/1/',
                                      content_type='application/json')
        self.assertEquals(response.status_code, 401)
        response = self.client.delete('/api/v1/benchmark/1/',
                                      content_type='application/json',
                                      **self.post_auth)
        self.assertEquals(response.status_code, 204)

        response = self.client.get('/api/v1/benchmark/1/')
        self.assertEquals(response.status_code, 404)


class ReportTest(FixtureTestCase):
    """Test Report() API"""

    def setUp(self):
        super(ReportTest, self).setUp()
        self.add = Permission.objects.get_by_natural_key(
            'add_report', 'codespeed', 'report')
        self.change = Permission.objects.get_by_natural_key(
            'change_report', 'codespeed', 'report')
        self.delete = Permission.objects.get_by_natural_key(
            'delete_report', 'codespeed', 'report')

        self.report1 = Report.objects.get(pk=1)
        self.revision1 = Revision.objects.get(pk=1)
        self.executable1 = Executable.objects.get(pk=1)
        self.environment1 = Environment.objects.get(pk=1)
        self.executable2_data = dict(
            name="Fibo",
            description="Fibonacci the Lame",
        )
        self.project = Project.objects.get(pk=1)
        self.executable2 = Executable(project=self.project,
                                      **self.executable2_data)
        self.executable2.save()
        self.report2_data = dict(
            revision=self.revision1,
            environment=self.environment1,
            executable=self.executable2,
            )
        self.report2 = Report(**self.report2_data)
        self.report2.save()
        self.report2_data = dict(
            revision='/api/v1/revision/{0}/'.format(self.revision1.id),
            environment='/api/v1/environment/{0}/'.format(self.environment1.id),
            executable='/api/v1/executable/{0}/'.format(self.executable2.id),
            )
        self.client = Client()

    def test_get_report(self):
        """Should get an existing report"""
        response = self.client.get('/api/v1/report/1/')
        self.assertEquals(response.status_code, 200)
        self.assertEqual(json.loads(response.content)['summary'],
                         'float -50.0%')
        self.assertEqual(json.loads(response.content)['colorcode'],
                         "green")

    def test_get_report_all_fields(self):
        """Should get all fields for an report"""
        response = self.client.get('/api/v1/report/{0}/'.format(
            self.report2.id,))
        self.assertEquals(response.status_code, 200)
        for k, v in self.report2_data.items():
            self.assertEqual(json.loads(response.content)[k], v)

    def test_post(self):
        """Should not save a new report"""
        request = HttpRequest()
        request.user = self.api_user

        request.user.user_permissions.add(self.add)

        modified_data = copy.deepcopy(self.report2_data)
        response = self.client.post('/api/v1/report/',
                                    data=json.dumps(modified_data),
                                    content_type='application/json')
        self.assertEquals(response.status_code, 405)
        # next has to be 405 (method not allowed),
        # otherwise would raise IntegrityError
        response = self.client.post('/api/v1/report/',
                                    data=json.dumps(modified_data),
                                    content_type='application/json',
                                    **self.post_auth)
        # next has to be 405, otherwise would raise IntegrityError
        self.assertEquals(response.status_code, 405)

    def test_put(self):
        """Should not modify an existing report"""
        request = HttpRequest()
        request.user = self.api_user

        request.user.user_permissions.add(self.add)
        request.user.user_permissions.add(self.change)
        request.user.user_permissions.add(self.delete)

        modified_data = copy.deepcopy(self.report2_data)
        response = self.client.put('/api/v1/report/1/',
                                   data=json.dumps(modified_data),
                                   content_type='application/json')
        self.assertEquals(response.status_code, 405)
        response = self.client.put('/api/v1/report/1/',
                                   data=json.dumps(modified_data),
                                   content_type='application/json',
                                   **self.post_auth)
        self.assertEquals(response.status_code, 405)

    def test_delete(self):
        """Should delete a report"""
        request = HttpRequest()
        request.user = self.api_user

        request.user.user_permissions.add(self.delete)

        response = self.client.get('/api/v1/report/1/')
        self.assertEquals(response.status_code, 200)
        # from fixture
        response = self.client.delete('/api/v1/report/1/',
                                      content_type='application/json')
        self.assertEquals(response.status_code, 405)
        response = self.client.delete('/api/v1/report/1/',
                                      content_type='application/json',
                                      **self.post_auth)
        self.assertEquals(response.status_code, 405)


class ResultBundleTestCase(FixtureTestCase):
    """Test CRUD of results via API"""

    def setUp(self):
        super(ResultBundleTestCase, self).setUp()
        self.request = HttpRequest()
        self.request.user = self.api_user
        self.data1 = {
            'commitid': '/api/v1/revision/2/',
            'branch': '/api/v1/branch/1/', # Always use default for trunk/master/tip
            'project': '/api/v1/project/2/',
            'executable': '/api/v1/executable/1/',
            'benchmark': '/api/v1/benchmark/1/',
            'environment': '/api/v1/environment/2/',
            'result_value': 4000,
            }
        DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
        self.data_optional = {
            'std_dev': 0.2,
            'val_min': 2.23,
            'val_max': 3.42,
            'date': datetime.now().strftime(DATETIME_FORMAT),
            }
        project_data = dict(
            name="PyPy",
            repo_type="M",
            repo_path="ssh://hg@bitbucket.org/pypy/pypy",
            repo_user="fridolin",
            repo_pass="secret",
            )
        self.project = Project(**project_data)
        self.project.save()
        self.env1 = Environment(name='Bulldozer')
        self.env1.save()

    def test_populate_and_save(self):
        """Should populate ResultBundle() with data"""
        bundle = ResultBundle(request=self.request,**self.data1)
        bundle._populate_obj_by_data()
        # should raise exception if not OK
        bundle.hydrate_and_save()
        self.assert_(True)

    def test_save_same_result_again(self):
        """Save a previously saved result. Expected is an IntegrityError"""
        modified_data = copy.deepcopy(self.data1)
        modified_data['environment'] = '/api/v1/environment/1/'
        modified_data['project'] = '/api/v1/project/1/'
        bundle = ResultBundle(request=self.request,**modified_data)
        bundle._populate_obj_by_data()
        self.assertRaises(IntegrityError, bundle.hydrate_and_save)

    def test_for_nonexistent_environment(self):
        """Save data using non existing environment. Expected is an
        ImmediateHttpResponse
        """
        modified_data = copy.deepcopy(self.data1)
        modified_data['environment'] = '/api/v1/environment/3/'
        self.assertRaises(ImmediateHttpResponse, ResultBundle, **modified_data)

    def test_insufficient_data(self):
        """See if Result() is saved w/ insufficient data"""
        modified_data = copy.deepcopy(self.data1)
        modified_data.pop('environment')
        self.assertRaises(ImmediateHttpResponse, ResultBundle, **modified_data)

    def test_date_attr_set(self):
        """Should add date attr to Result() obj if date is not given"""
        # date is set automatically
        modified_data = copy.deepcopy(self.data1)
        bundle = ResultBundle(request=self.request,**modified_data)
        bundle.hydrate_and_save()
        self.assertIsInstance(bundle.obj.date, datetime)
        # date set by value
        modified_data['date'] = '2011-05-05 03:01:45'
        bundle = ResultBundle(request=self.request,**modified_data)
        # wrong date string
        modified_data['date'] = '2011-05-05T03:01:45'
        self.assertRaises(ImmediateHttpResponse, ResultBundle, **modified_data)

    def test_optional_data(self):
        """Should save optional data."""
        data = dict(self.data1.items() + self.data_optional.items())
        bundle = ResultBundle(request=self.request,**data)
        bundle.hydrate_and_save()
        self.assertIsInstance(bundle.obj.date, datetime)
        self.assertEqual(bundle.obj.std_dev,
                         float(self.data_optional['std_dev']))
        self.assertEqual(bundle.obj.val_max,
                         float(self.data_optional['val_max']))
        self.assertEqual(bundle.obj.val_min,
                         float(self.data_optional['val_min']))


class ResultBundleResourceTestCase(FixtureTestCase):
    """Submitting new benchmark results"""

    DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'

    def setUp(self):
        super(ResultBundleResourceTestCase, self).setUp()

        self.add = Permission.objects.get_by_natural_key(
            'add_result', 'codespeed', 'result')
        self.change = Permission.objects.get_by_natural_key(
            'change_result', 'codespeed', 'result')
        self.delete = Permission.objects.get_by_natural_key(
            'delete_result', 'codespeed', 'result')

        self.data1 = {
            'commitid': '/api/v1/revision/2/',
            'branch': '/api/v1/branch/1/', # Always use default for trunk/master/tip
            'project': '/api/v1/project/2/',
            'executable': '/api/v1/executable/1/',
            'benchmark': '/api/v1/benchmark/1/',
            'environment': '/api/v1/environment/2/',
            'result_value': 4000,
            }
        self.data_optional = {
            'std_dev': 0.2,
            'val_min': 2.23,
            'val_max': 3.42,
            'date': datetime.now().strftime(self.DATETIME_FORMAT),
            }
        project_data = dict(
            name="PyPy",
            repo_type="M",
            repo_path="ssh://hg@bitbucket.org/pypy/pypy",
            repo_user="fridolin",
            repo_pass="secret",
            )
        self.project = Project(**project_data)
        self.project.save()
        self.env1 = Environment(name='Bulldozer')
        self.env1.save()
        self.client = Client()

    def test_post_mandatory(self):
        """Should save a new result with only mandatory data"""
        request = HttpRequest()
        request.user = self.api_user

        request.user.user_permissions.add(self.add)

        response = self.client.post('/api/v1/benchmark-result/',
                                    data=json.dumps(self.data1),
                                    content_type='application/json')
        self.assertEquals(response.status_code, 201)
        id = response['Location'].rsplit('/', 2)[-2]
        result = Result.objects.get(pk=int(id))
        # just to make the point
        self.assertIsInstance(result, Result)
        self.assertEqual(result.value, self.data1['result_value'])

    def test_post_all_data(self):
        """Should save a new result with mandatory and optional data"""
        request = HttpRequest()
        request.user = self.api_user

        request.user.user_permissions.add(self.add)

        data = dict(self.data1, **self.data_optional)
        response = self.client.post('/api/v1/benchmark-result/',
                                    data=json.dumps(data),
                                    content_type='application/json')
        self.assertEquals(response.status_code, 201)

    def test_post_invalid_data(self):
        """Should save a new result with mandatory and optional data"""
        request = HttpRequest()
        request.user = self.api_user

        request.user.user_permissions.add(self.add)

        modified_data = copy.deepcopy(self.data1)
        # environment does not exist
        modified_data['environment'] = '/api/v1/environment/5/'
        response = self.client.post('/api/v1/benchmark-result/',
                                    data=json.dumps(modified_data),
                                    content_type='application/json',
                                    **self.post_auth)
        self.assertEquals(response.status_code, 400)

    def test_get_one(self):
        """Should get a result bundle"""
        response = self.client.get('/api/v1/benchmark-result/1/',
                                    content_type='application/json')
        self.assertEquals(response.status_code, 200)
        response_data = json.loads(response.content)
        for k in ('project', 'result', 'branch', 'benchmark', 'environment',
            'executable', 'revision'):
            self.assertEqual(
                response_data[k],
                '/api/v1/{0}/1/'.format(k,))


#def suite():
#    suite = unittest.TestSuite()
#    suite.addTest(EnvironmentTest())
#    return suite
