# -*- coding: utf-8 -*-
from django.shortcuts import get_object_or_404, render_to_response
from pyspeed.codespeed.models import Revision, Result, Interpreter, Benchmark, Environment
from django.http import HttpResponse, Http404, HttpResponseNotAllowed, HttpResponseBadRequest, HttpResponseNotFound
from pyspeed import settings
import json

def resultstable(request):
    result_list = Result.objects.order_by('-date')[:300]
    return render_to_response('results_table.html', locals())

def results(request):
    return render_to_response('results.html')

def compare(request):
    return render_to_response('comparison.html')
    
def getdata(request):
    if request.method != 'GET':
        return HttpResponseNotAllowed('GET')
    data = request.GET
    
    lastrevisions = Revision.objects.filter(
        project=settings.PROJECT_NAME
    ).order_by('-number')[:data["revisions"]]
    
    result_list = {}
    result_list["error"] = "None"
    interpreters = data["interpreters"].split(",")
    if interpreters[0] == "":
        result_list["error"] = "No interpreters selected"
        return HttpResponse(json.dumps( result_list ))
    for interpreter in interpreters:
        results = []
        for rev in lastrevisions:
            res = Result.objects.filter(
                revision__number=rev.number
            ).filter(
                revision__project=settings.PROJECT_NAME
            ).filter(
                benchmark=data["benchmark"]
            ).filter(interpreter=interpreter)
            if len(res): results.append([rev.number, res[0].value])
        result_list[interpreter] = results
    return HttpResponse(json.dumps( result_list ))

def timeline(request):
    if request.method != 'GET':
        return HttpResponseNotAllowed('GET')
    data = request.GET
    
    # Configuration of default parameters
    defaultbenchmark = 1
    if data.has_key("benchmark"):
        try:
            defaultbenchmark = int(data["benchmark"])
        except ValueError:
            defaultbenchmark = get_object_or_404(Benchmark, name=data["benchmark"]).id
    
    defaultinterpreters = [2]
    if data.has_key("interpreters"):
        defaultinterpreters = []
        for i in data["interpreters"].split(","):
            selected = Interpreter.objects.filter(id=int(i))
            if len(selected): defaultinterpreters.append(selected[0].id)
    if not len(defaultinterpreters): defaultinterpreters = [2]

    lastrevisions = [20, 50, 100]
    defaultlast = 50
    if data.has_key("lastrevisions"):
        if data["lastrevisions"] in lastrevisions:
            defaultlast = data["lastrevisions"]
    
    # Information for template
    interpreters = Interpreter.objects.filter(name__startswith=settings.PROJECT_NAME)
    benchmarks = Benchmark.objects.all()
    hostlist = Environment.objects.all()
    return render_to_response('timeline.html', locals())

def overviewtable(request):
    interpreter = int(request.GET["interpreter"])
    trendconfig = int(request.GET["trend"])
    revision = int(request.GET["revision"])
    lastrevisions = Revision.objects.filter(
        project=settings.PROJECT_NAME
    ).filter(number__lte=revision).order_by('-number')[:11]
    lastrevision = lastrevisions[0].number
    changerevision = lastrevisions[1].number    
    pastrevisions = lastrevisions[trendconfig-2:trendconfig+1]
    
    result_list = Result.objects.filter(
        revision__number=lastrevision
    ).filter(
        revision__project=settings.PROJECT_NAME
    ).filter(interpreter=interpreter)

    change_list = Result.objects.filter(
        revision__number=changerevision
    ).filter(
        revision__project=settings.PROJECT_NAME
    ).filter(interpreter=interpreter)
    
    lastbase = Revision.objects.filter(
        tag__isnull=False
    ).filter(
        project='cpython'
    ).order_by('-number')[0].number
    base_list = Result.objects.filter(
        revision__number=lastbase
    ).filter(
        revision__project='cpython'
    ).filter(interpreter=1)
    
    table_list = []
    for bench in Benchmark.objects.all():
        if not len(result_list.filter(benchmark=bench)): continue
        result = result_list.filter(benchmark=bench)[0].value
        
        change = 0
        c = change_list.filter(benchmark=bench)
        if c.count():
            change = (result - c[0].value)*100/c[0].value
        
        #calculate past average
        average = 0
        averagecount = 0
        for rev in pastrevisions:
            past_rev = Result.objects.filter(
                revision__number=rev.number
            ).filter(
                revision__project=settings.PROJECT_NAME
            ).filter(
                interpreter=interpreter
            ).filter(benchmark=bench)
            if past_rev.count():
                average += past_rev[0].value
                averagecount += 1
        trend = 0
        if average:
            average = average / averagecount
            trend =  (result - average)*100/average
            trend = "%.2f" % trend
        else:
            trend = "-"

        relative = 0
        c = base_list.filter(benchmark=bench)
        if c.count():
            relative =  c[0].value / result
        table_list.append({
            'benchmark': bench.name,
            'result': result,
            'change': change,
            'trend': trend,
            'relative': relative
        })
    
    return render_to_response('overview_table.html', locals())
    
def overview(request):
    if request.method != 'GET':
        return HttpResponseNotAllowed('GET')
    data = request.GET
    
    # Configuration of default parameters
    defaulttrend = 10
    trends = [5, 10, 20]
    if data.has_key("trend"):
        if data["trend"] in trends:
            defaulttrend = int(request.GET["trend"])

    defaultinterpreter = 2
    if data.has_key("interpreter"):
        selected = Interpreter.objects.filter(id=int(data["interpreter"]))
        if len(selected): defaultinterpreter = selected[0].id
    
    # Information for template
    interpreters = Interpreter.objects.filter(name__startswith=settings.PROJECT_NAME)
    lastrevisions = Revision.objects.filter(
        project=settings.PROJECT_NAME
    ).order_by('-number')[:15]
    selectedrevision = lastrevisions[0].number
    if data.has_key("revision"):
        if data["revision"] > 0:
            # TODO: Create 404 html embeded in the overview
            selectedrevision = get_object_or_404(Revision, number=data["revision"])
    hostlist = Environment.objects.all()
    
    return render_to_response('overview.html', locals())

def addresult(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed('POST')
    data = request.POST
    
    mandatory_data = [
        'revision_number',
        'revision_project',
        'interpreter_name',
        'interpreter_coptions',
        'benchmark_name',
        'environment',
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
            result_type=result_type,
            revision=rev,
            interpreter=inter,
            benchmark=b,
            environment=e
    )
    r.value = data["result_value"]
    r.date = data["result_date"]
    r.save()
    
    return HttpResponse("Result data saved succesfully")
