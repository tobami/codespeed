# -*- coding: utf-8 -*-
from django.shortcuts import get_object_or_404, render_to_response
from codespeed.models import Revision, Result, Interpreter, Benchmark, Environment
from django.http import HttpResponse, Http404, HttpResponseNotAllowed, HttpResponseBadRequest, HttpResponseNotFound
from codespeed import settings
import json

def getbaselineinterpreters():
    baseline = []
    if hasattr(settings, 'baselinelist'):
        try:
            for entry in settings.baselinelist:
                interpreter = Interpreter.objects.get(id=entry['interpreter'])
                rev = Revision.objects.filter(number=entry['revision'])
                if len(rev) > 1:
                    for r in rev:
                        if(r.project in interpreter.name):
                            rev = r
                elif len(rev):
                    rev = rev[0]
                else:
                    raise Revision.DoesNotExist
                name = interpreter.name + " " + interpreter.coptions
                if rev.tag: name += " " + rev.tag
                else: name += " " + str(rev.number)
                baseline.append({
                    'interpreter': interpreter.id,
                    'name': name,
                    'revision': rev.number,
                    'project': rev.project,
                })
        except (Interpreter.DoesNotExist, Revision.DoesNotExist):
            # TODO: write to server logs
            pass
    else:
        revs = Revision.objects.exclude(tag="")
        interpreters = Interpreter.objects.all()
        for rev in revs:
            #add interpreters that correspond to each tagged revission.
            for interpreter in interpreters:
                if interpreter.name in rev.project:
                    name = interpreter.name + " " + interpreter.coptions
                    if rev.tag: name += " " + rev.tag
                    else: name += " " + str(rev.number)
                    baseline.append({
                        'interpreter': interpreter.id,
                        'name': name,
                        'revision': rev.number,
                        'project': rev.project,
                    })
    # move default to first place
    if hasattr(settings, 'defaultbaseline'):
        try:
            for base in baseline:
                if base['interpreter'] == settings.defaultbaseline['interpreter'] and base['revision'] == settings.defaultbaseline['revision']:
                    baseline.remove(base)
                    baseline.insert(0, base)
                    break
        except KeyError:
            # TODO: write to server logs
            #error in settings.defaultbaseline
            pass
    return baseline

def gettimelinedata(request):
    if request.method != 'GET':
        return HttpResponseNotAllowed('GET')
    data = request.GET
    
    timeline_list = {'error': 'None', 'timelines': []}
    interpreters = data['interpreters'].split(",")
    if interpreters[0] == "":
        timeline_list['error'] = "No interpreters selected"
        return HttpResponse(json.dumps( timeline_list ))
    
    benchmarks = []
    number_of_rev = data['revisions']
    if data['benchmark'] == 'grid':
        benchmarks = Benchmark.objects.all().order_by('name')
        number_of_rev = 15
    else:
        benchmarks.append(Benchmark.objects.get(id=data['benchmark']))
    
    baseline = Interpreter.objects.get(id=1)
    baselinerev = lastbase = Revision.objects.filter(
        tag__isnull=False
    ).filter(
        project='cpython'
    ).order_by('-number')[0]

    for bench in benchmarks:
        timeline = {}
        timeline['benchmark'] = bench.name
        timeline['benchmark_id'] = bench.id
        timeline['interpreters'] = {}
        if data['baseline'] == "true":
            timeline['baseline'] = Result.objects.get(
                interpreter=baseline, benchmark=bench, revision=baselinerev
            ).value
        for interpreter in interpreters:
            resultquery = Result.objects.filter(
                    revision__project=settings.PROJECT_NAME
                ).filter(
                    benchmark=bench
                ).filter(
                    interpreter=interpreter
                ).order_by('-revision__number')[:number_of_rev]
            results = []
            for res in resultquery:
                results.append([res.revision.number, res.value])
            timeline['interpreters'][interpreter] = results
        timeline_list['timelines'].append(timeline)
    return HttpResponse(json.dumps( timeline_list ))

def timeline(request):
    if request.method != 'GET':
        return HttpResponseNotAllowed('GET')
    data = request.GET
    
    # Configuration of default parameters
    baseline = Interpreter.objects.get(id=1)
    lastbaserev = Revision.objects.filter(
        tag__isnull=False
    ).filter(
        project='cpython'
    ).order_by('-number')[0]
    baselinetag = lastbaserev.tag
    baselinerev = lastbaserev.number

    defaultbaseline = True
    if data.has_key("baseline"):
        if data["baseline"] == "false":
            defaultbaseline = False
    
    defaulthost = 1
    defaultbenchmark = "grid"
    if data.has_key("benchmark"):
        try:
            defaultbenchmark = int(data["benchmark"])
        except ValueError:
            defaultbenchmark = get_object_or_404(Benchmark, name=data["benchmark"]).id
    
    defaultinterpreters = [2, 3]
    if data.has_key("interpreters"):
        defaultinterpreters = []
        for i in data["interpreters"].split(","):
            selected = Interpreter.objects.filter(id=int(i))
            if len(selected): defaultinterpreters.append(selected[0].id)
    if not len(defaultinterpreters): defaultinterpreters = [2, 3]

    lastrevisions = [10, 50, 200, 1000]
    defaultlast = 200
    if data.has_key("revisions"):
        if int(data["revisions"]) in lastrevisions:
            defaultlast = data["revisions"]
    
    # Information for template
    interpreters = Interpreter.objects.filter(name__startswith=settings.PROJECT_NAME)
    benchmarks = Benchmark.objects.all()
    hostlist = Environment.objects.all()
    return render_to_response('codespeed/timeline.html', {
        'defaultinterpreters': defaultinterpreters,
        'defaultbaseline': defaultbaseline,
        'baseline': baseline,
        'baselinetag': baselinetag,
        'defaultbenchmark': defaultbenchmark,
        'defaulthost': defaulthost,
        'lastrevisions': lastrevisions,
        'defaultlast': defaultlast,
        'interpreters': interpreters,
        'benchmarks': benchmarks,
        'hostlist': hostlist
    })

