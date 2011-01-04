# -*- coding: utf-8 -*-
from django.shortcuts import get_object_or_404, render_to_response
from codespeed.models import Project, Revision, Result, Executable, Benchmark, Environment
from django.http import HttpResponse, Http404, HttpResponseNotAllowed, HttpResponseBadRequest, HttpResponseNotFound
from codespeed import settings
from datetime import datetime
from time import sleep
import json
from itertools import chain

def no_environment_error():
    return render_to_response('codespeed/nodata.html', {
        'message': 'You need to configure at least one Environment. Please go to the <a href="../admin/codespeed/environment/">admin interface</a>'
    })

def no_default_project_error():
    return render_to_response('codespeed/nodata.html', {
        'message': 'You need to configure at least one one Project as default (checked "Track changes" field).<br />Please go to the <a href="../admin/codespeed/project/">admin interface</a>'
    })

def no_executables_error():
    return render_to_response('codespeed/nodata.html', {
        'message': 'There needs to be at least one executable'
    })

def getbaselineexecutables():
    baseline = [{'key': "none", 'name': "None", 'executable': "none", 'revision': "none"}]
    revs = Revision.objects.exclude(tag="")
    maxlen = 22
    for rev in revs:
        #add executables that correspond to each tagged revision.
        for exe in Executable.objects.filter(project=rev.project):
            exestring = str(exe)
            if len(exestring) > maxlen: exestring = str(exe)[0:maxlen] + "..."
            name = exestring + " " + rev.tag
            key = str(exe.id) + "+" + str(rev.id)
            baseline.append({
                'key': key,
                'executable': exe,
                'revision': rev,
                'name': name,
            })
    # move default to first place
    if hasattr(settings, 'defaultbaseline') and settings.defaultbaseline != None:
        try:
            for base in baseline:
                if base['key'] == "none": continue
                exename = settings.defaultbaseline['executable']
                commitid = settings.defaultbaseline['revision']
                if base['executable'].name == exename and base['revision'].commitid == commitid:
                    baseline.remove(base)
                    baseline.insert(1, base)
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
    if hasattr(settings, 'defaultexecutable') and settings.defaultexecutable != None:
        try:
            default = Executable.objects.get(name=settings.defaultexecutable)
        except Executable.DoesNotExist:
            pass
    if default == None:
        execquery = Executable.objects.filter(project__track=True)
        if len(execquery): default = execquery[0]
    
    return default

def getcomparisonexes():
    executables = []
    executablekeys = []
    maxlen = 20
    # add all tagged revs for any project
    for exe in getbaselineexecutables():
        if exe['key'] == "none": continue
        executablekeys.append(exe['key'])
        executables.append(exe)
    
    # add latest revs of tracked projects
    projects = Project.objects.filter(track=True)
    for proj in projects:
        rev = Revision.objects.filter(project=proj).latest('date')
        if rev.tag == "":
            for exe in Executable.objects.filter(project=rev.project):
                exestring = str(exe)
                if len(exestring) > maxlen: exestring = str(exe)[0:maxlen] + "..."
                name = exestring + " latest"
                key = str(exe.id) + "+L"
                executablekeys.append(key)
                executables.append({
                    'key': key,
                    'executable': exe,
                    'revision': rev,
                    'name': name,
                })
    
    return executables, executablekeys

def getcomparisondata(request):
    if request.method != 'GET': return HttpResponseNotAllowed('GET')
    data = request.GET
    
    executables, exekeys = getcomparisonexes()
    
    compdata = {}
    compdata['error'] = "Unknown error"
    for exe in executables:
        compdata[exe['key']] = {}
        for env in Environment.objects.all():
            compdata[exe['key']][env.id] = {}
            for bench in Benchmark.objects.all().order_by('name'):
                try:
                    value = Result.objects.get(
                        environment=env,
                        executable=exe['executable'],
                        revision=exe['revision'],
                        benchmark=bench
                    ).value
                except Result.DoesNotExist:
                    value = None
                compdata[exe['key']][env.id][bench.id] = value
    compdata['error'] = "None"
    
    return HttpResponse(json.dumps( compdata ))

