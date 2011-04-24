# -*- coding: utf-8 -*-
from datetime import datetime
from itertools import chain
import json
import logging

from django.http import HttpResponse, Http404, HttpResponseNotAllowed, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.db.models import Q

from speedcenter.codespeed import settings
from speedcenter.codespeed.models import Environment, Report
from speedcenter.codespeed.models import Project, Revision, Result, Executable, Benchmark, Branch


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

def no_data_found():
    return render_to_response('codespeed/nodata.html', {
        'message': 'No data found'
    })

def getbaselineexecutables():
    baseline = [{'key': "none", 'name': "None", 'executable': "none", 'revision': "none"}]
    revs = Revision.objects.exclude(tag="")
    maxlen = 22
    for rev in revs:
        #add executables that correspond to each tagged revision.
        for exe in Executable.objects.filter(project=rev.branch.project):
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
    if hasattr(settings, 'def_baseline') and settings.def_baseline != None:
        try:
            for base in baseline:
                if base['key'] == "none":
                    continue
                exename = settings.def_baseline['executable']
                commitid = settings.def_baseline['revision']
                if base['executable'].name == exename and base['revision'].commitid == commitid:
                    baseline.remove(base)
                    baseline.insert(1, base)
                    break
        except KeyError:
            # TODO: write to server logs
            #error in settings.def_baseline
            pass
    return baseline

def getdefaultenvironment():
    default = Environment.objects.all()
    if not len(default):
        return 0
    default = default[0]
    if hasattr(settings, 'def_environment'):
        try:
            default = Environment.objects.get(name=settings.def_environment)
        except Environment.DoesNotExist:
            pass
    return default

def getdefaultexecutable():
    default = None
    if hasattr(settings, 'def_executable') and settings.def_executable != None:
        try:
            default = Executable.objects.get(name=settings.def_executable)
        except Executable.DoesNotExist:
            pass
    if default == None:
        execquery = Executable.objects.filter(project__track=True)
        if len(execquery):
            default = execquery[0]

    return default

def getcomparisonexes(proj):
    executables = []
    executablekeys = []
    maxlen = 20
    # add all tagged revs for any project
    for exe in getbaselineexecutables():
        if exe['key'] == "none":
            continue
        executablekeys.append(exe['key'])
        executables.append(exe)

    # add latest revs of tracked projects
    #projects = Project.objects.filter(track=True)
    branches = Branch.objects.filter(project=proj)
    for branch in branches:
        try:
            rev = Revision.objects.filter(branch=branch).latest('date')
        except Revision.DoesNotExist:
            continue
        if rev.tag == "":
            for exe in Executable.objects.filter(project=proj):
                exestring = str(exe)
                if len(exestring) > maxlen:
                    exestring = str(exe)[0:maxlen] + "..."
                if branch.name == 'trunk':
                    name = exestring + " latest trunk"
                else:
                    name = exestring + " latest " + branch.name + " branch"
                key = str(exe.id) + "+L" + branch.name
                executablekeys.append(key)
                executables.append({
                    'key': key,
                    'executable': exe,
                    'revision': rev,
                    'name': name,
                })
    return executables, executablekeys

