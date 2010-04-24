# -*- coding: utf-8 -*-
from django.shortcuts import get_object_or_404, render_to_response
from codespeed.models import Project, Revision, Result, Executable, Benchmark, Environment
from django.http import HttpResponse, Http404, HttpResponseNotAllowed, HttpResponseBadRequest, HttpResponseNotFound
from codespeed import settings
from datetime import datetime
from time import sleep
import json


def getbaselineexecutables():
    baseline = []
    if hasattr(settings, 'baselinelist') and settings.baselinelist != None:
        try:
            for entry in settings.baselinelist:
                executable = Executable.objects.get(id=entry['executable'])
                rev = Revision.objects.filter(
                    commitid=str(entry['revision']), project=executable.project
                )
                if len(rev) > 0:
                    rev = rev[0]
                else:
                    raise Revision.DoesNotExist
                name = executable.name
                if executable.coptions != "default" or executable.coptions != "none":
                    name += " " + executable.coptions
                if rev.tag: name += " " + rev.tag
                else: name += " " + rev.commitid
                baseline.append({
                    'executable': executable,
                    'revision': rev,
                    'name': name,
                })
        except (Executable.DoesNotExist, Revision.DoesNotExist):
            # TODO: write to server logs
            pass
    else:
        revs = Revision.objects.exclude(tag="")
        for rev in revs:
            #add executables that correspond to each tagged revision.
            executables = Executable.objects.filter(project=rev.project)
            for executable in executables:
                name = executable.name
                if executable.coptions != "default": name += " " + executable.coptions
                if rev.tag: name += " " + rev.tag
                else: name += " " + rev.commitid
                baseline.append({
                    'executable': executable,
                    'revision': rev,
                    'name': name,
                })
    # move default to first place
    if hasattr(settings, 'defaultbaseline') and settings.defaultbaseline != None:
        try:
            for base in baseline:
                if base['executable'] == settings.defaultbaseline['executable'] and base['revision'] == str(settings.defaultbaseline['revision']):
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

def getdefaultexecutable():
    default = None
    defaultproject = Project.objects.filter(isdefault=True)[0]
    if hasattr(settings, 'defaultexecutable') and settings.defaultexecutable != None:
        try:
            default = Executable.objects.get(id=settings.defaultexecutable)
        except Executable.DoesNotExist:
            pass
    if default == None: default = Executable.objects.filter(project=defaultproject)[0]
    
    return default

def gettimelinedata(request):
    if request.method != 'GET':
        return HttpResponseNotAllowed('GET')
    data = request.GET

    defaultproject = Project.objects.filter(isdefault=True)[0]

    timeline_list = {'error': 'None', 'timelines': []}
    executables = data['executables'].split(",")
    if executables[0] == "":
        timeline_list['error'] = "No executables selected"
        return HttpResponse(json.dumps( timeline_list ))

    benchmarks = []
    number_of_rev = data['revisions']
    if data['benchmark'] == 'grid':
        benchmarks = Benchmark.objects.all().order_by('name')
        number_of_rev = 15
    else:
        benchmarks.append(Benchmark.objects.get(id=data['benchmark']))
    
    baseline = getbaselineexecutables()
    if len(baseline): baseline = baseline[0]
    else: baseline = None
    baselinerev = None
    if data['baseline'] == "true":
        baselinerev = baseline['revision']
    defaultenvironment = getdefaultenvironment()
    for bench in benchmarks:
        append = False
        timeline = {}
        timeline['benchmark'] = bench.name
        timeline['benchmark_id'] = bench.id
        timeline['executables'] = {}
        results = []
        for executable in executables:
            resultquery = Result.objects.filter(
                    benchmark=bench
                ).filter(
                    executable=executable
                ).order_by('-revision__date')[:number_of_rev]
            results = []
            for res in resultquery:
                std_dev = ""
                if res.std_dev != None: std_dev = res.std_dev
                results.append(
                    [str(res.revision.date), res.value, std_dev, res.revision.commitid]
                )
            timeline['executables'][executable] = results
            if len(results): append = True
        if data['baseline'] == "true" and baseline != None and append:
            try:
                baselinevalue = Result.objects.get(
                    executable=baseline['executable'],
                    benchmark=bench,
                    revision=baselinerev,
                    environment=defaultenvironment
                ).value
            except Result.DoesNotExist:
                timeline['baseline'] = "None"
            else:
                end = results[0][0]
                start = results[len(results)-1][0]
                timeline['baseline'] = [
                    [str(start), baselinevalue],
                    [str(end), baselinevalue]
                ]
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
    defaultenvironment = getdefaultenvironment()
    if not defaultenvironment:
        return HttpResponse("You need to configure at least one Environment")
    defaultenvironment = defaultenvironment.id
    
    defaultproject = Project.objects.filter(isdefault=True)
    if not len(defaultproject):
        return HttpResponse("You need to configure at least one Project as default")
    else: defaultproject = defaultproject[0]
    
    baseline = getbaselineexecutables()
    
    defaultbaseline = True
    if data.has_key('baseline'):
        if data['baseline'] == "false":
            defaultbaseline = False
    if len(baseline): baseline = baseline[0]
    else: defaultbaseline = False
    
    defaultbenchmark = "grid"
    if data.has_key('benchmark'):
        if data['benchmark'] != defaultbenchmark:
            try:
                defaultbenchmark = int(data['benchmark'])
            except ValueError:
                defaultbenchmark = get_object_or_404(Benchmark, name=data['benchmark']).id
    
    if data.has_key('executables'):
        checkedexecutables = []
        for i in data['executables'].split(","):
            selected = Executable.objects.filter(id=int(i))
            if len(selected): checkedexecutables.append(selected[0])
    else:
        checkedexecutables = Executable.objects.filter(project=defaultproject)
    
    lastrevisions = [10, 50, 200, 1000]
    defaultlast = 200
    if data.has_key('revisions'):
        if int(data['revisions']) in lastrevisions:
            defaultlast = data['revisions']
    
    # Information for template
    executables = Executable.objects.filter(project=defaultproject)
    benchmarks = Benchmark.objects.all()
    hostlist = Environment.objects.all()
    return render_to_response('codespeed/timeline.html', {
        'checkedexecutables': checkedexecutables,
        'defaultbaseline': defaultbaseline,
        'baseline': baseline,
        'defaultbenchmark': defaultbenchmark,
        'defaultenvironment': defaultenvironment,
        'lastrevisions': lastrevisions,
        'defaultlast': defaultlast,
        'executables': executables,
        'benchmarks': benchmarks,
        'hostlist': hostlist
    })

