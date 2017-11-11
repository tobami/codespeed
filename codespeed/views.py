# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import json
import logging
import django

from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.http import HttpResponse, Http404, HttpResponseBadRequest,\
    HttpResponseNotFound
from django.db.models import F
from django.shortcuts import get_object_or_404, render_to_response
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt

from .auth import basic_auth_required
from .models import (Environment, Report, Project, Revision, Result,
                     Executable, Benchmark, Branch)
from .views_data import (get_default_environment, getbaselineexecutables,
                         getdefaultexecutable, getcomparisonexes,
                         get_benchmark_results)
from .results import save_result, create_report_if_enough_data
from . import commits
from .validators import validate_results_request
from .images import gen_image_from_results

logger = logging.getLogger(__name__)


def no_environment_error(request):
    admin_url = reverse('admin:codespeed_environment_changelist')
    return render_to_response('codespeed/nodata.html', {
        'message': ('You need to configure at least one Environment. '
                    'Please go to the '
                    '<a href="%s">admin interface</a>' % admin_url)
    })


def no_default_project_error(request):
    admin_url = reverse('admin:codespeed_project_changelist')
    return render_to_response('codespeed/nodata.html', {
        'message': ('You need to configure at least one one Project as '
                    'default (checked "Track changes" field).<br />'
                    'Please go to the '
                    '<a href="%s">admin interface</a>' % admin_url)
    })


def no_executables_error(request):
    return render_to_response('codespeed/nodata.html', {
        'message': 'There needs to be at least one executable'
    })


def no_data_found(request):
    return render_to_response('codespeed/nodata.html', {
        'message': 'No data found'
    })


@require_GET
def getcomparisondata(request):
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
                    compdata[exe['key']][env.id][bench.id] = results.get(
                        bench.id, None)

    compdata['error'] = "None"

    return HttpResponse(json.dumps(compdata))


@require_GET
def comparison(request):
    data = request.GET

    # Configuration of default parameters
    enviros = Environment.objects.all()
    if not enviros:
        return no_environment_error(request)
    checkedenviros = get_default_environment(enviros, data, multi=True)

    if not len(Project.objects.filter(track=True)):
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
    })


@require_GET
def gettimelinedata(request):
    data = request.GET

    timeline_list = {'error': 'None', 'timelines': []}

    executable_ids = data.get('exe', '').split(',')

    executables = []
    for i in executable_ids:
        if not i:
            continue
        try:
            executables.append(Executable.objects.get(id=int(i)))
        except Executable.DoesNotExist:
            pass

    if not executables:
        timeline_list['error'] = "No executables selected"
        return HttpResponse(json.dumps(timeline_list))
    environment = None
    try:
        environment = get_object_or_404(Environment, id=data.get('env'))
    except ValueError:
        Http404()

    benchmarks = []
    number_of_revs = int(data.get('revs', 10))

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
            'data_type':             bench.data_type,
            'units':                 bench.units,
            'lessisbetter':          lessisbetter,
            'branches':              {},
            'baseline':              "None",
        }
        append = False
        for branch in Branch.objects.filter(
                project__track=True, name=F('project__default_branch')):
            # For now, we'll only work with default branches
            for executable in executables:
                if executable.project != branch.project:
                    continue

                resultquery = Result.objects.filter(
                    benchmark=bench
                ).filter(
                    environment=environment
                ).filter(
                    executable=executable
                ).filter(
                    revision__branch=branch
                ).select_related(
                    "revision"
                ).order_by('-revision__date')[:number_of_revs]
                if not len(resultquery):
                    continue
                timeline['branches'].setdefault(branch.name, {})

                results = []
                for res in resultquery:
                    if bench.data_type == 'M':
                        val_min = ""
                        if res.val_min is not None:
                            val_min = res.val_min
                        val_max = ""
                        if res.val_max is not None:
                            val_max = res.val_max
                        q1 = ""
                        if res.q1 is not None:
                            q1 = res.q1
                        q3 = ""
                        if res.q3 is not None:
                            q3 = res.q3
                        results.append(
                            [
                                res.revision.date.strftime('%Y/%m/%d %H:%M:%S %z'),
                                res.value, val_max, q3, q1, val_min,
                                res.revision.get_short_commitid(), res.revision.tag, branch.name
                            ]
                        )
                    else:
                        std_dev = ""
                        if res.std_dev is not None:
                            std_dev = res.std_dev
                        results.append(
                            [
                                res.revision.date.strftime('%Y/%m/%d %H:%M:%S %z'),
                                res.value, std_dev,
                                res.revision.get_short_commitid(), res.revision.tag, branch.name
                            ]
                        )
                timeline['branches'][branch.name][executable.id] = results
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
                for branch in timeline['branches']:
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


@require_GET
def timeline(request):
    data = request.GET

    # Configuration of default parameters #
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
    if defaultproject.default_branch in branch_list:
        defaultbranch = defaultproject.default_branch
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
    if 'quarts' in data:
        defaultquarts = data['quarts']
    else:
        defaultquarts = "on"
    if 'extr' in data:
        defaultextr = data['extr']
    else:
        defaultextr = "on"

    # Information for template
    if defaultbenchmark in ['grid', 'show_none']:
        pagedesc = None
    else:
        pagedesc = "Results timeline for the '%s' benchmark (project %s)" % \
            (defaultbenchmark, defaultproject)
    executables = {}
    for proj in Project.objects.filter(track=True):
        executables[proj] = Executable.objects.filter(project=proj)
    use_median_bands = hasattr(settings, 'USE_MEDIAN_BANDS') and settings.USE_MEDIAN_BANDS
    return render_to_response('codespeed/timeline.html', {
        'pagedesc': pagedesc,
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
        'defaultequid': defaultequid,
        'defaultquarts': defaultquarts,
        'defaultextr': defaultextr,
        'use_median_bands': use_median_bands,
    })