def comparison(request):
    if request.method != 'GET': return HttpResponseNotAllowed('GET')
    data = request.GET
    
    # Configuration of default parameters
    defaultenvironment = getdefaultenvironment()
    if not defaultenvironment: return no_environment_error()
    if 'env' in data:
        try:
            defaultenvironment = Environment.objects.get(name=data['env'])
        except Environment.DoesNotExist:
            pass
    
    enviros = Environment.objects.all()
    checkedenviros = []
    if 'env' in data:
        for i in data['env'].split(","):
            if not i: continue
            try:
                checkedenviros.append(Environment.objects.get(id=int(i)))
            except Environment.DoesNotExist:
                pass
    if not checkedenviros:
        checkedenviros = enviros
    
    if not len(Project.objects.all()): return no_default_project_error()
    
    defaultexecutable = getdefaultexecutable()
    if not defaultexecutable: return no_executables_error()
    
    executables, exekeys = getcomparisonexes()
    checkedexecutables = []
    if 'exe' in data:
        for i in data['exe'].split(","):
            if not i: continue
            if i in exekeys:
                checkedexecutables.append(i)
    if not checkedexecutables:
        checkedexecutables = exekeys
    
    units_titles = Benchmark.objects.filter(
        benchmark_type="C"
    ).values('units_title').distinct()
    units_titles = [unit['units_title'] for unit in units_titles]
    benchmarks = {}
    bench_units = {}
    for unit in units_titles:
        # Only include benchmarks marked as cross-project
        benchmarks[unit] = Benchmark.objects.filter(benchmark_type="C").filter(units_title=unit)
        units = benchmarks[unit][0].units
        lessisbetter = benchmarks[unit][0].lessisbetter and ' (less is better)' or ' (more is better)'
        bench_units[unit] = [[b.id for b in benchmarks[unit]], lessisbetter, units]
    checkedbenchmarks = []
    if 'ben' in data:
        checkedbenchmarks = []
        for i in data['ben'].split(","):
            if not i: continue
            try:
                checkedbenchmarks.append(Benchmark.objects.get(id=int(i)))
            except Benchmark.DoesNotExist:
                pass
    if not checkedbenchmarks:
        # Only include benchmarks marked as cross-project
        checkedbenchmarks = Benchmark.objects.filter(benchmark_type="C")
    
    charts = ['normal bars', 'stacked bars', 'relative bars']
    # Don't show relative charts as an option if there is only one executable
    # Relative charts need normalization
    if len(executables) == 1: charts.remove('relative bars')
    
    selectedchart = charts[0]
    if 'chart' in data and data['chart'] in charts:
        selectedchart = data['chart']
    elif hasattr(settings, 'charttype') and settings.charttype in charts:
        selectedchart = settings.charttype
    
    selectedbaseline = "none"
    if 'bas' in data and data['bas'] in exekeys:
        selectedbaseline = data['bas']
    elif len(exekeys) > 1 and hasattr(settings, 'normalization') and settings.normalization:
        # Uncheck exe used for normalization when normalization is chosen as default in the settings
        selectedbaseline = exekeys[0]#this is the default baseline
        checkedexecutables.remove(selectedbaseline)        
    
    selecteddirection = False
    if 'hor' in data and data['hor'] == "true" or\
        hasattr(settings, 'chartorientation') and settings.chartorientation == 'horizontal':
        selecteddirection = True
    
    return render_to_response('codespeed/comparison.html', {
        'checkedexecutables': checkedexecutables,
        'checkedbenchmarks': checkedbenchmarks,
        'checkedenviros': checkedenviros,
        'defaultenvironment': defaultenvironment,
        'executables': executables,
        'benchmarks': benchmarks,
        'bench_units': json.dumps(bench_units),
        'enviros': enviros,
        'charts': charts,
        'selectedbaseline': selectedbaseline,
        'selectedchart': selectedchart,
        'selecteddirection': selecteddirection
    })

