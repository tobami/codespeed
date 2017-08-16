# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging
from datetime import datetime

from django.core.exceptions import ValidationError

from .models import (Environment, Project, Branch, Benchmark, Executable,
                     Revision, Result, Report)
from . import commits

logger = logging.getLogger(__name__)


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
                commit_logs = commits.get_logs(rev, rev, update=True)
            except commits.exceptions.CommitLogError as e:
                logger.warning("unable to save revision %s info: %s", rev, e,
                               exc_info=True)
            else:
                if commit_logs:
                    log = commit_logs[0]
                    rev.author = log['author']
                    rev.date = log['date']
                    rev.message = log['message']
                    rev.tag = log['tag']

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
    r.q1 = data.get('q1')
    r.q3 = data.get('q3')

    r.full_clean()
    r.save()

    return (rev, exe, env), False


def create_report_if_enough_data(rev, exe, e):
    """Triggers Report creation when there are enough results"""
    if exe.project.track is not True:
        return False

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
            logger.debug("Created new report for branch %s and revision %s",
                         rev.branch, rev.commitid)