@require_GET
def getchangestable(request):
    executable = get_object_or_404(Executable, pk=request.GET.get('exe'))
    environment = get_object_or_404(Environment, pk=request.GET.get('env'))
    try:
        trendconfig = int(request.GET.get('tre'))
    except TypeError:
        raise Http404()
    selectedrev = get_object_or_404(Revision, commitid=request.GET.get('rev'),
                                    branch__project=executable.project)
    prevrev = Revision.objects.filter(
        branch=selectedrev.branch,
        date__lt=selectedrev.date,
    ).order_by('-date').first()
    if prevrev:
        try:
            summary = Report.objects.get(
                revision=prevrev,
                executable=executable,
                environment=environment).item_description
        except Report.DoesNotExist:
            summary = ''
        prevrev = {
            'desc': str(prevrev),
            'rev': prevrev.commitid,
            'short_rev': prevrev.get_short_commitid(),
            'summary': summary,
        }
    else:
        prevrev = None

    nextrev = Revision.objects.filter(
        branch=selectedrev.branch,
        date__gt=selectedrev.date,
    ).order_by('date').first()
    if nextrev:
        try:
            summary = Report.objects.get(
                revision=nextrev,
                executable=executable,
                environment=environment).item_description
        except Report.DoesNotExist:
            summary = ''
        nextrev = {
            'desc': str(nextrev),
            'rev': nextrev.commitid,
            'short_rev': nextrev.get_short_commitid(),
            'summary': summary,
        }
    else:
        nextrev = None

    report, created = Report.objects.get_or_create(
        executable=executable, environment=environment, revision=selectedrev
    )
    tablelist = report.get_changes_table(trendconfig)

    if not len(tablelist):
        return HttpResponse('<table id="results" class="tablesorter" '
                            'style="height: 232px;"></table>'
                            '<p class="errormessage">No results for this '
                            'parameters</p>')

    return render_to_response('codespeed/changes_data.html', {
        'tablelist': tablelist,
        'trendconfig': trendconfig,
        'rev': selectedrev,
        'exe': executable,
        'env': environment,
        'prev': prevrev,
        'next': nextrev,
    })


@require_GET
def changes(request):
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

    if not len(Project.objects.filter(track=True)):
        return no_default_project_error(request)

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
        branch = Branch.objects.filter(name=proj.default_branch, project=proj)
        revisionlists[proj.name] = list(Revision.objects.filter(
            branch=branch
        ).order_by('-date')[:revlimit])
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
            if selectedrevision not in revisionlists[selectedrevision.project.name]:
                revisionlists[selectedrevision.project.name].append(selectedrevision)
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
            (str(rev), rev.commitid) for rev in revisions
        ]
    revisionlists = json.dumps(revisionlists)

    pagedesc = "Report of %s performance changes for commit %s on branch %s" % \
        (defaultexecutable, selectedrevision.commitid, selectedrevision.branch)
    return render_to_response('codespeed/changes.html', {
        'pagedesc': pagedesc,
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
    })


@require_GET
def reports(request):
    context = {}

    context['reports'] = \
        Report.objects.order_by('-revision__date')[:10]

    context['significant_reports'] = Report.objects.filter(
        colorcode__in=('red', 'green')
    ).order_by('-revision__date')[:10]

    return render_to_response('codespeed/reports.html', context)


@require_GET
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

        remotelogs = commits.get_logs(rev, startrev)
        if len(remotelogs):
            try:
                if remotelogs[0]['error']:
                    error = remotelogs[0]['message']
            except KeyError:
                pass  # no errors
            logs = remotelogs
        else:
            error = 'No logs found'
    except commits.exceptions.CommitLogError as e:
        logger.error('Unhandled exception displaying logs for %s: %s',
                     rev, e, exc_info=True)
        error = str(e)

    # Add commit browsing url to logs
    project = rev.branch.project
    for log in logs:
        log['commit_browse_url'] = project.commit_browsing_url.format(**log)

    return render_to_response(
        'codespeed/changes_logs.html',
        {
            'error': error, 'logs': logs,
            'show_email_address': settings.SHOW_AUTHOR_EMAIL_ADDRESS
        })


@csrf_exempt
@require_POST
@basic_auth_required('results')
def add_result(request):
    response, error = save_result(request.POST)
    if error:
        logger.error("Could not save result: " + response)
        return HttpResponseBadRequest(response)
    else:
        create_report_if_enough_data(response[0], response[1], response[2])
        logger.debug("add_result: completed")
        return HttpResponse("Result data saved successfully", status=202)


@csrf_exempt
@require_POST
@basic_auth_required('results')
def add_json_results(request):
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


def django_has_content_type():
    return (django.VERSION[0] > 1 or
            (django.VERSION[0] == 1 and django.VERSION[1] >= 6))


@require_GET
def makeimage(request):
    data = request.GET

    try:
        validate_results_request(data)
    except ValidationError as err:
        return HttpResponseBadRequest(str(err))

    try:
        result_data = get_benchmark_results(data)
    except ObjectDoesNotExist as err:
        return HttpResponseNotFound(str(err))

    image_data = gen_image_from_results(
                    result_data,
                    int(data['width']) if 'width' in data else None,
                    int(data['height']) if 'height' in data else None)

    if django_has_content_type():
        response = HttpResponse(content=image_data, content_type='image/png')
    else:
        response = HttpResponse(content=image_data, mimetype='image/png')

    response['Content-Length'] = len(image_data)
    response['Content-Disposition'] = 'attachment; filename=image.png'

    return response
