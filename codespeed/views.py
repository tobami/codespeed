# -*- coding: utf-8 -*-
from datetime import datetime
from itertools import chain
import json
import logging

from django.http import (HttpResponse, Http404, HttpResponseNotAllowed,
                         HttpResponseBadRequest)
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from codespeed.models import (Environment, Report, Project, Revision, Result,
                              Executable, Benchmark, Branch)


logger = logging.getLogger(__name__)


def no_environment_error(request):
    admin_url = reverse('admin:codespeed_environment_changelist')
    return render_to_response('codespeed/nodata.html', {
        'message': ('You need to configure at least one Environment. '
                    'Please go to the '
                    '<a href="%s">admin interface</a>' % admin_url)
    }, context_instance=RequestContext(request))


def no_default_project_error(request):
    admin_url = reverse('admin:codespeed_project_changelist')
    return render_to_response('codespeed/nodata.html', {
        'message': ('You need to configure at least one one Project as '
                    'default (checked "Track changes" field).<br />'
                    'Please go to the '
                    '<a href="%s">admin interface</a>' % admin_url)
    }, context_instance=RequestContext(request))


def no_executables_error(request):
    return render_to_response('codespeed/nodata.html', {
        'message': 'There needs to be at least one executable'
    }, context_instance=RequestContext(request))


def no_data_found(request):
    return render_to_response('codespeed/nodata.html', {
        'message': 'No data found'
    }, context_instance=RequestContext(request))


def getbaselineexecutables():
    baseline = [{
        'key': "none",
        'name': "None",
        'executable': "none",
        'revision': "none",
    }]
    executables = Executable.objects.select_related('project')
    revs = Revision.objects.exclude(tag="").select_related('branch__project')
    maxlen = 22
    for rev in revs:
        # Add executables that correspond to each tagged revision.
        for exe in [e for e in executables if e.project == rev.branch.project]:
            exestring = str(exe)
            if len(exestring) > maxlen:
                exestring = str(exe)[0:maxlen] + "..."
            name = exestring + " " + rev.tag
            key = str(exe.id) + "+" + str(rev.id)
            baseline.append({
                'key': key,
                'executable': exe,
                'revision': rev,
                'name': name,
            })
    # move default to first place
    if hasattr(settings, 'DEF_BASELINE') and settings.DEF_BASELINE is not None:
        try:
            exename = settings.DEF_BASELINE['executable']
            commitid = settings.DEF_BASELINE['revision']
            for base in baseline:
                if base['key'] == "none":
                    continue
                if (base['executable'].name == exename and
                        base['revision'].commitid == commitid):
                    baseline.remove(base)
                    baseline.insert(1, base)
                    break
        except KeyError:
            # TODO: write to server logs
            #error in settings.DEF_BASELINE
            pass
    return baseline


def get_default_environment(enviros, data, multi=False):
    """Returns the default environment. Preference level is:
        * Present in URL parameters (permalinks)
        * Value in settings.py
        * First Environment ID

    """
    defaultenviros = []
    # Use permalink values
    if 'env' in data:
        for env_value in data['env'].split(","):
            for env in enviros:
                try:
                    env_id = int(env_value)
                except ValueError:
                    # Not an int
                    continue
                for env in enviros:
                    if env_id == env.id:
                        defaultenviros.append(env)
            if not multi:
                break
    # Use settings.py value
    if not defaultenviros and not multi:
        if (hasattr(settings, 'DEF_ENVIRONMENT') and
                settings.DEF_ENVIRONMENT is not None):
            for env in enviros:
                if settings.DEF_ENVIRONMENT == env.name:
                    defaultenviros.append(env)
                    break
    # Last fallback
    if not defaultenviros:
        defaultenviros = enviros
    if multi:
        return defaultenviros
    else:
        return defaultenviros[0]