def getoverviewtable(request):
    data = request.GET
    
    defaultproject = Project.objects.filter(isdefault=True)[0]
    executable = int(data["executable"])
    trendconfig = int(data["trend"])
    temp = data["revision"].split(" ")
    date = temp[0] + " " + temp[1]
    lastrevisions = Revision.objects.filter(
        project=defaultproject
    ).filter(date__lte=date).order_by('-date')[:trendconfig+1]
    lastrevision = lastrevisions[0]

    change_list = None
    pastrevisions = None
    if len(lastrevisions) > 1:
        changerevision = lastrevisions[1]
        change_list = Result.objects.filter(
            revision=changerevision
        ).filter(executable=executable)   
        pastrevisions = lastrevisions[trendconfig-2:trendconfig+1]

    result_list = Result.objects.filter(
        revision=lastrevision
    ).filter(executable=executable)
    
    # TODO: remove baselineflag
    baselineflag = False
    base_list = None
    baseexecutable = None
    if data.has_key("baseline"):
        if data['baseline'] != "undefined":
            baselineflag = True
            base = int(data['baseline']) - 1
            baseline = getbaselineexecutables()
            baseexecutable = baseline[base]
            base_list = Result.objects.filter(
                revision=baseline[base]['revision']
            ).filter(executable=baseline[base]['executable'])

    table_list = []
    totals = {'change': [], 'trend': [],}
    for bench in Benchmark.objects.all():
        resultquery = result_list.filter(benchmark=bench)
        if not len(resultquery): continue
        result = resultquery.filter(benchmark=bench)[0]
        std_dev = result.std_dev
        result = result.value
        
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
                    revision=rev
                ).filter(
                    executable=executable
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
            'std_dev': std_dev,
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
    defaultenvironment = getdefaultenvironment()
    if not defaultenvironment:
        return HttpResponse("You need to configure at least one Environment")
    defaultenvironment = defaultenvironment.id
    
    defaultproject = Project.objects.filter(isdefault=True)
    if not len(defaultproject):
        return HttpResponse("You need to configure at least one Project as default")
    else: defaultproject = defaultproject[0]

    defaultchangethres = 3
    defaulttrendthres = 3
    defaultcompthres = 0.2
    defaulttrend = 10
    trends = [5, 10, 20, 100]
    if data.has_key('trend'):
        if data['trend'] in trends:
            defaulttrend = int(request.GET['trend'])

    defaultexecutable = getdefaultexecutable().id
    if data.has_key("executable"):
        selected = Executable.objects.filter(id=int(data['executable']))
        if len(selected): defaultexecutable = selected[0].id
    
    baseline = getbaselineexecutables()
    defaultbaseline = 1
    if data.has_key("baseline"):
        if data['baseline'] != "undefined":
            defaultbaseline = int(request.GET['baseline'])
            if len(baseline) < defaultbaseline: defaultbaseline = 1
    
    # Information for template
    executables = Executable.objects.filter(project=defaultproject)
    lastrevisions = Revision.objects.filter(
        project=defaultproject
    ).order_by('-date')[:20]
    if not len(lastrevisions):
        response = 'No data found for project "' + defaultproject.name + '"'
        return HttpResponse(response)
    selectedrevision = lastrevisions[0]
    if data.has_key("revision"):
        # TODO: Create 404 html embeded in the overview
        commitid = data['revision'].split(" ")[-1]
        selectedrevision = get_object_or_404(
            Revision, commitid=commitid, project=defaultproject
        )
    hostlist = Environment.objects.all()
    return render_to_response('codespeed/overview.html', locals())

def displaylogs(request):
    defaultproject = Project.objects.filter(isdefault=True)[0]
    rev = Revision.objects.get(id=request.GET['revisionid'])
    logs = []
    logs.append(rev)
    remotelogs = getcommitlogs(rev)
    if len(remotelogs): logs = remotelogs
    return render_to_response('codespeed/overview_logs.html', { 'logs': logs })

def getlogsfromsvn(newrev, startrev):
    import pysvn
    logs = []
    loglimit = 200
    if startrev == newrev:
        start = startrev.commitid
    else:
        start = int(startrev.commitid) + 1
    
    client = pysvn.Client()
    log_message = \
        client.log(
            newrev.project.repository_path,
            revision_start=pysvn.Revision(
                    pysvn.opt_revision_kind.number, start
            ),
            revision_end=pysvn.Revision(
                pysvn.opt_revision_kind.number, newrev.commitid
            )
        )
    log_message.reverse()
    s = len(log_message)
    while s > loglimit:
        log_message = log_message[:s]
        s = len(log_message) - 1
    for log in log_message:
        try:
            author = log.author
        except AttributeError:
            author = ""
        date = datetime.fromtimestamp(log.date).strftime("%Y-%m-%d %H:%M:%S")
        message = log.message
        logs.append({'date': date, 'author': author, 'message': message, 'commitid': log.revision.number})
    return logs

def getcommitlogs(rev):
    logs = []
    defaultproject = Project.objects.filter(isdefault=True)[0]
    if rev.project.repository_type == 'N' or rev.project.repository_path == "":
        #Don't create logs
        return []
    
    startrev = Revision.objects.filter(
        project=defaultproject
    ).filter(
        branch='trunk'
    ).filter(date__lt=rev.date).order_by('-date')[:1]
    if not len(startrev): startrev = rev
    else: startrev = startrev[0]
    
    if rev.project.repository_type == 'S':
        logs = getlogsfromsvn(rev, startrev)
    return logs

def saverevisioninfo(rev):
    log = None
    if rev.project.repository_type == 'N' or rev.project.repository_path == "":
        #Don't create logs
        return
    elif rev.project.repository_type == 'S':
        log = getlogsfromsvn(rev, rev)
    if len(log):
        log = log[0]
        rev.author  = log['author']
        rev.date    = log['date']
        rev.message = log['message']
    else:
        rev.date = datetime.now()

def addresult(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed('POST')
    data = request.POST
    
    mandatory_data = [
        'commitid',
        'project',
        'executable_name',
        'executable_coptions',
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
    
    branch = 'trunk'
    if data.has_key('branch') and data['branch'] != "": branch = data['branch']
    rev, created = Revision.objects.get_or_create(
        commitid=data['commitid'],
        project=p,
        branch=branch,
    )
    
    if created:
        rev.date = data["result_date"]
        saverevisioninfo(rev)
        rev.save()        
    
    exe, created = Executable.objects.get_or_create(
        name=data['executable_name'],
        coptions=data['executable_coptions'],
        project=p
    )
    try:
        r = Result.objects.get(revision=rev,executable=exe,benchmark=b,environment=e)
    except Result.DoesNotExist:
        r = Result(revision=rev,executable=exe,benchmark=b,environment=e)
    r.value = data["result_value"]    
    r.date = data["result_date"]
    if data.has_key('std_dev'): r.std_dev = data['std_dev']
    if data.has_key('min'): r.val_min = data['min']
    if data.has_key('max'): r.val_max = data['max']
    r.save()
    
    return HttpResponse("Result data saved succesfully")