def getoverviewtable(request):
    data = request.GET
    interpreter = int(data["interpreter"])
    trendconfig = int(data["trend"])
    revision = int(data["revision"])
    lastrevisions = Revision.objects.filter(
        project=settings.PROJECT_NAME
    ).filter(number__lte=revision).order_by('-number')[:trendconfig+1]
    lastrevision = lastrevisions[0].number

    change_list = None
    pastrevisions = None
    if len(lastrevisions) > 1:
        changerevision = lastrevisions[1].number
        change_list = Result.objects.filter(
            revision__number=changerevision
        ).filter(
            revision__project=settings.PROJECT_NAME
        ).filter(interpreter=interpreter)   
        pastrevisions = lastrevisions[trendconfig-2:trendconfig+1]

    result_list = Result.objects.filter(
        revision__number=lastrevision
    ).filter(
        revision__project=settings.PROJECT_NAME
    ).filter(interpreter=interpreter)
    
    # TODO: remove baselineflag
    baselineflag = False
    base_list = None
    if data.has_key("baseline"):
        if data['baseline'] != "undefined":
            baselineflag = True
            base = int(data['baseline']) - 1
            baseline = getbaselineinterpreters()
            baseinterpreter = Interpreter.objects.get(id=baseline[base]['interpreter'])
            baserevision = baseline[base]['revision']
            base_list = Result.objects.filter(
                revision__number=baserevision
            ).filter(
                revision__project=baseline[base]['project']
            ).filter(interpreter=baseinterpreter)
    
    table_list = []
    totals = {'change': [], 'trend': [],}
    for bench in Benchmark.objects.all():
        resultquery = result_list.filter(benchmark=bench)
        if not len(resultquery): continue
        result = resultquery.filter(benchmark=bench)[0].value
        
        change = 0
        if change_list != None:
            c = change_list.filter(benchmark=bench)
            if c.count():
                change = (result - c[0].value)*100/c[0].value
                totals['change'].append(result / c[0].value)
        
        #calculate past average
        average = 0
        averagecount = 0
        if pastrevisions != None:
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
            totals['trend'].append(result / average)
        else:
            trend = "-"

        relative = 0
        if baselineflag:
            c = base_list.filter(benchmark=bench)
            if c.count():
                relative =  c[0].value / result
                #totals['relative'].append(relative)#deactivate average for comparison
        table_list.append({
            'benchmark': bench.name,
            'bench_description': bench.description,
            'result': result,
            'change': change,
            'trend': trend,
            'relative': relative,
        })
    
    # Compute Arithmetic averages
    for key in totals.keys():
        if len(totals[key]):
            totals[key] = float(sum(totals[key]) / len(totals[key]))
        else:
            totals[key] = "-"
    if totals['change'] != "-":
        totals['change'] = (totals['change'] - 1) * 100#transform ratio to percentage
    if totals['trend'] != "-":
        totals['trend'] = (totals['trend'] - 1) * 100#transform ratio to percentage

    return render_to_response('codespeed/overview_table.html', locals())
    
def overview(request):
    if request.method != 'GET':
        return HttpResponseNotAllowed('GET')
    data = request.GET

    # Configuration of default parameters
    defaulthost = 1
    defaultchangethres = 3
    defaulttrendthres = 3
    defaultcompthres = 0.2
    defaulttrend = 10
    trends = [5, 10, 20, 100]
    if data.has_key("trend"):
        if data["trend"] in trends:
            defaulttrend = int(request.GET["trend"])

    defaultinterpreter = 2
    if data.has_key("interpreter"):
        selected = Interpreter.objects.filter(id=int(data["interpreter"]))
        if len(selected): defaultinterpreter = selected[0].id
    
    baseline = getbaselineinterpreters()
    defaultbaseline = 1
    if data.has_key("baseline"):
        defaultbaseline = int(request.GET["baseline"])
        if len(baseline) < defaultbaseline: defaultbaseline = 1
    
    # Information for template
    interpreters = Interpreter.objects.filter(name__startswith=settings.PROJECT_NAME)
    lastrevisions = Revision.objects.filter(
        project=settings.PROJECT_NAME
    ).order_by('-number')[:15]
    if not len(lastrevisions):
        response = 'No data found for project "' + settings.PROJECT_NAME + '"'
        return HttpResponse(response)
    selectedrevision = lastrevisions[0].number
    if data.has_key("revision"):
        if data["revision"] > 0:
            # TODO: Create 404 html embeded in the overview
            selectedrevision = get_object_or_404(Revision, number=data["revision"])
    hostlist = Environment.objects.all()
    
    return render_to_response('codespeed/overview.html', locals())

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
