# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging
from datetime import datetime
from django.core.exceptions import ValidationError

from django.conf import settings
from codespeed.models import (Environment, Executable, Revision,
                              Project, Branch, Benchmark,
                              Result, Report)

logger = logging.getLogger(__name__)


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
            # error in settings.DEF_BASELINE
            pass
    return baseline


def getdefaultexecutable():
    default = None
    if (hasattr(settings, 'DEF_EXECUTABLE') and
            settings.DEF_EXECUTABLE is not None):
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


def getcommitlogs(rev, startrev, update=False):
    logs = []

    if rev.branch.project.repo_type == 'S':
        from codespeed.subversion import getlogs, updaterepo
    elif rev.branch.project.repo_type == 'M':
        from codespeed.mercurial import getlogs, updaterepo
    elif rev.branch.project.repo_type == 'G':
        from codespeed.git import getlogs, updaterepo
    elif rev.branch.project.repo_type == 'H':
        from codespeed.github import getlogs, updaterepo
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

    error = True
    for key in mandatory_data:
        if key not in item:
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
