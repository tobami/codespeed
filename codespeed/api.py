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

from tastypie.resources import ModelResource
from tastypie.authorization import Authorization
from codespeed.models import Environment


class EnvironmentResource(ModelResource):
    class Meta:
        queryset = Environment.objects.all()
        resource_name = 'environment'
        authorization= Authorization()