def getcomparisondata(request):
    if request.method != 'GET':
        return HttpResponseNotAllowed('GET')
    data = request.GET

    executables = {}
    exekeys = []
    for project in Project.objects.filter(track=True):
        executables[project], exekeys_project = getcomparisonexes(project)
        exekeys += exekeys_project
        
    compdata = {}
    compdata['error'] = "Unknown error"
    for proj in executables:
        for exe in executables[proj]:
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
    if request.method != 'GET':
        return HttpResponseNotAllowed('GET')
    data = request.GET

    # Configuration of default parameters
    defaultenvironment = getdefaultenvironment()
    if not defaultenvironment:
        return no_environment_error()
    if 'env' in data:
        try:
            defaultenvironment = Environment.objects.get(name=data['env'])
        except Environment.DoesNotExist:
            pass

    enviros = Environment.objects.all()
    checkedenviros = []
    if 'env' in data:
        for i in data['env'].split(","):
            if not i:
                continue
            try:
                checkedenviros.append(Environment.objects.get(id=int(i)))
            except Environment.DoesNotExist:
                pass
    if not checkedenviros:
        checkedenviros = enviros

    if not len(Project.objects.all()):
        return no_default_project_error()

    defaultexecutable = getdefaultexecutable()

    if not defaultexecutable:
        return no_executables_error()

    executables = {}
    exekeys = []
    for project in Project.objects.filter(track=True):
        executables[project], exekeys_project = getcomparisonexes(project)
        exekeys += exekeys_project

    checkedexecutables = []
    if 'exe' in data:
        for i in data['exe'].split(","):
            if not i:
                continue
            if i in exekeys:
                checkedexecutables.append(i)
    elif hasattr(settings, 'comp_executables') and\
        settings.comp_executables:
        for exe, rev in settings.comp_executables:
            try:
                exe = Executable.objects.get(name=exe)
                key = str(exe.id) + "+"
                if rev == "L":
                    key += rev
                else:
                    rev = Revision.objects.get(commitid=rev)
                    key += str(rev.id)
                if key in exekeys:
                    checkedexecutables.append(key)
                else:
                    #TODO: log
                    pass
            except Executable.DoesNotExist:
                #TODO: log
                pass
            except Revision.DoesNotExist:
                #TODO: log
                pass

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
        benchmarks[unit] = Benchmark.objects.filter(
            benchmark_type="C"
        ).filter(units_title=unit)
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
    elif hasattr(settings, 'chart_type') and settings.chart_type in charts:
        selectedchart = settings.chart_type

    selectedbaseline = "none"
    if 'bas' in data and data['bas'] in exekeys:
        selectedbaseline = data['bas']
    elif 'bas' in data:
        # bas is present but is none
        pass
    elif len(exekeys) > 1 and hasattr(settings, 'normalization') and\
        settings.normalization:
        # Uncheck exe used for normalization when normalization is chosen as default in the settings
        selectedbaseline = exekeys[0]#this is the default baseline
        try:
            checkedexecutables.remove(selectedbaseline)
        except ValueError:
            pass#the selected baseline was not checked

    selecteddirection = False
    if 'hor' in data and data['hor'] == "true" or\
        hasattr(settings, 'chart_orientation') and settings.chart_orientation == 'horizontal':
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
    }, context_instance=RequestContext(request))

