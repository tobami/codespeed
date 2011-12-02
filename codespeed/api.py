# -*- coding: utf-8 -*-

"""RESTful API implementation

Example:
GET Environment() data:
    →curl -H "Accept: application/json" \
        http://127.0.0.1:8000/api/v1/environment/1/

POST Environment() data:
    curl --dump-header - -H "Content-Type: application/json" -X POST \
        --data '{"name": "Single Core"}' \
        http://127.0.0.1:8000/api/v1/environment/

PUT Environment() data:
    curl --dump-header - -H "Content-Type: application/json" -X PUT \
        --data '{"name": "Quad Core"}' \
        http://127.0.0.1:8000/api/v1/environment/2/

DELETE Environment() data:
    →curl --dump-header - -H "Content-Type: application/json" -X DELETE \
        http://127.0.0.1:8000/api/v1/environment/2/

See http://django-tastypie.readthedocs.org/en/latest/interacting.html
"""

from django.contrib.auth.models import User
from django.db import models
from tastypie.resources import ModelResource, Resource
from tastypie import fields
from tastypie.authorization import Authorization, DjangoAuthorization
from tastypie.authentication import ApiKeyAuthentication
from tastypie.models import create_api_key
from codespeed.models import Environment, Project, Result, Branch, Revision, Executable, Benchmark, Report


models.signals.post_save.connect(create_api_key, sender=User)


class UserResource(ModelResource):
    """Ressource for Django User()
    """
    class Meta:
        queryset = User.objects.filter(is_active=True)
        resource_name = 'user'
        fields = ['username', 'first_name', 'last_name', 'email']
        allowed_methods = ['get']
        #excludes = ['email', 'password', 'is_superuser']
        # Add it here.
        #authorization = DjangoAuthorization()
        authorization= Authorization()
        #authentication = ApiKeyAuthentication() 


class ProjectResource(ModelResource):
    """Ressource for Project()
    """

    class Meta:
        queryset = Project.objects.all()
        authorization= Authorization()


class BranchResource(ModelResource):
    """Ressource for Branch()
    """

    class Meta:
        queryset = Branch.objects.all()
        authorization= Authorization()


class RevisionResource(ModelResource):
    """Ressource for Revision()
    """

    class Meta:
        queryset = Revision.objects.all()
        authorization= Authorization()


class ExecutableResource(ModelResource):
    """Ressource for Executable()
    """

    class Meta:
        queryset = Executable.objects.all()
        authorization= Authorization()


class BenchmarkResource(ModelResource):
    """Ressource for Benchmark()
    """

    class Meta:
        queryset = Benchmark.objects.all()
        authorization= Authorization()


class EnvironmentResource(ModelResource):
    """Ressource for Enviroment()
    """

    class Meta:
        queryset = Environment.objects.all()
        resource_name = 'environment'
        authorization= Authorization()


class ResultResource(ModelResource):
    """Ressource for Result()
    """

    class Meta:
        queryset = Result.objects.all()
        authorization= Authorization()


class ReportResource(ModelResource):
    """Ressource for Report()
    """

    class Meta:
        queryset = Report.objects.all()
        authorization= Authorization()