def gettimelinedata(request):
    if request.method != 'GET': return HttpResponseNotAllowed('GET')
    data = request.GET
    
    timeline_list = {'error': 'None', 'timelines': []}
    executables = data['exe'].split(",")
    if executables[0] == "":
        timeline_list['error'] = "No executables selected"
        return HttpResponse(json.dumps( timeline_list ))

    environment = Environment.objects.get(name=data['env'])
    benchmarks = []
    number_of_rev = data['revs']
    if data['ben'] == 'grid':
        benchmarks = Benchmark.objects.all().order_by('name')
        number_of_rev = 15
    else:
        benchmarks.append(Benchmark.objects.get(name=data['ben']))
        number_of_rev = int(number_of_rev)


    resultData = {}
    for result in Result.objects.filter(environment=environment):
        key = (result.benchmark_id, result.executable_id)
        resultData.setdefault(key, []).append(result)
    dates = {}
    commitids = {}
    for revision in Revision.objects.all():
        dates[revision.id] = revision.date
        commitids[revision.id] = revision.commitid

    baselinerev = None
    baselineexe = None
    if data['base'] != "none" and data['base'] != 'undefined':
        exeid, revid = data['base'].split("+")
        baselinerev = Revision.objects.get(id=revid)
        baselineexe = Executable.objects.get(id=exeid)
    for bench in benchmarks:
        append = False
        timeline = {}
        timeline['benchmark'] = bench.name
        timeline['benchmark_id'] = bench.id
        timeline['units'] = bench.units
        lessisbetter = bench.lessisbetter and ' (less is better)' or ' (more is better)'
        timeline['lessisbetter'] = lessisbetter
        timeline['executables'] = {}
        timeline['baseline'] = "None"
        
        for executable in executables:
            resultquery = resultData.get((bench.id, int(executable)))
            if not resultquery:
                continue
            resultquery.sort(key=lambda result: dates[result.revision_id])
            resultquery.reverse()
            del resultquery[number_of_rev:]

            results = []
            for res in resultquery:
                std_dev = ""
                if res.std_dev != None: std_dev = res.std_dev
                results.append([
                        str(dates[res.revision_id]),
                        res.value, std_dev,
                        str(commitids[res.revision_id])])

            timeline['executables'][executable] = results
            append = True
        if baselinerev != None and append:
            try:
                baselinevalue = resultData[bench, baselineexe].value
            except KeyError:
                timeline['baseline'] = "None"
            else:
                # determine start and end revision (x axis) from longest data series
                results = []
                for exe in timeline['executables']:
                    if len(timeline['executables'][exe]) > len(results):
                        results = timeline['executables'][exe]
                end = results[0][0]
                start = results[len(results)-1][0]
                timeline['baseline'] = [
                    [str(start), baselinevalue],
                    [str(end), baselinevalue]
                ]
        if append: timeline_list['timelines'].append(timeline)
    
    if not len(timeline_list['timelines']):
        response = 'No data found for the selected options'
        timeline_list['error'] = response

    return HttpResponse(json.dumps( timeline_list ))

