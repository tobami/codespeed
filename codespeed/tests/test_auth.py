# -*- coding: utf-8 -*-

import mock

from django.test import TestCase, override_settings
from django.http import HttpResponse
from django.contrib.auth.models import AnonymousUser

from codespeed.auth import basic_auth_required


@override_settings(ALLOW_ANONYMOUS_POST=False)
class AuthModuleTestCase(TestCase):
    @override_settings(ALLOW_ANONYMOUS_POST=True)
    def test_allow_anonymous_post_is_true(self):
        wrapped_function = mock.Mock()
        wrapped_function.__name__ = 'mock'
        wrapped_function.return_value = 'success'

        request = mock.Mock()
        request.user = AnonymousUser()
        request.META = {}

        res = basic_auth_required()(wrapped_function)(request=request)
        self.assertEqual(wrapped_function.call_count, 1)
        self.assertEqual(res, 'success')

    def test_basic_auth_required_django_pre_2_0_succesful_auth(self):
        # request.user.is_authenticated is a method (pre Django 2.0)
        user = mock.Mock()
        user.is_authenticated = lambda: True

        request = mock.Mock()
        request.user = user

        wrapped_function = mock.Mock()
        wrapped_function.__name__ = 'mock'
        wrapped_function.return_value = 'success'

        res = basic_auth_required()(wrapped_function)(request=request)
        self.assertEqual(wrapped_function.call_count, 1)
        self.assertEqual(res, 'success')

    def test_basic_auth_required_django_pre_2_0_failed_auth(self):
        # request.user.is_authenticated is a method (pre Django 2.0)
        user = mock.Mock()
        user.is_authenticated = lambda: False

        request = mock.Mock()
        request.user = user
        request.META = {}

        wrapped_function = mock.Mock()
        wrapped_function.__name__ = 'mock'

        res = basic_auth_required()(wrapped_function)(request=request)
        self.assertTrue(isinstance(res, HttpResponse))
        self.assertEqual(res.status_code, 401)
        self.assertEqual(wrapped_function.call_count, 0)

        # Also test with actual AnonymousUser class which will have different
        # implementation under different Django versions
        request.user = AnonymousUser()

        res = basic_auth_required()(wrapped_function)(request=request)
        self.assertTrue(isinstance(res, HttpResponse))
        self.assertEqual(res.status_code, 401)
        self.assertEqual(wrapped_function.call_count, 0)

    def test_basic_auth_required_django_post_2_0_successful_auth(self):
        # request.user.is_authenticated is a property (post Django 2.0)
        user = mock.Mock()
        user.is_authenticated = True

        request = mock.Mock()
        request.user = user

        wrapped_function = mock.Mock()
        wrapped_function.__name__ = 'mock'
        wrapped_function.return_value = 'success'

        res = basic_auth_required()(wrapped_function)(request=request)
        self.assertEqual(wrapped_function.call_count, 1)
        self.assertEqual(res, 'success')

    def test_basic_auth_required_django_post_2_0_failed_auth(self):
        # request.user.is_authenticated is a property (post Django 2.0)
        user = mock.Mock()
        user.is_authenticated = False

        request = mock.Mock()
        request.user = user
        request.META = {}

        wrapped_function = mock.Mock()
        wrapped_function.__name__ = 'mock'

        res = basic_auth_required()(wrapped_function)(request=request)
        self.assertTrue(isinstance(res, HttpResponse))
        self.assertEqual(res.status_code, 401)
        self.assertEqual(wrapped_function.call_count, 0)

        # Also test with actual AnonymousUser class which will have different
        # implementation under different Django versions
        request.user = AnonymousUser()

        res = basic_auth_required()(wrapped_function)(request=request)
        self.assertTrue(isinstance(res, HttpResponse))
        self.assertEqual(res.status_code, 401)
        self.assertEqual(wrapped_function.call_count, 0)
