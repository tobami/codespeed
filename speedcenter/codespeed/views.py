# -*- coding: utf-8 -*-
from django.shortcuts import get_object_or_404, render_to_response
from codespeed.models import Project, Revision, Result, Executable, Benchmark, Environment
from django.http import HttpResponse, Http404, HttpResponseNotAllowed, HttpResponseBadRequest, HttpResponseNotFound
from codespeed import settings
from datetime import datetime
from time import sleep
import json, pysvn


def getbaselineexecutables():
    baseline = []
    if hasattr(settings, 'baselinelist'):
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
                shortname = executable.name
                #if executable.coptions != "default":
                    #shortname += " " + executable.coptions
                name = executable.name + " " + executable.coptions
                if rev.tag: name += " " + rev.tag
                else: name += " " + rev.commitid
                baseline.append({
                    'executable': executable.id,
                    'name': name,
                    'shortname': shortname,
                    'revision': rev.commitid,
                    'project': rev.project,
                })
        except (Executable.DoesNotExist, Revision.DoesNotExist):
            # TODO: write to server logs
            pass
    else:
        revs = Revision.objects.exclude(tag="")
        executables = Executable.objects.all()
        for rev in revs:
            #add executables that correspond to each tagged revision.
            for executable in executables:
                if executable.project == rev.project:
                    shortname = executable.name
                    #if executable.coptions != "default":
                        #shortname += " " + executable.coptions
                    name = executable.name + " " + executable.coptions
                    if rev.tag: name += " " + rev.tag
                    else: name += " " + str(rev.commitid)
                    baseline.append({
                        'executable': executable.id,
                        'name': name,
                        'shortname': shortname,
                        'revision': rev.commitid,
                        'project': rev.project,
                    })
    # move default to first place
    if hasattr(settings, 'defaultbaseline'):
        try:
            for base in baseline:
                if base['executable'] == settings.defaultbaseline['executable'] and base['revision'] == settings.defaultbaseline['revision']:
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

def getdefaultexecutables():
    default = []
    defaultproject = Project.objects.filter(isdefault=True)[0]
    if hasattr(settings, 'defaultexecutables'):
        try:
            for executable in settings.defaultexecutables:
                i = Executable.objects.get(id=executable)
                default.append(executable)
        except Executable.DoesNotExist:
            i_list = Executable.objects.filter(project=defaultproject)
            for i in i_list:
                default.append(i.id)
    else:
        i_list = Executable.objects.filter(project=defaultproject)
        for i in i_list:
            default.append(i.id)
    
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
        timeline['executables'] = {}
        if data['baseline'] == "true" and len(baseline):
            timeline['baseline'] = Result.objects.get(
                executable=baseline['executable'],
                benchmark=bench,
                revision=baselinerev
            ).value
        for executable in executables:
            resultquery = Result.objects.filter(
                    benchmark=bench
                ).filter(
                    executable=executable
                ).order_by('-revision__commitid')[:number_of_rev]
            results = []
            for res in resultquery:
                results.append([res.revision.commitid, res.value])
            timeline['executables'][executable] = results
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
    
    defaultexecutables = getdefaultexecutables()
    if data.has_key("executables"):
        defaultexecutables = []
        for i in data["executables"].split(","):
            selected = Executable.objects.filter(id=int(i))
            if len(selected): defaultexecutables.append(selected[0].id)
    
    lastrevisions = [10, 50, 200, 1000]
    defaultlast = 200
    if data.has_key("revisions"):
        if int(data["revisions"]) in lastrevisions:
            defaultlast = data["revisions"]
    
    # Information for template
    executables = Executable.objects.filter(project=defaultproject)
    benchmarks = Benchmark.objects.all()
    hostlist = Environment.objects.all()
    return render_to_response('codespeed/timeline.html', {
        'defaultexecutables': defaultexecutables,
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
            p = Project.objects.get(name=baseline[base]['project'])
            base_list = Result.objects.filter(
                revision__commitid=baseline[base]['revision']
            ).filter(
                revision__project=p
            ).filter(executable=baseline[base]['executable'])

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

    defaultexecutable = getdefaultexecutables()
    if len(defaultexecutable): defaultexecutable = defaultexecutable[0]
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
    logs = []
    loglimit = 200
    client = pysvn.Client()
    log_message = \
        client.log(
            newrev.project.repository_path,
            revision_start=pysvn.Revision(
                pysvn.opt_revision_kind.number, startrev.commitid
            ),
            revision_end=pysvn.Revision(
                pysvn.opt_revision_kind.number, newrev.commitid
            )
        )
    s = len(log_message) - loglimit
    log_message = log_message[s:]
    for log in log_message:
        try:
            author = log.author
        except AttributeError:
            author = ""
        date = datetime.fromtimestamp(log.date).strftime("%Y-%m-%d %H:%M:%S")
        message = log.message
        logs.append({'date': date, 'author': author, 'message': message, 'commitid': log.revision.number})
    if len(logs) != 1: del(logs[0])
    logs.reverse()
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

def addresult(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed('POST')
    data = request.POST
    
    mandatory_data = [
        'commitid',
        'project',
        'branch',
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
    rev, created = Revision.objects.get_or_create(
        commitid=data['commitid'],
        project=p,
        branch=data['branch'],
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
    r, created = Result.objects.get_or_create(
            value=data["result_value"],
            revision=rev,
            executable=exe,
            benchmark=b,
            environment=e
    )
    
    r.date = data["result_date"]
    if data.has_key('std_dev'): r.std_dev = data['std_dev']
    if data.has_key('min'): r.val_min = data['min']
    if data.has_key('max'): r.val_max = data['max']
    r.save()
    
    return HttpResponse("Result data saved succesfully")