def gettimelinedata(request):
    if request.method != 'GET':
        return HttpResponseNotAllowed('GET')
    data = request.GET

    timeline_list = {'error': 'None', 'timelines': []}

    executables = data.get('exe', "").split(",")
    if not filter(None, executables):
        timeline_list['error'] = "No executables selected"
        return HttpResponse(json.dumps( timeline_list ))

    environment = get_object_or_404(Environment, name=data.get('env'))

    benchmarks = []
    number_of_revs = data.get('revs', 10)

    if data['ben'] == 'grid':
        benchmarks = Benchmark.objects.all().order_by('name')
        number_of_revs = 15
    else:
        benchmarks = [get_object_or_404(Benchmark, name=data['ben'])]

    baselinerev = None
    baselineexe = None
    if data.get('base') not in (None, 'none', 'undefined'):
        exeid, revid = data['base'].split("+")
        baselinerev = Revision.objects.get(id=revid)
        baselineexe = Executable.objects.get(id=exeid)
    for bench in benchmarks:
        lessisbetter = bench.lessisbetter and ' (less is better)' or ' (more is better)'
        timeline = {
            'benchmark':             bench.name,
            'benchmark_id':          bench.id,
            'benchmark_description': bench.description,
            'units':                 bench.units,
            'lessisbetter':          lessisbetter,
            'branches':              {},
            'baseline':              "None",
        }
        for branch in data.get('bran', '').split(','):
            append = False
            timeline['branches'][branch] = {}
            for executable in executables:
                resultquery = Result.objects.filter(
                        benchmark=bench
                    ).filter(
                        environment=environment
                    ).filter(
                        executable=executable
                    ).filter(
                        revision__branch__name=branch
                    ).select_related(
                        "revision"
                    ).order_by('-revision__date')[:number_of_revs]
                if not len(resultquery):
                    continue
    
                results = []
                for res in resultquery:
                    std_dev = ""
                    if res.std_dev != None:
                        std_dev = res.std_dev
                    results.append(
                        [str(res.revision.date), res.value, std_dev, res.revision.get_short_commitid(), branch]
                    )
                timeline['branches'][branch][executable] = results
                append = True
            if baselinerev != None and append:
                try:
                    baselinevalue = Result.objects.get(
                        executable=baselineexe,
                        benchmark=bench,
                        revision=baselinerev,
                        environment=environment
                    ).value
                except Result.DoesNotExist:
                    timeline['baseline'] = "None"
                else:
                    # determine start and end revision (x axis) from longest data series
                    results = []
                    for exe in timeline['branches'][branch]['executables']:
                        if len(timeline['branches'][branch]['executables'][exe]) > len(results):
                            results = timeline['branches'][branch]['executables'][exe]
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
    if request.method != 'GET':
        return HttpResponseNotAllowed('GET')
    data = request.GET

    # Configuration of default parameters
    defaultenvironment = getdefaultenvironment()
    if not defaultenvironment:
        return no_environment_error()
    if 'env' in data:
        try:
            defaultenvironment = Environment.objects.get(name=data['env'])
        except Environment.DoesNotExist:
            pass

    defaultproject = Project.objects.filter(track=True)
    if not len(defaultproject):
        return no_default_project_error()
    else:
        defaultproject = defaultproject[0]

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

    if not len(checkedexecutables):
        return no_executables_error()

    branch_list = [
        branch.name for branch in Branch.objects.filter(project=defaultproject)]
    branch_list.sort()
    
    defaultbranch = ""
    if "trunk" in branch_list:
        defaultbranch = "trunk"
    if data.get('bran') in branch_list:
        defaultbranch = data.get('bran')

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
    if not len(benchmarks):
        return no_data_found()
    elif len(benchmarks) == 1:
        defaultbenchmark = benchmarks[0]
    else:
        defaultbenchmark = "grid"

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
        'environments': environments,
        'branch_list': branch_list,
        'defaultbranch': defaultbranch
    }, context_instance=RequestContext(request))

def getchangestable(request):
    executable = get_object_or_404(Executable, pk=request.GET.get('exe'))
    environment = get_object_or_404(Environment, name=request.GET.get('env'))
    try:
        trendconfig = int(request.GET.get('tre'))
    except TypeError:
        raise Http404()
    selectedrev = get_object_or_404(Revision, commitid=request.GET.get('rev'),
                                    branch__project=executable.project)

    report, created = Report.objects.get_or_create(
        executable=executable, environment=environment, revision=selectedrev
    )
    tablelist = report.get_changes_table(trendconfig)

    if not len(tablelist):
        return HttpResponse('<table id="results" class="tablesorter" style="height: 232px;"></table><p class="errormessage">No results for this parameters</p>')

    return render_to_response('codespeed/changes_table.html', {
        'tablelist': tablelist,
        'trendconfig': trendconfig,
        'rev': selectedrev,
        'exe': executable,
        'env': environment,
    }, context_instance=RequestContext(request))

