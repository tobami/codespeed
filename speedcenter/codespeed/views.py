# -*- coding: utf-8 -*-
from django.shortcuts import get_object_or_404, render_to_response
from codespeed.models import Project, Revision, Result, Interpreter, Benchmark, Environment
from django.http import HttpResponse, Http404, HttpResponseNotAllowed, HttpResponseBadRequest, HttpResponseNotFound
from codespeed import settings
from datetime import datetime
from time import sleep
import json

def getbaselineinterpreters():
    baseline = []
    if hasattr(settings, 'baselinelist'):
        try:
            for entry in settings.baselinelist:
                interpreter = Interpreter.objects.get(id=entry['interpreter'])
                rev = Revision.objects.filter(
                    commitid=entry['revision'], project=interpreter.project
                )
                if len(rev) > 1:
                    rev = rev[0]
                else:
                    raise Revision.DoesNotExist
                shortname = interpreter.name
                #if interpreter.coptions != "default":
                    #shortname += " " + interpreter.coptions
                name = interpreter.name + " " + interpreter.coptions
                if rev.tag: name += " " + rev.tag
                else: name += " " + str(rev.commitid)
                baseline.append({
                    'interpreter': interpreter.id,
                    'name': name,
                    'shortname': shortname,
                    'revision': rev.commitid,
                    'project': rev.project,
                })
        except (Interpreter.DoesNotExist, Revision.DoesNotExist):
            # TODO: write to server logs
            pass
    else:
        revs = Revision.objects.exclude(tag="")
        interpreters = Interpreter.objects.all()
        for rev in revs:
            #add interpreters that correspond to each tagged revision.
            for interpreter in interpreters:
                if interpreter.project == rev.project:
                    shortname = interpreter.name
                    #if interpreter.coptions != "default":
                        #shortname += " " + interpreter.coptions
                    name = interpreter.name + " " + interpreter.coptions
                    if rev.tag: name += " " + rev.tag
                    else: name += " " + str(rev.commitid)
                    baseline.append({
                        'interpreter': interpreter.id,
                        'name': name,
                        'shortname': shortname,
                        'revision': rev.commitid,
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

def getdefaultenvironment():
    default = Environment.objects.all()
    if not len(default): return 0
    default = default[0]
    if hasattr(settings, 'defaultenvironment'):
        try:
            default = Environment.objects.get(name=settings.defaultenvironment)
        except Environment.DoesNotExist:
            pass
    return default

def getdefaultinterpreters():
    default = []
    defaultproject = Project.objects.filter(isdefault=True)[0]
    if hasattr(settings, 'defaultinterpreters'):
        try:
            for interpreter in settings.defaultinterpreters:
                i = Interpreter.objects.get(id=interpreter)
                default.append(interpreter)
        except Interpreter.DoesNotExist:
            i_list = Interpreter.objects.filter(project=defaultproject)
            for i in i_list:
                default.append(i.id)
    else:
        i_list = Interpreter.objects.filter(project=defaultproject)
        for i in i_list:
            default.append(i.id)
    
    return default

def gettimelinedata(request):
    if request.method != 'GET':
        return HttpResponseNotAllowed('GET')
    data = request.GET

    defaultproject = Project.objects.filter(isdefault=True)[0]

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
    
    baseline = getbaselineinterpreters()
    baselinerev = None
    if data['baseline'] == "true" and len(baseline):
        p = Project.objects.get(name=baseline['project'])
        baseline = baseline[0]
        baselinerev = Revision.objects.get(
            commitid=baseline['revision'], project=p
        )
    
    for bench in benchmarks:
        append = False
        timeline = {}
        timeline['benchmark'] = bench.name
        timeline['benchmark_id'] = bench.id
        timeline['interpreters'] = {}
        if data['baseline'] == "true" and len(baseline):
            timeline['baseline'] = Result.objects.get(
                interpreter=baseline['interpreter'], benchmark=bench, revision=baselinerev
            ).value
        for interpreter in interpreters:
            resultquery = Result.objects.filter(
                    revision__project=defaultproject
                ).filter(
                    benchmark=bench
                ).filter(
                    interpreter=interpreter
                ).order_by('-revision__commitid')[:number_of_rev]
            results = []
            for res in resultquery:
                results.append([res.revision.commitid, res.value])
            timeline['interpreters'][interpreter] = results
            if len(results): append = True
        if append: timeline_list['timelines'].append(timeline)
    
    if not len(timeline_list['timelines']):
        response = 'No data found for project "' + defaultproject.name + '"'
        timeline_list['error'] = response
    return HttpResponse(json.dumps( timeline_list ))

def timeline(request):
    if request.method != 'GET':
        return HttpResponseNotAllowed('GET')
    data = request.GET
    
    # Configuration of default parameters
    defaultproject = Project.objects.filter(isdefault=True)
    if not len(defaultproject):
        return HttpResponse("You need to configure at least one Project as default")
    else: defaultproject = defaultproject[0]
    
    defaultenvironment = getdefaultenvironment()
    if not defaultenvironment:
        return HttpResponse("You need to configure at least one Environment")
    defaultenvironment = defaultenvironment.id
    
    baseline = getbaselineinterpreters()
    
    defaultbaseline = True
    if data.has_key("baseline"):
        if data["baseline"] == "false":
            defaultbaseline = False
    if len(baseline): baseline = baseline[0]
    else: defaultbaseline = False
    
    defaultbenchmark = "grid"
    if data.has_key("benchmark"):
        try:
            defaultbenchmark = int(data["benchmark"])
        except ValueError:
            defaultbenchmark = get_object_or_404(Benchmark, name=data["benchmark"]).id
    
    defaultinterpreters = getdefaultinterpreters()
    if data.has_key("interpreters"):
        defaultinterpreters = []
        for i in data["interpreters"].split(","):
            selected = Interpreter.objects.filter(id=int(i))
            if len(selected): defaultinterpreters.append(selected[0].id)
    
    lastrevisions = [10, 50, 200, 1000]
    defaultlast = 200
    if data.has_key("revisions"):
        if int(data["revisions"]) in lastrevisions:
            defaultlast = data["revisions"]
    
    # Information for template
    interpreters = Interpreter.objects.filter(project=defaultproject)
    benchmarks = Benchmark.objects.all()
    hostlist = Environment.objects.all()
    return render_to_response('codespeed/timeline.html', {
        'defaultinterpreters': defaultinterpreters,
        'defaultbaseline': defaultbaseline,
        'baseline': baseline,
        'defaultbenchmark': defaultbenchmark,
        'defaultenvironment': defaultenvironment,
        'lastrevisions': lastrevisions,
        'defaultlast': defaultlast,
        'interpreters': interpreters,
        'benchmarks': benchmarks,
        'hostlist': hostlist
    })

def getoverviewtable(request):
    data = request.GET
    
    defaultproject = Project.objects.filter(isdefault=True)[0]
    interpreter = int(data["interpreter"])
    trendconfig = int(data["trend"])
    revision = int(data["revision"])
    lastrevisions = Revision.objects.filter(
        project=defaultproject
    ).filter(commitid__lte=revision).order_by('-commitid')[:trendconfig+1]
    lastrevision = lastrevisions[0].commitid

    change_list = None
    pastrevisions = None
    if len(lastrevisions) > 1:
        changerevision = lastrevisions[1].commitid
        change_list = Result.objects.filter(
            revision__commitid=changerevision
        ).filter(
            revision__project=defaultproject
        ).filter(interpreter=interpreter)   
        pastrevisions = lastrevisions[trendconfig-2:trendconfig+1]

    result_list = Result.objects.filter(
        revision__commitid=lastrevision
    ).filter(
        revision__project=defaultproject
    ).filter(interpreter=interpreter)
    
    # TODO: remove baselineflag
    baselineflag = False
    base_list = None
    baseinterpreter = None
    if data.has_key("baseline"):
        if data['baseline'] != "undefined":
            baselineflag = True
            base = int(data['baseline']) - 1
            baseline = getbaselineinterpreters()
            baseinterpreter = baseline[base]
            p = Project.objects.get(name=baseline[base]['project'])
            base_list = Result.objects.filter(
                revision__commitid=baseline[base]['revision']
            ).filter(
                revision__project=p
            ).filter(interpreter=baseline[base]['interpreter'])

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
                    revision__commitid=rev.commitid
                ).filter(
                    revision__project=defaultproject
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
    defaultproject = Project.objects.filter(isdefault=True)
    if not len(defaultproject):
        return HttpResponse("You need to configure at least one Project as default")
    else: defaultproject = defaultproject[0]
    defaultenvironment = getdefaultenvironment()
    if not defaultenvironment:
        return HttpResponse("You need to configure at least one Environment")
    defaultenvironment = defaultenvironment.id

    defaultchangethres = 3
    defaulttrendthres = 3
    defaultcompthres = 0.2
    defaulttrend = 10
    trends = [5, 10, 20, 100]
    if data.has_key("trend"):
        if data["trend"] in trends:
            defaulttrend = int(request.GET["trend"])

    defaultinterpreter = getdefaultinterpreters()
    if len(defaultinterpreter): defaultinterpreter = defaultinterpreter[0]
    if data.has_key("interpreter"):
        selected = Interpreter.objects.filter(id=int(data["interpreter"]))
        if len(selected): defaultinterpreter = selected[0].id
    
    baseline = getbaselineinterpreters()
    defaultbaseline = 1
    if data.has_key("baseline"):
        defaultbaseline = int(request.GET["baseline"])
        if len(baseline) < defaultbaseline: defaultbaseline = 1
    
    # Information for template
    interpreters = Interpreter.objects.filter(project=defaultproject)
    lastrevisions = Revision.objects.filter(
        project=defaultproject
    ).order_by('-commitid')[:20]
    if not len(lastrevisions):
        response = 'No data found for project "' + defaultproject.name + '"'
        return HttpResponse(response)
    selectedrevision = lastrevisions[0].commitid
    if data.has_key("revision"):
        if data["revision"] > 0:
            # TODO: Create 404 html embeded in the overview
            selectedrevision = get_object_or_404(Revision, commitid=data["revision"])
    hostlist = Environment.objects.all()
    
    return render_to_response('codespeed/overview.html', locals())

def getcommitdate(project, branch, commitid):
    # FIXME: if project has defined a repository, read real commitdate
    if project.rcType == 'N':
        return None
    else:
        return None

def addresult(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed('POST')
    data = request.POST
    
    mandatory_data = [
        'commitid',
        'project',
        'branch',
        'interpreter_name',
        'interpreter_coptions',
        'benchmark',
        'environment',
        'result_value',
        'result_date',
    ]
    
    for key in mandatory_data:
        if data.has_key(key):
            if data[key] == "":
                return HttpResponseBadRequest('Key "' + key + '" empty in request')
        else: return HttpResponseBadRequest('Key "' + key + '" missing from request')

    # Check that Environment exists
    try:
        e = get_object_or_404(Environment, name=data['environment'])
    except Http404:
        return HttpResponseNotFound("Environment " + data["environment"] + " not found")
    
    p, created = Project.objects.get_or_create(name=data["project"])
    b, created = Benchmark.objects.get_or_create(name=data["benchmark"])
    rev, created = Revision.objects.get_or_create(
        commitid=data['commitid'],
        project=p,
        branch=data['branch'],
    )
    
    temp_date = getcommitdate(p, data['branch'], data['commitid'])
    if temp_date:
        rev.date = temp_date
    else:
        rev.date = data["result_date"]
    rev.save()
    
    inter, created = Interpreter.objects.get_or_create(
        name=data['interpreter_name'],
        coptions=data['interpreter_coptions'],
        project=p
    )
    r, created = Result.objects.get_or_create(
            value=data["result_value"],
            revision=rev,
            interpreter=inter,
            benchmark=b,
            environment=e
    )
    
    r.date = data["result_date"]
    if data.has_key('std_dev'): r.std_dev = data['std_dev']
    if data.has_key('min'): r.val_min = data['min']
    if data.has_key('max'): r.val_max = data['max']
    r.save()
    
    return HttpResponse("Result data saved succesfully")