def getdefaultexecutable():
    default = None
    if hasattr(settings, 'DEF_EXECUTABLE') and settings.DEF_EXECUTABLE is not None:
        try:
            default = Executable.objects.get(name=settings.DEF_EXECUTABLE)
        except Executable.DoesNotExist:
            pass
    if default is None:
        execquery = Executable.objects.filter(project__track=True)
        if len(execquery):
            default = execquery[0]

    return default


def getcomparisonexes():
    all_executables = {}
    exekeys = []
    baselines = getbaselineexecutables()
    for proj in Project.objects.all():
        executables = []
        executablekeys = []
        maxlen = 20
        # add all tagged revs for any project
        for exe in baselines:
            if exe['key'] is not "none" and exe['executable'].project == proj:
                executablekeys.append(exe['key'])
                executables.append(exe)

        # add latest revs of the project
        branches = Branch.objects.filter(project=proj)
        for branch in branches:
            try:
                rev = Revision.objects.filter(branch=branch).latest('date')
            except Revision.DoesNotExist:
                continue
            # Now only append when tag == "",
            # because we already added tagged revisions
            if rev.tag == "":
                for exe in Executable.objects.filter(project=proj):
                    exestring = str(exe)
                    if len(exestring) > maxlen:
                        exestring = str(exe)[0:maxlen] + "..."
                    name = exestring + " latest"
                    if branch.name != 'default':
                        name += " in branch '" + branch.name + "'"
                    key = str(exe.id) + "+L+" + branch.name
                    executablekeys.append(key)
                    executables.append({
                        'key': key,
                        'executable': exe,
                        'revision': rev,
                        'name': name,
                    })
        all_executables[proj] = executables
        exekeys += executablekeys
    return all_executables, exekeys


def getcomparisondata(request):
    if request.method != 'GET':
        return HttpResponseNotAllowed('GET')
    data = request.GET

    executables, exekeys = getcomparisonexes()
    benchmarks = Benchmark.objects.all()
    environments = Environment.objects.all()

    compdata = {}
    compdata['error'] = "Unknown error"
    for proj in executables:
        for exe in executables[proj]:
            compdata[exe['key']] = {}
            for env in environments:
                compdata[exe['key']][env.id] = {}

                # Load all results for this env/executable/revision in a dict
                # for fast lookup
                results = dict(Result.objects.filter(
                    environment=env,
                    executable=exe['executable'],
                    revision=exe['revision'],
                ).values_list('benchmark', 'value'))

                for bench in benchmarks:
                    compdata[exe['key']][env.id][bench.id] = results.get(bench.id, None)

    compdata['error'] = "None"

    return HttpResponse(json.dumps(compdata))


