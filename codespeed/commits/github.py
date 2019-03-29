# encoding: utf-8
"""
Specialized Git backend which uses Github.com for all of the heavy work

Among other things, this means that the codespeed server doesn't need to have
git installed, the ability to write files, etc.
"""
from __future__ import absolute_import

import logging
try:
    # Python 3
    from urllib.request import urlopen
except ImportError:
    # Python 2
    from urllib import urlopen
import re
import json

import isodate
from django.core.cache import cache

from .exceptions import CommitLogError

logger = logging.getLogger(__name__)

GITHUB_URL_RE = re.compile(
    r'^(?P<proto>\w+)://github.com/(?P<username>[^/]+)/(?P<project>[^/]+)([.]git)?$')

# We currently use a simple linear search of on a single parent to retrieve
# the history. This is often good enough, but might miss the actual starting
# point. Thus, we need to terminate the search after a resonable number of
# revisions.
GITHUB_REVISION_LIMIT = 10


def updaterepo(project, update=True):
    return


def fetch_json(url):
    json_obj = cache.get(url)

    if json_obj is None:
        try:
            json_obj = json.load(urlopen(url))
        except IOError as e:
            logger.exception("Unable to load %s: %s",
                             url, e, exc_info=True)
            raise e

        if "message" in json_obj and \
           json_obj["message"] in ("Not Found", "Server Error",):
            # We'll still cache these for a brief period of time to avoid
            # making too many requests:
            cache.set(url, json_obj, 300)
        else:
            # We'll cache successes for a very long period of time since
            # SCM diffs shouldn't change:
            cache.set(url, json_obj, 86400 * 30)

    if "message" in json_obj and \
       json_obj["message"] in ("Not Found", "Server Error",):
        raise CommitLogError(
            "Unable to load %s: %s" % (url, json_obj["message"]))

    return json_obj


def retrieve_tag(commit_id, username, project):
    tags_url = 'https://api.github.com/repos/%s/%s/git/refs/tags' % (
        username, project)

    tags_json = fetch_json(tags_url)
    for tag in tags_json:
        if tag['object']['sha'] == commit_id:
            return tag['ref'].split("refs/tags/")[-1]

    return ""


def retrieve_revision(commit_id, username, project, revision=None):
    commit_url = 'https://api.github.com/repos/%s/%s/git/commits/%s' % (
        username, project, commit_id)

    commit_json = fetch_json(commit_url)

    date = isodate.parse_datetime(commit_json['committer']['date'])
    tag = retrieve_tag(commit_id, username, project)

    if revision:
        # Overwrite any existing data we might have for this revision since
        # we never want our records to be out of sync with the actual VCS:

        # We need to convert the timezone-aware date to a naive (i.e.
        # timezone-less) date in UTC to avoid killing MySQL:
        revision.date = date.astimezone(
            isodate.tzinfo.Utc()).replace(tzinfo=None)
        revision.author = commit_json['author']['name']
        revision.message = commit_json['message']
        revision.full_clean()
        revision.save()

    return {'date':         date,
            'message':      commit_json['message'],
            'body':         "",   # TODO: pretty-print diffs
            'author':       commit_json['author']['name'],
            'author_email': commit_json['author']['email'],
            'commitid':     commit_json['sha'],
            'short_commit_id': commit_json['sha'][0:7],
            'parents':      commit_json['parents'],
            'tag':          tag}


def getlogs(endrev, startrev):
    if endrev != startrev:
        revisions = endrev.branch.revisions.filter(
            date__lte=endrev.date, date__gte=startrev.date)
    else:
        revisions = [i for i in (startrev, endrev) if i.commitid]

    if endrev.branch.project.repo_path[-1] == '/':
        endrev.branch.project.repo_path = endrev.branch.project.repo_path[:-1]

    m = GITHUB_URL_RE.match(endrev.branch.project.repo_path)

    if not m:
        raise ValueError(
            "Unable to parse Github URL %s" % endrev.branch.project.repo_path)

    username = m.group("username")
    project = m.group("project")

    logs = []
    last_rev_data = None
    revision_count = 0
    ancestor_found = False
    # TODO: get all revisions between endrev and startrev,
    # not only those present in the Codespeed DB

    for revision in revisions:
        last_rev_data = retrieve_revision(
            revision.commitid, username, project, revision)
        logs.append(last_rev_data)
        revision_count += 1
        ancestor_found = (
            startrev.commitid in [
                rev['sha'] for rev in last_rev_data['parents']])

    # Simple approach to find the startrev, stop after found or after
    # #GITHUB_REVISION_LIMIT revisions are fetched
    while (revision_count < GITHUB_REVISION_LIMIT
            and not ancestor_found
            and len(last_rev_data['parents']) > 0):
        last_rev_data = retrieve_revision(
            last_rev_data['parents'][0]['sha'], username, project)
        logs.append(last_rev_data)
        revision_count += 1
        ancestor_found = (
            startrev.commitid in [
                rev['sha'] for rev in last_rev_data['parents']])

    return sorted(logs, key=lambda i: i['date'], reverse=True)