def changes(request):
    if request.method != 'GET': return HttpResponseNotAllowed('GET')
    data = request.GET

    # Configuration of default parameters
    defaultchangethres = 3.0
    defaulttrendthres = 4.0
    if hasattr(settings, 'change_threshold') and settings.change_threshold != None:
        defaultchangethres = settings.change_threshold
    if hasattr(settings, 'trend_threshold') and settings.trend_threshold != None:
        defaulttrendthres = settings.trend_threshold

    defaulttrend = 10
    trends = [5, 10, 20, 50, 100]
    if 'tre' in data and int(data['tre']) in trends:
        defaulttrend = int(data['tre'])

    defaultenvironment = getdefaultenvironment()
    if not defaultenvironment:
        return no_environment_error()
    if 'env' in data:
        try:
            defaultenvironment = Environment.objects.get(name=data['env'])
        except Environment.DoesNotExist:
            pass
    environments = Environment.objects.all()

    defaultproject = Project.objects.filter(track=True)
    if not len(defaultproject):
        return no_default_project_error()
    else:
        defaultproject = defaultproject[0]

    defaultexecutable = getdefaultexecutable()
    if not defaultexecutable:
        return no_executables_error()

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
        Q(branch__project=defaultexecutable.project),
        Q(branch__name="trunk") | Q(branch__name="")
    ).order_by('-date')[:revlimit]
    if not len(lastrevisions):
        return no_data_found()

    selectedrevision = lastrevisions[0]

    if "rev" in data:
        commitid = data['rev']
        try:
            selectedrevision = Revision.objects.get(
                commitid=commitid, branch__project=defaultexecutable.project
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
            branch__project=p
        ).order_by('-date')[:revlimit]
        
    return render_to_response('codespeed/changes.html', locals(), context_instance=RequestContext(request))


def reports(request):
    if request.method != 'GET':
        return HttpResponseNotAllowed('GET')

    return render_to_response('codespeed/reports.html', {
        'reports': Report.objects.filter(
                                     Q(revision__branch__name='trunk') |
                                     Q(revision__branch__name='')
                                     ).order_by('-revision__date')[:10],
    }, context_instance=RequestContext(request))

def displaylogs(request):
    rev = get_object_or_404(Revision, pk=request.GET.get('revisionid'))
    logs = []
    logs.append(rev)
    error = False
    try:
        startrev = Revision.objects.filter(
            project=rev.branch.project
        ).filter(date__lt=rev.date).order_by('-date')[:1]

        if not len(startrev):
            startrev = rev
        else:
            startrev = startrev[0]

        remotelogs = getcommitlogs(rev, startrev)
        if len(remotelogs):
            try:
                if remotelogs[0]['error']:
                    error = remotelogs[0]['message']
            except KeyError:
                pass#no errors
            logs = remotelogs
        else:
            error = 'no logs found'
    except StandardError, e:
        logging.error("Unhandled exception displaying logs for %s: %s", rev, e, exc_info=True)
        error = repr(e)

    return render_to_response('codespeed/changes_logs.html',
                                {'error': error, 'logs': logs },
                                context_instance=RequestContext(request))

def getcommitlogs(rev, startrev, update=False):
    logs = []

    if rev.branch.project.repo_type == 'S':
        from subversion import getlogs, updaterepo
    elif rev.branch.project.repo_type == 'M':
        from mercurial import getlogs, updaterepo
    elif rev.branch.project.repo_type == 'G':
        from git import getlogs, updaterepo
    elif rev.branch.project.repo_type == 'H':
        from github import getlogs, updaterepo
    else:
        if rev.branch.project.repo_type not in ("N", ""):
            logging.warning("Don't know how to retrieve logs from %s project",
                            rev.branch.project.get_repo_type_display())
        return logs

    if update:
        updaterepo(rev.branch.project)

    logs = getlogs(rev, startrev)

    # Remove last log because the startrev log shouldn't be shown
    if len(logs) > 1 and logs[-1].get('commitid') == startrev.commitid:
        logs.pop()

    return logs

def saverevisioninfo(rev):
    log = getcommitlogs(rev, rev, update=True)

    if log:
        log = log[0]
        rev.author  = log['author']
        rev.date    = log['date']
        rev.message = log['message']
    else:
        rev.date = datetime.now()

