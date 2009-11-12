# -*- coding: utf-8 -*-
#from django.shortcuts import render_to_response
#from django.views.generic.list_detail import object_list
from pyspeed.codespeed.models import Revision, Result, Interpreter, Benchmark
#from pyspeed import settings
from django.http import HttpResponse, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404

def addresult(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed('POST')
    data =  request.POST
    print data
    ben = get_object_or_404(Benchmark, name=data["benchmark_name"])
    print "benchmark:", ben
    rev = get_object_or_404(Revision, number=data["revision_number"], project=data["revision_project"])
    print "revision object:", rev
    inter = get_object_or_404(Interpreter, name=data["interpreter_name"], coptions=data["interpreter_coptions"])
    print inter
    return HttpResponse("Data saved succesfully")
