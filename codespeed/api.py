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
import logging

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


class BenchmarkResultResource(Resource):
    """Ressource for all the data of a benchmark result.

       Primarily used to submit benchmark results

        mandatory data
        'commitid',
        'branch',
        'project',
        'executable',
        'benchmark',
        'environment',
        'result_value',
    """

    revision = fields.ToOneField(RevisionResource, 'revision')
    branch = fields.ToOneField(BranchResource, 'branch')
    project = fields.ToOneField(ProjectResource, 'project')
    executable = fields.ToOneField(ExecutableResource, 'executable')
    benchmark = fields.ToOneField(BenchmarkResource, 'benchmark')
    environment = fields.ToOneField(EnvironmentResource, 'environment')
    result = fields.ToOneField(ResultResource, 'result')

    class Meta:
        resource_name = 'benchmark-result'
        authorization= Authorization()
        allowed_methods = ['get', 'post', 'put', 'delete']

    def get_object_list(self, request):
        query = self._client().add('messages')
        query.map("function(v) { var data = JSON.parse(v.values[0].data); return [[v.key, data]]; }")
        results = []

        for result in query.run():
            new_obj = RiakObject(initial=result[1])
            new_obj.uuid = result[0]
            results.append(new_obj)

        return results

    def obj_get_list(self, request=None, **kwargs):
        """Return all benchmark results ever
        """
        return self.get_object_list(request)

    def obj_get(self, request=None, **kwargs):
        pk = kwargs['pk']
        result = Result.objects.get(pk=pk)
        result.project = result.executable.project
        result.result = result
        result.branch = result.revision.branch
        return result

    def obj_create(self, bundle, request=None, **kwargs):
        bundle.obj = RiakObject(initial=kwargs)
        bundle = self.full_hydrate(bundle)
        bucket = self._bucket()
        new_message = bucket.new(bundle.obj.uuid, data=bundle.obj.to_dict())
        new_message.store()
        return bundle

    def obj_update(self, bundle, request=None, **kwargs):
        return self.obj_create(bundle, request, **kwargs)

    def obj_delete_list(self, request=None, **kwargs):
        bucket = self._bucket()

        for key in bucket.get_keys():
            obj = bucket.get(key)
            obj.delete()

    def obj_delete(self, request=None, **kwargs):
        bucket = self._bucket()
        obj = bucket.get(kwargs['pk'])
        obj.delete()

    def rollback(self, bundles):
        pass
