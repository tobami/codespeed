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

PUT a full result:
    curl --dump-header - -H "Content-Type: application/json" -X POST \
        --data '{"commitid": "4", "branch": "default", \
        "project": "MyProject", "executable": "myexe O3 64bits", \
        "benchmark": "float", "environment": "Quad Core", \
        "result_value": 4000, "result": "4000"}' \
        http://127.0.0.1:8000/api/v1/benchmark-result/

See http://django-tastypie.readthedocs.org/en/latest/interacting.html
"""
import logging
from datetime import datetime

from django.contrib.auth.models import User
from django.db import models
from django.http import Http404
from django.shortcuts import get_object_or_404
from tastypie.bundle import Bundle
from tastypie.exceptions import ImmediateHttpResponse
from tastypie.http import HttpBadRequest, HttpCreated, HttpNotImplemented
from tastypie.resources import ModelResource, Resource
from tastypie import fields
from tastypie.authorization import Authorization, DjangoAuthorization
from tastypie.authentication import (Authentication, ApiKeyAuthentication,
                                     MultiAuthentication)
from tastypie.models import create_api_key
from tastypie.utils.dict import dict_strip_unicode_keys

from codespeed.models import (Environment, Project, Result, Branch, Revision,
                              Executable, Benchmark, Report)


models.signals.post_save.connect(create_api_key, sender=User)


class UserResource(ModelResource):
    """Resource for Django User()"""

    class Meta:
        queryset = User.objects.filter(is_active=True)
        resource_name = 'user'
        fields = ['username', 'first_name', 'last_name', 'email']
        allowed_methods = ['get']
        #excludes = ['email', 'password', 'is_superuser']
        # Add it here.
        authorization = DjangoAuthorization()
        authentication = ApiKeyAuthentication()


class ProjectResource(ModelResource):
    """Resource for Project()"""

    class Meta:
        queryset = Project.objects.all()
        authorization = DjangoAuthorization()
        # Note, the order for MultiAuthentication matters!
        authentication = MultiAuthentication(ApiKeyAuthentication(),
                                             Authentication())


class BranchResource(ModelResource):
    """Resource for Branch()"""

    project = fields.ToOneField(ProjectResource, 'project')

    class Meta:
        queryset = Branch.objects.all()
        authorization = DjangoAuthorization()
        authentication = MultiAuthentication(ApiKeyAuthentication(),
                                             Authentication())


class RevisionResource(ModelResource):
    """Resource for Revision()"""

    project = fields.ToOneField(ProjectResource, 'project')
    branch = fields.ToOneField(BranchResource, 'branch')

    class Meta:
        queryset = Revision.objects.all()
        authorization = DjangoAuthorization()
        authentication = MultiAuthentication(ApiKeyAuthentication(),
                                             Authentication())


class ExecutableResource(ModelResource):
    """Resource for Executable()"""

    project = fields.ToOneField(ProjectResource, 'project')

    class Meta:
        queryset = Executable.objects.all()
        authorization = DjangoAuthorization()
        authentication = MultiAuthentication(ApiKeyAuthentication(),
                                             Authentication())


class BenchmarkResource(ModelResource):
    """Resource for Benchmark()"""

    class Meta:
        queryset = Benchmark.objects.all()
        authorization = DjangoAuthorization()
        authentication = MultiAuthentication(ApiKeyAuthentication(),
                                             Authentication())


class EnvironmentResource(ModelResource):
    """Resource for Enviroment()"""

    class Meta:
        queryset = Environment.objects.all()
        resource_name = 'environment'
        authorization = DjangoAuthorization()
        authentication = MultiAuthentication(ApiKeyAuthentication(),
                                             Authentication())


class ResultResource(ModelResource):
    """Resource for Result()"""
    revision = fields.ToOneField(RevisionResource, 'revision')
    executable = fields.ToOneField(ExecutableResource, 'executable')
    benchmark = fields.ToOneField(BenchmarkResource, 'benchmark')
    environment = fields.ToOneField(EnvironmentResource, 'environment')

    class Meta:
        queryset = Result.objects.all()
        authorization = DjangoAuthorization()
        authentication = MultiAuthentication(ApiKeyAuthentication(),
                                             Authentication())


class ReportResource(ModelResource):
    """Resource for Report()"""

    revision = fields.ToOneField(RevisionResource, 'revision')
    environment = fields.ToOneField(EnvironmentResource, 'environment')
    executable = fields.ToOneField(ExecutableResource, 'executable')

    class Meta:
        queryset = Report.objects.all()
        allowed_methods = ['get']
        authorization = DjangoAuthorization()
        authentication = MultiAuthentication(ApiKeyAuthentication(),
                                             Authentication())


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

    def __init__(self, obj=None, request=None, **kwargs):
        self.data = kwargs
        self.request = request

        if isinstance(obj, Result):
            self.obj = obj
            self._populate_by_obj()
        elif obj is None:
            self.obj = Result()
        else:
            raise ValueError("obj has to be an instance of models.Result")

        if self.data:
            self._check_data()
        self.__data_validated = False  # not used for now
        super(ResultBundle, self).__init__(data=self.data, obj=self.obj,
                                           request=self.request)

    def _populate_obj_by_data(self):
        """Database lookup

        get everything except the result, 2nd try reverse lookup
        """
        def populate(key):
            return {'project': lambda: ProjectResource().get_via_uri(
                    self.data['project'], request=self.request),

                    'executable': lambda: ExecutableResource().get_via_uri(
                    self.data['executable'], request=self.request),

                    'benchmark': lambda: BenchmarkResource().get_via_uri(
                    self.data['benchmark'], request=self.request),

                    'environment': lambda: EnvironmentResource().get_via_uri(
                    self.data['environment'], request=self.request),

                    'branch': lambda: BranchResource().get_via_uri(
                    self.data['branch'], request=self.request),

                    'revision': lambda: RevisionResource().get_via_uri(
                    self.data['commitid'],
                    request=self.request)}.get(key, None)()

        try:
            self.obj.value = float(self.data['result_value'])
        except ValueError, error:
            logging.error(
                "Result value: {0} cannot be converted to float. {1}".format(
                    self.data['result_value'], error
                ))
            raise ImmediateHttpResponse(
                response=HttpBadRequest(u"Value needs to be a number"))
        for key in [k for k in self.mandatory_keys
                    if k not in ('result_value',)]:
            try:
                #populate
                item = populate(key)
                setattr(self.obj, key, item)
            except Exception, error:
                logging.error("Data for field %s: %s not found. %s" % (
                    key, self.data[key], error))
                raise ImmediateHttpResponse(
                    response=HttpBadRequest(u"Error finding: {0}={1}".format(
                        key, self.data[key]
                    )))
        # populate optional data
        for key in [k for k in self.optional_keys
                    if k not in ('date')]:
            if key in self.data.keys():
                setattr(self.obj, key, self.data[key])

        if 'date' in self.data.keys():
            self.obj.date = self.data['date']
        else:
            self.obj.date = datetime.now()

    def _populate_by_obj(self):
        """set attributes to make obj match ResultBundleResource

        FIXME: That looks very wrong here.
        """
        self.obj.project = self.obj.executable.project
        self.obj.branch = self.obj.revision.branch
        #self.obj.result = self.obj
        setattr(self.obj, 'result', self.obj)

    def _check_data(self):
        """See if all mandatory data is there"""
        # check if all mandatory keys are there
        for key in [k for k in self.mandatory_keys
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
                raise ImmediateHttpResponse(
                    response=HttpBadRequest(error_text))

        # Check that the Environment exists
        try:
            self.obj.environment = EnvironmentResource().get_via_uri(
                self.data['environment'], request=self.request)
        except Environment.DoesNotExist:
            error_text = 'Environment: {0} not found in database.'.format(
                self.data['environment'])
            logging.error(error_text)
            raise ImmediateHttpResponse(
                response=HttpBadRequest(
                    error_text
                ))
        except Exception as e:
            error_text = ('Error while looking up Environment: '
                          '{0}, {1}.'.format(self.data['environment'], e))
            logging.error(error_text)
            raise ImmediateHttpResponse(response=HttpBadRequest(error_text))
        # check optional data
        for key in [k for k in self.optional_keys
                    if k not in ('date',)]:
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

    def hydrate_and_save(self):
        """Save self.obj which is an instance of Result()

           First populate the Result() instance with self.data
        """
        self._populate_obj_by_data()
        self.obj.save()


class ResultBundleResource(Resource):
    """Resource for all the data of a benchmark result.

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
         'notify'  -  Send notification to registered user if result varies
                      from previous results, currently not implemented
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
        object_class = Result
        authorization = DjangoAuthorization()
        authentication = MultiAuthentication(ApiKeyAuthentication(),
                                             Authentication())
        allowed_methods = ['get', 'post', 'put', 'delete']

    def get_resource_uri(self, bundle_or_obj):
        kwargs = {
            'resource_name': self._meta.resource_name,
        }

        if isinstance(bundle_or_obj, Bundle):
            kwargs['pk'] = bundle_or_obj.obj.pk
        else:
            kwargs['pk'] = bundle_or_obj.pk

        if self._meta.api_name is not None:
            kwargs['api_name'] = self._meta.api_name

        return self._build_reverse_url("api_dispatch_detail", kwargs=kwargs)

    def get_object_list(self, request):
        results = Result.objects.all()

        return [ResultBundle(obj=r, request=request).obj for r in results]

    def obj_get_list(self, request=None, **kwargs):
        """Return all benchmark results ever"""
        return self.get_object_list(request)

    def obj_get(self, request=None, **kwargs):
        """get the ResultBundle with the result_id as the primary key"""
        pk = kwargs['pk']
        result = Result.objects.get(pk=pk)
        result.project = result.executable.project
        result.branch = result.revision.branch
        setattr(result, 'result', result)
        return result

    def obj_create(self, bundle, request=None, **kwargs):
        # not calling hydrate here since bundle.save() has that functionality
        # self.full_hydrate(bundle) will try to hydrate result which is not
        # there yet
        #bundle = self.full_hydrate(bundle)
        bundle.hydrate_and_save()
        return bundle

    def obj_update(self, bundle, request=None, **kwargs):
        return self.obj_create(bundle, request, **kwargs)

    def post_list(self, request, **kwargs):
        """
        Creates a new resource/object with the provided data.

        Calls ``obj_create`` with the provided data and returns a response
        with the new resource's location.

        If a new resource is created, return ``HttpCreated`` (201 Created).
        """
        deserialized = self.deserialize(
            request, request.raw_post_data,
            format=request.META.get('CONTENT_TYPE', 'application/json')
        )
        deserialized = self.alter_deserialized_list_data(request, deserialized)
        bundle = ResultBundle(request=request,
                              **dict_strip_unicode_keys(deserialized))
        self.is_valid(bundle)
        updated_bundle = self.obj_create(bundle, request=request)
        return HttpCreated(location=self.get_resource_uri(updated_bundle))

    def post_detail(self, request, **kwargs):
        """
        Creates a new subcollection of the resource under a resource.

        This is not implemented by default because most people's data models
        aren't self-referential.

        If a new resource is created, return ``HttpCreated`` (201 Created).
        """
        return HttpNotImplemented()

    def obj_delete_list(self, request=None, **kwargs):
        return HttpNotImplemented()

    def obj_delete(self, request=None, **kwargs):
        #obj = Result.objects.get(pk=kwargs['pk'])
        #obj.delete()
        return HttpNotImplemented()

    def rollback(self, bundles):
        pass

    def detail_uri_kwargs(self):
        pass