def timeline(request):
    if request.method != 'GET': return HttpResponseNotAllowed('GET')
    data = request.GET
    
    # Configuration of default parameters
    defaultenvironment = getdefaultenvironment()
    if not defaultenvironment: return no_environment_error()
    if 'env' in data:
        try:
            defaultenvironment = Environment.objects.get(name=data['env'])
        except Environment.DoesNotExist:
            pass
    
    defaultproject = Project.objects.filter(track=True)
    if not len(defaultproject): return no_default_project_error()
    else: defaultproject = defaultproject[0]
    
    checkedexecutables = []
    if 'exe' in data:
        for i in data['exe'].split(","):
            if not i: continue
            try:
                checkedexecutables.append(Executable.objects.get(id=int(i)))
            except Executable.DoesNotExist:
                pass
    if not checkedexecutables:
        checkedexecutables = Executable.objects.filter(project__track=True)
    
    if not len(checkedexecutables): return no_executables_error()
    
    baseline = getbaselineexecutables()
    defaultbaseline = None
    if len(baseline) > 1:
        defaultbaseline = str(baseline[1]['executable'].id) + "+"
        defaultbaseline += str(baseline[1]['revision'].id)
    if "base" in data and data['base'] != "undefined":
        try:
            defaultbaseline = data['base']
        except ValueError:
            pass
    
    lastrevisions = [10, 50, 200, 1000]
    defaultlast = 200
    if 'revs' in data:
        if int(data['revs']) not in lastrevisions:
            lastrevisions.append(data['revs'])
        defaultlast = data['revs']
    
    benchmarks = Benchmark.objects.all()
    if len(benchmarks) > 1: defaultbenchmark = "grid"
    else: defaultbenchmark = benchmarks[0]
    
    if 'ben' in data and data['ben'] != defaultbenchmark:
        defaultbenchmark = get_object_or_404(Benchmark, name=data['ben'])
    
    # Information for template
    executables = Executable.objects.filter(project__track=True)
    environments = Environment.objects.all()
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
        'environments': environments
    })

