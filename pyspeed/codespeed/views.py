# -*- coding: utf-8 -*-
from django.shortcuts import get_object_or_404
from pyspeed.codespeed.models import Revision, Result, Interpreter, Benchmark, Environment
from django.http import HttpResponse, Http404, HttpResponseNotAllowed, HttpResponseBadRequest, HttpResponseNotFound

def addresult(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed('POST')
    data =  request.POST
    
    mandatory_data = [
        'revision_number',
        'revision_project',
        'interpreter_name',
        'interpreter_coptions',
        'benchmark_name',
        'environment',
        'result_key',
        'result_value',
        'result_date',
    ]
    for key in mandatory_data:
        if data.has_key(key):
            if data[key] == "":
                return HttpResponseBadRequest('Key "' + key + '" empty in request')
        else: return HttpResponseBadRequest('Key "' + key + '" missing from request')
    b, created = Benchmark.objects.get_or_create(name=data["benchmark_name"])
    if data.has_key('benchmark_type'):
        b.benchmark_type = data['benchmark_type']
        b.save()
    rev, created = Revision.objects.get_or_create(number=data["revision_number"], project=data["revision_project"])
    if data.has_key('revision_date'):
        rev.date = data['revision_date']
        rev.save()
    inter, created = Interpreter.objects.get_or_create(name=data["interpreter_name"], coptions=data["interpreter_coptions"])
    try:
        e = get_object_or_404(Environment, name=data["environment"])
    except Http404:
        return HttpResponseNotFound("Environment " + data["environment"] + " not found")
    result_type = "T"
    if data.has_key('result_type'):
        result_type = data['result_type']
    r, created = Result.objects.get_or_create(
            key=data["result_key"],
            value=data["result_value"],
            result_type=result_type,
            date=data["result_date"],
            revision=rev,
            interpreter=inter,
            benchmark=b,
            environment=e
    )
    return HttpResponse("Result data saved succesfully")