def validate_result(item):
    '''
    Validates that a result dictionary has all needed parameters

    It returns a tuple
        Environment, False  when no errors where found
        Errormessage, True  when there is an error
    '''
    mandatory_data = [
        'commitid',
        'project',
        'executable',
        'benchmark',
        'environment',
        'result_value',
    ]

    response = {}
    error    = True
    
    for key in mandatory_data:
        if not key in item:
            return 'Key "' + key + '" missing from request', error
        elif key in item and item[key] == "":
            return 'Value for key "' + key + '" empty in request', error
    
    # Check that the Environment exists
    try:
        e = Environment.objects.get(name=item['environment'])
        error = False
        return e, error
    except Environment.DoesNotExist:
        return "Environment %(environment)s not found" % item, error

def create_report_if_enough_data(rev, exe, e):
    # Trigger Report creation when there are enough results
    last_revs = Revision.objects.filter(branch__project=rev.branch.project).order_by('-date')[:2]
    if len(last_revs) > 1:
        current_results = rev.results.filter(executable=exe, environment=e)
        last_results = last_revs[1].results.filter(executable=exe,environment=e)
        # If there is are at least as many results as in the last revision,
        # create new report
        if len(current_results) >= len(last_results):
            logging.debug("create_report_if_enough_data: About to create new report")
            report, created = Report.objects.get_or_create(
                executable=exe, environment=e, revision=rev
            )
            report.full_clean()
            report.save()
            logging.debug("create_report_if_enough_data: Created new report.")

def save_result(data):
    res, error = validate_result(data)
    if error:
        return res, True
    else:
        assert(isinstance(res, Environment))
        e = res

    p, created = Project.objects.get_or_create(name=data["project"])
    b, created = Benchmark.objects.get_or_create(name=data["benchmark"])
    branch, created = Branch.objects.get_or_create(name=data["branch"],
                                                   project=p)
    
    try:
        rev = branch.revisions.get(commitid=data['commitid'])
    except Revision.DoesNotExist:
        rev = Revision(branch=branch, commitid=data['commitid'],
                        date=data.get("revision_date", datetime.now()))
        rev.full_clean()
        rev.save()

        if not rev.date:
            try:
                saverevisioninfo(rev)
            except StandardError, e:
                logging.warning("unable to save revision %s info: %s", rev, e,
                                exc_info=True)
    
    exe, created = Executable.objects.get_or_create(
        name=data['executable'],
        project=p
    )

    try:
        r = Result.objects.get(revision=rev,executable=exe,benchmark=b,environment=e)
    except Result.DoesNotExist:
        r = Result(revision=rev,executable=exe,benchmark=b,environment=e)

    r.value = data["result_value"]
    if 'result_date' in data:
        r.date = data["result_date"]
    elif rev.date:
        r.date = rev.date
    else:
        r.date = datetime.now()

    r.std_dev = data.get('std_dev')
    r.val_min = data.get('min')
    r.val_max = data.get('max')

    r.full_clean()
    r.save()

    return (rev, exe, e), False

def add_result(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed('POST')
    data = request.POST

    response, error = save_result(data)
    if error:
        return HttpResponseBadRequest(response)
    else:
        create_report_if_enough_data(response[0], response[1], response[2])
        logging.debug("add_result: completed")
        return HttpResponse("Result data saved succesfully", status=202)

def add_json_results(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed('POST')
    data = json.loads(request.POST['json'])
    logging.info("add_json_results request with %d entries." % len(data))

    unique_reports = set()
    i = 0
    for result in data:
        i += 1
        logging.debug("add_json_results: save item %d." % i)
        response, error = save_result(result)
        if error:
            logging.debug(
                "add_json_results: could not save item %d because %s" % (
                i, response))
            return HttpResponseBadRequest(response)
        else:
            unique_reports.add(response)

    logging.debug("add_json_results: about to create reports")
    for rep in unique_reports:
        create_report_if_enough_data(rep[0], rep[1], rep[2])

    logging.debug("add_json_results: completed")

    return HttpResponse("All result data saved successfully", status=202)