def getchangestable(request):
    data = request.GET
    
    executable = Executable.objects.get(id=int(data['exe']))
    environment = Environment.objects.get(name=data['env'])
    trendconfig = int(data['tre'])
    selectedrev = Revision.objects.get(
        commitid=data['rev'], project=executable.project
    )
    date = selectedrev.date
    lastrevisions = Revision.objects.filter(
        project=executable.project
    ).filter(
        date__lte=date
    ).order_by('-date')[:trendconfig+1]
    lastrevision = lastrevisions[0]

    change_list = []
    pastrevisions = []
    if len(lastrevisions) > 1:
        changerevision = lastrevisions[1]
        change_list = Result.objects.filter(
            revision=changerevision
        ).filter(
            environment=environment
        ).filter(
            executable=executable
        )
        pastrevisions = lastrevisions[trendconfig-2:trendconfig+1]

    result_list = Result.objects.filter(
        revision=lastrevision
    ).filter(
        environment=environment
    ).filter(
        executable=executable
    )

    tablelist = []
    for units in Benchmark.objects.all().values('units').distinct():
        currentlist = []
        units_title = ""
        hasmin = False
        hasmax = False
        smallest = 1000
        totals = {'change': [], 'trend': [],}
        for bench in Benchmark.objects.filter(units=units['units']):
            units_title = bench.units_title
            lessisbetter = bench.lessisbetter
            resultquery = result_list.filter(benchmark=bench)
            if not len(resultquery): continue
            resobj = resultquery.filter(benchmark=bench)[0]
            std_dev = resobj.std_dev
            result = resobj.value
            val_min = resobj.val_min
            if val_min is not None: hasmin = True
            else: val_min = "-"
            val_max = resobj.val_max
            if val_max is not None: hasmax = True
            else: val_max = "-"
            
            # Calculate percentage change relative to previous result
            change = "-"
            if len(change_list):
                c = change_list.filter(benchmark=bench)
                if c.count() and c[0].value and result:
                    change = (result - c[0].value)*100/c[0].value
                    totals['change'].append(result / c[0].value)
            
            # Calculate trend:
            # percentage change relative to average of 3 previous results
            # Calculate past average
            average = 0
            averagecount = 0
            if len(pastrevisions):
                for rev in pastrevisions:
                    past_rev = Result.objects.filter(
                        revision=rev
                    ).filter(
                        environment=environment
                    ).filter(
                        executable=executable
                    ).filter(benchmark=bench)
                    if past_rev.count():
                        average += past_rev[0].value
                        averagecount += 1
            trend = "-"
            if average:
                average = average / averagecount
                trend =  (result - average)*100/average
                totals['trend'].append(result / average)
            
            # Retain lowest number different than 0
            # to be used later for calculating significant digits
            if result < smallest and result:
                smallest = result
            
            currentlist.append({
                'benchmark': bench,
                'result': result,
                'std_dev': std_dev,
                'val_min': val_min,
                'val_max': val_max,
                'change': change,
                'trend': trend
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
        
        # Calculate significant digits
        digits = 2;
        while smallest < 1:
            smallest *= 10
            digits += 1
        
        tablelist.append({
            'units': units['units'],
            'units_title': units_title,
            'lessisbetter': lessisbetter,
            'hasmin': hasmin,
            'hasmax': hasmax,
            'precission': digits,
            'totals': totals,
            'rows': currentlist
        })

    if not len(tablelist):
        return HttpResponse('<table id="results" class="tablesorter" style="height: 232px;"></table><p class="errormessage">No results for this parameters</p>')
    
    return render_to_response('codespeed/changes_table.html', {
        'tablelist': tablelist,
        'trendconfig': trendconfig,
        'executable': executable,
        'lastrevision': lastrevision,
        'totals': totals,
        'rev': selectedrev,
        'exe': executable,
        'env': environment,
    })
    
def changes(request):
    if request.method != 'GET': return HttpResponseNotAllowed('GET')
    data = request.GET

    # Configuration of default parameters
    defaultchangethres = 3
    defaulttrendthres = 3
    defaulttrend = 10
    trends = [5, 10, 20, 50, 100]
    if 'tre' in data and int(data['tre']) in trends:
        defaulttrend = int(data['tre'])
    
    defaultenvironment = getdefaultenvironment()
    if not defaultenvironment: return no_environment_error()
    if 'env' in data:
        try:
            defaultenvironment = Environment.objects.get(name=data['env'])
        except Environment.DoesNotExist:
            pass
    environments = Environment.objects.all()
    
    defaultproject = Project.objects.filter(track=True)
    if not len(defaultproject): return no_default_project_error()
    else: defaultproject = defaultproject[0]
    
    defaultexecutable = getdefaultexecutable()
    if not defaultexecutable: return no_executables_error()
    
    if "exe" in data:
        try:
            defaultexecutable = Executable.objects.get(id=int(data['exe']))
        except Executable.DoesNotExist:
            pass
        except ValueError:
            pass
    
    baseline = getbaselineexecutables()
    defaultbaseline = "+"
    if len(baseline) > 1:
        defaultbaseline = str(baseline[1]['executable'].id) + "+"
        defaultbaseline += str(baseline[1]['revision'].id)
    if "base" in data and data['base'] != "undefined":
        try:
            defaultbaseline = data['base']
        except ValueError:
            pass
    
    # Information for template
    executables = Executable.objects.filter(project__track=True)
    revlimit = 20
    lastrevisions = Revision.objects.filter(
        project=defaultexecutable.project
    ).order_by('-date')[:revlimit]
    if not len(lastrevisions):
        response = 'No data found for project "' + str(defaultexecutable.project) + '"'
        return HttpResponse(response)
    selectedrevision = lastrevisions[0]
    if "rev" in data:
        commitid = data['rev']
        try:
            selectedrevision = Revision.objects.get(
                commitid=commitid, project=defaultexecutable.project
            )
            if not selectedrevision in lastrevisions:
                lastrevisions = list(chain(lastrevisions))
                lastrevisions.append(selectedrevision)
        except Revision.DoesNotExist:
            selectedrevision = lastrevisions[0]
    
    # This variable is used to know when the newly selected executable
    # belongs to another project (project changed) and then trigger the
    # repopulation of the revision selection selectbox
    projectmatrix = {}
    for e in executables: projectmatrix[e.id] = e.project.name
    projectmatrix = json.dumps(projectmatrix)
    projectlist = []
    for p in Project.objects.filter(
            track=True
        ).exclude(
            id=defaultexecutable.project.id
        ):
        projectlist.append(p)
    revisionboxes = { defaultexecutable.project.name: lastrevisions }
    for p in projectlist:
        revisionboxes[p.name] = Revision.objects.filter(
            project=p
        ).order_by('-date')[:revlimit]
    return render_to_response('codespeed/changes.html', locals())

def displaylogs(request):
    rev = Revision.objects.get(id=request.GET['revisionid'])
    logs = []
    logs.append(rev)
    error = False
    remotelogs = getcommitlogs(rev)
    if len(remotelogs):
        try:
            if remotelogs[0]['error']:
                error = remotelogs[0]['message']
        except KeyError:
            pass#no errors
        logs = remotelogs
    else: error = 'no logs found'
    return render_to_response('codespeed/changes_logs.html', { 'error': error, 'logs': logs })

def getlogsfromsvn(newrev, startrev):
    import pysvn
    logs = []
    log_messages = []
    loglimit = 200
    if startrev == newrev:
        start = startrev.commitid
    else:
        #don't show info corresponding to previously tested revision
        start = int(startrev.commitid) + 1
    
    def get_login(realm, username, may_save):
        return True, newrev.project.repo_user, newrev.project.repo_pass, False
    
    client = pysvn.Client()
    if newrev.project.repo_user != "":
        client.callback_get_login = get_login
    try:
        log_messages = \
            client.log(
                newrev.project.repo_path,
                revision_start=pysvn.Revision(
                        pysvn.opt_revision_kind.number, start
                ),
                revision_end=pysvn.Revision(
                    pysvn.opt_revision_kind.number, newrev.commitid
                )
            )
    except pysvn.ClientError:
        return [{'error': True, 'message': "Could not resolve '" + newrev.project.repo_path + "'"}]
    log_messages.reverse()
    s = len(log_messages)
    while s > loglimit:
        log_messages = log_messages[:s]
        s = len(log_messages) - 1
    for log in log_messages:
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
    if rev.project.repo_type == 'N' or rev.project.repo_path == "":
        #Don't create logs
        return []
    
    startrev = Revision.objects.filter(
        project=rev.project
    ).filter(date__lt=rev.date).order_by('-date')[:1]
    if not len(startrev): startrev = rev
    else: startrev = startrev[0]
    
    if rev.project.repo_type == 'S':
        logs = getlogsfromsvn(rev, startrev)
    return logs

def saverevisioninfo(rev):
    log = None
    if rev.project.repo_type == 'N' or rev.project.repo_path == "":
        #Don't create logs
        return
    elif rev.project.repo_type == 'S':
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
        'executable',
        'benchmark',
        'environment',
        'result_value',
    ]
    
    for key in mandatory_data:
        if not key in data:
            return HttpResponseBadRequest('Key "' + key + '" missing from request')
        elif key in data and data[key] == "":
            return HttpResponseBadRequest('Key "' + key + '" empty in request')

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
    )
    if created:
        if 'revision_date' in data: rev.date = data["revision_date"]
        else:
            try:
                saverevisioninfo(rev)
            except:
                pass
        if not rev.date:
            temp = datetime.today()
            rev.date = datetime(temp.year, temp.month, temp.day, temp.hour, temp.minute, temp.second)

        rev.save()
    
    exe, created = Executable.objects.get_or_create(
        name=data['executable'],
        project=p
    )
    
    try:
        r = Result.objects.get(revision=rev,executable=exe,benchmark=b,environment=e)
    except Result.DoesNotExist:
        r = Result(revision=rev,executable=exe,benchmark=b,environment=e)
    r.value = data["result_value"]    
    if 'result_date' in data: r.date = data["result_date"]
    else: r.date = rev.date
    if 'std_dev' in data: r.std_dev = data['std_dev']
    if 'min' in data: r.val_min = data['min']
    if 'max' in data: r.val_max = data['max']
    r.save()
    
    return HttpResponse("Result data saved succesfully")
