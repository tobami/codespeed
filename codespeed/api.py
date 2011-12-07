# -*- coding: utf-8 -*-

"""RESTful API implementation

Example:
GET Environment() data:
    curl -H "Accept: application/json" \
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
    curl --dump-header - -H "Content-Type: application/json" -X DELETE \
        http://127.0.0.1:8000/api/v1/environment/2/

See http://django-tastypie.readthedocs.org/en/latest/interacting.html
"""
import logging
from datetime import datetime
from django.contrib.auth.models import User
from django.db import models
<<<<<<< HEAD
from tastypie.bundle import Bundle
=======
from django.http import Http404
from django.shortcuts import get_object_or_404
from tastypie.bundle import Bundle
from tastypie.exceptions import ImmediateHttpResponse
from tastypie.http import HttpBadRequest
>>>>>>> Implement the 1st version of the Result Bundle class
from tastypie.resources import ModelResource, Resource
from tastypie import fields
from tastypie.authorization import Authorization, DjangoAuthorization
from tastypie.authentication import ApiKeyAuthentication
from tastypie.models import create_api_key
from codespeed.models import (Environment, Project, Result, Branch, Revision,
                              Executable, Benchmark, Report)


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


class ResultBundle(Bundle):
    """tastypie.api.Bundle class to deal with submitted results.

    Note, to populate the Bundle.obj with data .save()
    has to be called first.

    FIXME (a8): add models.Data if they do not exist in DB
    """
    DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'

    # order of mandatory_keys must not be changed
    # FIXME (a8): refactor result_value to just value
    mandatory_keys = (
        'revision',
        'project',
        'executable',
        'benchmark',
        'environment',
        'branch',
        'result_value',
    )

    # Note, views.add_result() expects result_date. Here it's the
    # same as the Result() attribute
    optional_keys = (
        'std_dev',
        'val_min',
        'val_max',
        'date',
    )

    def __init__(self, **data):
        self.data = data
        self.obj =  Result()
        self.__data_validated = False   #not used so far
        self._check_data()
        super(ResultBundle, self).__init__(data=data, obj=self.obj)

    def _populate_obj_by_data(self):
        """Database lookup

        get everything except the result, 2nd try reverse lookup
        """
        def populate(key):
            return {
                'project': lambda: Project.objects.get(name=self.data['project']),
                'executable': lambda: Executable.objects.get(
                    name=self.data['executable']),
                'benchmark': lambda: Benchmark.objects.get(name=self.data['benchmark']),
                'environment': lambda: Environment.objects.get(
                    name=self.data['environment']),
                'branch': lambda: Branch.objects.get(name=self.data['branch'],
                                            project=self.obj.project),
            }.get(key, None)()

        try:
            self.obj.value =  float(self.data['result_value'])
        except ValueError, error:
            logging.error(
                "Result value: {0} cannot be converted to float. {1}".format(
                    self.data['result_value'], error
                ))
            raise ImmediateHttpResponse(
                response=HttpBadRequest(u"Value needs to be a number"))
        for key in [k for k in self.mandatory_keys \
                    if k not in ('result_value', 'revision')]:
            try:
                #populate
                item = populate(key)
                setattr(self.obj, key, item)
                #self.data[key] = populate(key)
            except Exception, error:
                print "Except Key: %s" % key
                logging.error("Data for field %s: %s not found. %s" % (
                    key, self.data[key], error))
                raise ImmediateHttpResponse(
                    response=HttpBadRequest(u"Error finding: {0}={1}".format(
                        key, self.data[key]
                    )))

        # find the revision
        self.obj.revision = Revision.objects.get(
            commitid=self.data['commitid'],
            project=self.obj.project,
            branch=self.obj.branch,
            )
        # populate optional data
        for key in [k for k in self.optional_keys \
                    if k not in ('date')]:
            if key in self.data.keys():
                setattr(self.obj, key, self.data[key])

        if 'date' in self.data.keys():
            self.obj.date = self.data['date']
        else:
            self.obj.date = datetime.now()

    def _check_data(self):
        """See if all mandatory data is there
        """
        # check if all mandatory keys are there
        for key in [k for k in self.mandatory_keys\
                    if k not in ('revision')]:
            if not key in self.data.keys():
                error_text = u"You need to provide key: {0}".format(key)
                logging.error(error_text)
                raise ImmediateHttpResponse(
                    response=HttpBadRequest(error_text))
            # check for data
            elif not self.data[key]:
                error_text = 'Value for key {0} is empty.'.format(key)
                logging.error(error_text)
                raise ImmediateHttpResponse(response=HttpBadRequest(error_text))

        # Check that the Environment exists
        try:
            self.obj.environment = Environment.objects.get(
                name=self.data['environment'])
        except Environment.DoesNotExist:
            error_text = 'Environment: {0} not found in database.'.format(
                self.data['environment'])
            logging.error(error_text)
            raise ImmediateHttpResponse(
                response=HttpBadRequest(
                    error_text
                ))
        except Exception as e:
            error_text = 'Error while looking up Environment: {0}, {1}.'.format(
                self.data['environment'], e)
            logging.error(error_text)
            raise ImmediateHttpResponse(
                response=HttpBadRequest(
                    error_text
                ))
        # check optional data
        for key in [k for k in self.optional_keys \
                    if k not in ('date')]:
            if key in self.data.keys():
                try:
                    self.data[key] = float(self.data[key])
                except ValueError:
                    error_text = u"{0} cannot be casted to float.".format(
                        self.data[key])
                    logging.error(error_text)
                    raise ImmediateHttpResponse(
                        response=HttpBadRequest(error_text))

        if 'date' in self.data.keys():
            #FIXME (a8): make that more robust for different json date formats
            try:
                self.data['date'] = datetime.strptime(self.data['date'],
                                                      self.DATETIME_FORMAT)
            except ValueError:
                error_text = u"Cannot convert date {0} into datetime.".format(
                    self.data['date'])
                logging.error(error_text)
                raise ImmediateHttpResponse(
                    response=HttpBadRequest(error_text))

    def save(self):
            """Save self.obj which is an instance of Result()

                First populate the Result() instance with self.data
            """
            self._populate_obj_by_data()
            self.obj.save()


class ResultBundleResource(Resource):
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

        not mandatory data
         'notify'  -  Send notification to registered user if result varies from
                      previous results
    """

    revision = fields.ToOneField(RevisionResource, 'revision')
    branch = fields.ToOneField(BranchResource, 'branch')
    project = fields.ToOneField(ProjectResource, 'project')
    executable = fields.ToOneField(ExecutableResource, 'executable')
    benchmark = fields.ToOneField(BenchmarkResource, 'benchmark')
    environment = fields.ToOneField(EnvironmentResource, 'environment')
    result = fields.ToOneField(ResultResource, 'result')
    user = fields.ToOneField(UserResource, 'user')
    notify = fields.CharField(attribute='notify')

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
        """get the ResultBundle with the result_id as the primary key
        """
        pk = kwargs['pk']
        result = Result.objects.get(pk=pk)
        bundle.obj = result
        bundle.obj.project = bundle.obj.executable.project
        bundle.obj.branch = bundle.obj.revision.branch
        bundle.obj.result = result
        return bundle.obj

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