def comparison(request):
    if request.method != 'GET':
        return HttpResponseNotAllowed('GET')
    data = request.GET

    # Configuration of default parameters
    enviros = Environment.objects.all()
    if not enviros:
        return no_environment_error(request)
    checkedenviros = get_default_environment(enviros, data, multi=True)

    if not len(Project.objects.all()):
        return no_default_project_error(request)

    # Check whether there exist appropiate executables
    if not getdefaultexecutable():
        return no_executables_error(request)

    executables, exekeys = getcomparisonexes()
    checkedexecutables = []
    if 'exe' in data:
        for i in data['exe'].split(","):
            if not i:
                continue
            if i in exekeys:
                checkedexecutables.append(i)
    elif hasattr(settings, 'COMP_EXECUTABLES') and settings.COMP_EXECUTABLES:
        for exe, rev in settings.COMP_EXECUTABLES:
            try:
                exe = Executable.objects.get(name=exe)
                key = str(exe.id) + "+"
                if rev == "L":
                    key += rev
                else:
                    rev = Revision.objects.get(commitid=rev)
                    key += str(rev.id)
                key += "+default"
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
        lessisbetter = (benchmarks[unit][0].lessisbetter and
                        ' (less is better)' or ' (more is better)')
        bench_units[unit] = [
            [b.id for b in benchmarks[unit]], lessisbetter, units
        ]
    checkedbenchmarks = []
    if 'ben' in data:
        checkedbenchmarks = []
        for i in data['ben'].split(","):
            if not i:
                continue
            try:
                checkedbenchmarks.append(Benchmark.objects.get(id=int(i)))
            except Benchmark.DoesNotExist:
                pass
    if not checkedbenchmarks:
        # Only include benchmarks marked as cross-project
        checkedbenchmarks = Benchmark.objects.filter(
            benchmark_type="C", default_on_comparison=True)

    charts = ['normal bars', 'stacked bars', 'relative bars']
    # Don't show relative charts as an option if there is only one executable
    # Relative charts need normalization
    if len(executables) == 1:
        charts.remove('relative bars')

    selectedchart = charts[0]
    if 'chart' in data and data['chart'] in charts:
        selectedchart = data['chart']
    elif hasattr(settings, 'CHART_TYPE') and settings.CHART_TYPE in charts:
        selectedchart = settings.CHART_TYPE

    selectedbaseline = "none"
    if 'bas' in data and data['bas'] in exekeys:
        selectedbaseline = data['bas']
    elif 'bas' in data:
        # bas is present but is none
        pass
    elif (len(exekeys) > 1 and hasattr(settings, 'NORMALIZATION') and
            settings.NORMALIZATION):
        try:
            # TODO: Avoid calling twice getbaselineexecutables
            selectedbaseline = getbaselineexecutables()[1]['key']
            # Uncheck exe used for normalization
            try:
                checkedexecutables.remove(selectedbaseline)
            except ValueError:
                pass  # The selected baseline was not checked
        except:
            pass  # Keep "none" as default baseline

    selecteddirection = False
    if ('hor' in data and data['hor'] == "true" or
        hasattr(settings, 'CHART_ORIENTATION') and
            settings.CHART_ORIENTATION == 'horizontal'):
        selecteddirection = True

    return render_to_response('codespeed/comparison.html', {
        'checkedexecutables': checkedexecutables,
        'checkedbenchmarks': checkedbenchmarks,
        'checkedenviros': checkedenviros,
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
        return HttpResponse(json.dumps(timeline_list))
    environment = None
    try:
        environment = get_object_or_404(Environment, id=data.get('env'))
    except ValueError:
        Http404()

    benchmarks = []
    number_of_revs = data.get('revs', 10)

    if data['ben'] == 'grid':
        benchmarks = Benchmark.objects.all().order_by('name')
        number_of_revs = 15
    elif data['ben'] == 'show_none':
        benchmarks = []
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
        # Temporary
        trunks = []
        if Branch.objects.filter(name=settings.DEF_BRANCH):
            trunks.append(settings.DEF_BRANCH)
        # For now, we'll only work with trunk branches
        append = False
        for branch in trunks:
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
                    if res.std_dev is not None:
                        std_dev = res.std_dev
                    results.append(
                        [
                            res.revision.date.isoformat(), res.value, std_dev,
                            res.revision.get_short_commitid(), branch
                        ]
                    )
                timeline['branches'][branch][executable] = results
                append = True
            if baselinerev is not None and append:
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
                    # determine start and end revision (x axis)
                    # from longest data series
                    results = []
                    for exe in timeline['branches'][branch]:
                        if len(timeline['branches'][branch][exe]) > len(results):
                            results = timeline['branches'][branch][exe]
                    end = results[0][0]
                    start = results[len(results) - 1][0]
                    timeline['baseline'] = [
                        [str(start), baselinevalue],
                        [str(end), baselinevalue]
                    ]
        if append:
            timeline_list['timelines'].append(timeline)

    if not len(timeline_list['timelines']) and data['ben'] != 'show_none':
        response = 'No data found for the selected options'
        timeline_list['error'] = response
    return HttpResponse(json.dumps(timeline_list))


def timeline(request):
    if request.method != 'GET':
        return HttpResponseNotAllowed('GET')
    data = request.GET

    ## Configuration of default parameters ##
    # Default Environment
    enviros = Environment.objects.all()
    if not enviros:
        return no_environment_error(request)
    defaultenviro = get_default_environment(enviros, data)

    # Default Project
    defaultproject = Project.objects.filter(track=True)
    if not len(defaultproject):
        return no_default_project_error(request)
    else:
        defaultproject = defaultproject[0]

    checkedexecutables = []
    if 'exe' in data:
        for i in data['exe'].split(","):
            if not i:
                continue
            try:
                checkedexecutables.append(Executable.objects.get(id=int(i)))
            except Executable.DoesNotExist:
                pass

    if not checkedexecutables:
        checkedexecutables = Executable.objects.filter(project__track=True)

    if not len(checkedexecutables):
        return no_executables_error(request)

    # TODO: we need branches for all tracked projects
    branch_list = [
        branch.name for branch in Branch.objects.filter(project=defaultproject)]
    branch_list.sort()

    defaultbranch = ""
    if "default" in branch_list:
        defaultbranch = settings.DEF_BRANCH
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
    defaultlast = settings.DEF_TIMELINE_LIMIT
    if 'revs' in data:
        if int(data['revs']) not in lastrevisions:
            lastrevisions.append(data['revs'])
        defaultlast = data['revs']

    benchmarks = Benchmark.objects.all()
    grid_limit = 30
    defaultbenchmark = "grid"
    if not len(benchmarks):
        return no_data_found(request)
    elif len(benchmarks) == 1:
        defaultbenchmark = benchmarks[0]
    elif hasattr(settings, 'DEF_BENCHMARK') and settings.DEF_BENCHMARK is not None:
        if settings.DEF_BENCHMARK in ['grid', 'show_none']:
            defaultbenchmark = settings.DEF_BENCHMARK
        else:
            try:
                defaultbenchmark = Benchmark.objects.get(
                    name=settings.DEF_BENCHMARK)
            except Benchmark.DoesNotExist:
                pass
    elif len(benchmarks) >= grid_limit:
        defaultbenchmark = 'show_none'

    if 'ben' in data and data['ben'] != defaultbenchmark:
        if data['ben'] == "show_none":
            defaultbenchmark = data['ben']
        else:
            defaultbenchmark = get_object_or_404(Benchmark, name=data['ben'])

    if 'equid' in data:
        defaultequid = data['equid']
    else:
        defaultequid = "off"

    # Information for template
    executables = {}
    for proj in Project.objects.filter(track=True):
        executables[proj] = Executable.objects.filter(project=proj)
    return render_to_response('codespeed/timeline.html', {
        'checkedexecutables': checkedexecutables,
        'defaultbaseline': defaultbaseline,
        'baseline': baseline,
        'defaultbenchmark': defaultbenchmark,
        'defaultenvironment': defaultenviro,
        'lastrevisions': lastrevisions,
        'defaultlast': defaultlast,
        'executables': executables,
        'benchmarks': benchmarks,
        'environments': enviros,
        'branch_list': branch_list,
        'defaultbranch': defaultbranch,
        'defaultequid': defaultequid
    }, context_instance=RequestContext(request))


def getchangestable(request):
    executable = get_object_or_404(Executable, pk=request.GET.get('exe'))
    environment = get_object_or_404(Environment, pk=request.GET.get('env'))
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
        return HttpResponse('<table id="results" class="tablesorter" '
                            'style="height: 232px;"></table>'
                            '<p class="errormessage">No results for this '
                            'parameters</p>')

    return render_to_response('codespeed/changes_table.html', {
        'tablelist': tablelist,
        'trendconfig': trendconfig,
        'rev': selectedrev,
        'exe': executable,
        'env': environment,
    }, context_instance=RequestContext(request))


def changes(request):
    if request.method != 'GET':
        return HttpResponseNotAllowed('GET')
    data = request.GET

    # Configuration of default parameters
    defaultchangethres = 3.0
    defaulttrendthres = 4.0
    if (hasattr(settings, 'CHANGE_THRESHOLD') and
            settings.CHANGE_THRESHOLD is not None):
        defaultchangethres = settings.CHANGE_THRESHOLD
    if (hasattr(settings, 'TREND_THRESHOLD') and
            settings.TREND_THRESHOLD is not None):
        defaulttrendthres = settings.TREND_THRESHOLD

    defaulttrend = 10
    trends = [5, 10, 20, 50, 100]
    if 'tre' in data and int(data['tre']) in trends:
        defaulttrend = int(data['tre'])

    enviros = Environment.objects.all()
    if not enviros:
        return no_environment_error(request)
    defaultenv = get_default_environment(enviros, data)

    defaultexecutable = getdefaultexecutable()
    if not defaultexecutable:
        return no_executables_error(request)

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
    revlimit = 20
    executables = {}
    revisionlists = {}
    projectlist = []
    for proj in Project.objects.filter(track=True):
        executables[proj] = Executable.objects.filter(project=proj)
        projectlist.append(proj)
        branch = Branch.objects.filter(name=settings.DEF_BRANCH, project=proj)
        revisionlists[proj.name] = Revision.objects.filter(
            branch=branch
        ).order_by('-date')[:revlimit]
    # Get lastest revisions for this project and it's "default" branch
    lastrevisions = revisionlists.get(defaultexecutable.project.name)
    if not len(lastrevisions):
        return no_data_found(request)
    selectedrevision = lastrevisions[0]

    if "rev" in data:
        commitid = data['rev']
        try:
            selectedrevision = Revision.objects.get(
                commitid__startswith=commitid, branch=branch
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
    for proj in executables:
        for e in executables[proj]:
            projectmatrix[e.id] = e.project.name
    projectmatrix = json.dumps(projectmatrix)

    for project, revisions in revisionlists.items():
        revisionlists[project] = [
            (unicode(rev), rev.commitid) for rev in revisions
        ]
    revisionlists = json.dumps(revisionlists)

    return render_to_response('codespeed/changes.html', {
        'defaultenvironment': defaultenv,
        'defaultexecutable': defaultexecutable,
        'selectedrevision': selectedrevision,
        'defaulttrend': defaulttrend,
        'defaultchangethres': defaultchangethres,
        'defaulttrendthres': defaulttrendthres,
        'environments': enviros,
        'executables': executables,
        'projectmatrix': projectmatrix,
        'revisionlists': revisionlists,
        'trends': trends,
    }, context_instance=RequestContext(request))


def reports(request):
    if request.method != 'GET':
        return HttpResponseNotAllowed('GET')

    return render_to_response('codespeed/reports.html', {
        'reports': Report.objects.filter(
            revision__branch__name=settings.DEF_BRANCH
        ).order_by('-revision__date')[:10],
    }, context_instance=RequestContext(request))


def displaylogs(request):
    rev = get_object_or_404(Revision, pk=request.GET.get('revisionid'))
    logs = []
    logs.append(
        {
            'date': str(rev.date), 'author': rev.author,
            'author_email': '', 'message': rev.message,
            'short_commit_id': rev.get_short_commitid(),
            'commitid': rev.commitid
        }
    )
    error = False
    try:
        startrev = Revision.objects.filter(
            branch=rev.branch
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
                pass  # no errors
            logs = remotelogs
        else:
            error = 'no logs found'
    except (StandardError, RuntimeError) as e:
        logger.error(
            "Unhandled exception displaying logs for %s: %s",
            rev, e, exc_info=True)
        error = repr(e)

    # add commit browsing url to logs
    project = rev.branch.project
    for log in logs:
        log['commit_browse_url'] = project.commit_browsing_url.format(**log)

    return render_to_response(
        'codespeed/changes_logs.html',
        {'error': error, 'logs': logs,
         'show_email_address': settings.SHOW_AUTHOR_EMAIL_ADDRESS},
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
            logger.warning("Don't know how to retrieve logs from %s project",
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
        rev.author = log['author']
        rev.date = log['date']
        rev.message = log['message']


def validate_result(item):
    """
    Validates that a result dictionary has all needed parameters

    It returns a tuple
        Environment, False  when no errors where found
        Errormessage, True  when there is an error
    """
    mandatory_data = [
        'commitid',
        'branch',
        'project',
        'executable',
        'benchmark',
        'environment',
        'result_value',
    ]

    response = {}
    error = True
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
    """Triggers Report creation when there are enough results"""
    last_revs = Revision.objects.filter(
        branch=rev.branch
    ).order_by('-date')[:2]
    if len(last_revs) > 1:
        current_results = rev.results.filter(executable=exe, environment=e)
        last_results = last_revs[1].results.filter(
            executable=exe, environment=e)
        # If there is are at least as many results as in the last revision,
        # create new report
        if len(current_results) >= len(last_results):
            logger.debug("create_report_if_enough_data: About to create new report")
            report, created = Report.objects.get_or_create(
                executable=exe, environment=e, revision=rev
            )
            report.full_clean()
            report.save()
            logger.debug("create_report_if_enough_data: Created new report.")


def save_result(data):
    res, error = validate_result(data)
    if error:
        return res, True
    else:
        assert(isinstance(res, Environment))
        env = res

    p, created = Project.objects.get_or_create(name=data["project"])
    branch, created = Branch.objects.get_or_create(name=data["branch"],
                                                   project=p)
    b, created = Benchmark.objects.get_or_create(name=data["benchmark"])

    if created:
        if "description" in data:
            b.description = data["description"]
        if "units" in data:
            b.units = data["units"]
        if "units_title" in data:
            b.units_title = data["units_title"]
        if "lessisbetter" in data:
            b.lessisbetter = data["lessisbetter"]
        b.full_clean()
        b.save()

    try:
        rev = branch.revisions.get(commitid=data['commitid'])
    except Revision.DoesNotExist:
        rev_date = data.get("revision_date")
        # "None" (as string) can happen when we urlencode the POST data
        if not rev_date or rev_date in ["", "None"]:
            rev_date = datetime.today()
        rev = Revision(branch=branch, project=p, commitid=data['commitid'],
                       date=rev_date)
        try:
            rev.full_clean()
        except ValidationError as e:
            return str(e), True
        if p.repo_type not in ("N", ""):
            try:
                saverevisioninfo(rev)
            except RuntimeError as e:
                logger.warning("unable to save revision %s info: %s", rev, e,
                               exc_info=True)
        rev.save()

    exe, created = Executable.objects.get_or_create(
        name=data['executable'],
        project=p
    )

    try:
        r = Result.objects.get(
            revision=rev, executable=exe, benchmark=b, environment=env)
    except Result.DoesNotExist:
        r = Result(revision=rev, executable=exe, benchmark=b, environment=env)

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

    return (rev, exe, env), False


@csrf_exempt
def add_result(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed('POST')
    data = request.POST

    response, error = save_result(data)
    if error:
        logger.error("Could not save result: " + response)
        return HttpResponseBadRequest(response)
    else:
        create_report_if_enough_data(response[0], response[1], response[2])
        logger.debug("add_result: completed")
        return HttpResponse("Result data saved successfully", status=202)


@csrf_exempt
def add_json_results(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed('POST')
    if not request.POST.get('json'):
        return HttpResponseBadRequest("No key 'json' in POST payload")
    data = json.loads(request.POST['json'])
    logger.info("add_json_results request with %d entries." % len(data))

    unique_reports = set()
    i = 0
    for result in data:
        i += 1
        logger.debug("add_json_results: save item %d." % i)
        response, error = save_result(result)
        if error:
            logger.debug(
                "add_json_results: could not save item %d because %s" % (
                i, response))
            return HttpResponseBadRequest(response)
        else:
            unique_reports.add(response)

    logger.debug("add_json_results: about to create reports")
    for rep in unique_reports:
        create_report_if_enough_data(rep[0], rep[1], rep[2])

    logger.debug("add_json_results: completed")

    return HttpResponse("All result data saved successfully", status=202)
