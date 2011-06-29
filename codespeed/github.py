# encoding: utf-8
"""
Specialized Git backend which uses Github.com for all of the heavy work

Among other things, this means that the codespeed server doesn't need to have
git installed, the ability to write files, etc.
"""
import logging
import urllib
import re
import isodate

from django.core.cache import cache

# Import from here on the off-chance someone is using a really old Python:
from django.utils import simplejson as json


GITHUB_URL_RE = re.compile(r'^(?P<proto>\w+)://github.com/(?P<username>[^/]+)/(?P<project>[^/]+)[.]git$')

# We currently use a simple linear search of on a single parent to retrieve
# the history. This is often good enough, but might miss the actual starting
# point. Thus, we need to terminate the search after a resonable number of
# revisions.
GITHUB_REVISION_LIMIT = 10

def updaterepo(project, update=True):
    return


def retrieve_revision(commit_id, username, project, revision = None):
    commit_url = 'http://github.com/api/v2/json/commits/show/%s/%s/%s' % (
        username, project, commit_id)

    commit_json = cache.get(commit_url)

    if commit_json is None:
        try:
            commit_json = json.load(urllib.urlopen(commit_url))
        except IOError, e:
            logging.exception("Unable to load %s: %s",
                commit_url, e, exc_info=True)
            raise e

        if 'error' in commit_json:
            # We'll still cache these for a brief period of time to avoid making too many requests:
            cache.set(commit_url, commit_json, 300)
        else:
            # We'll cache successes for a very long period of time since
            # SCM diffs shouldn't change:
            cache.set(commit_url, commit_json, 86400 * 30)

    if 'error' in commit_json:
        raise RuntimeError("Unable to load %s: %s" % (commit_url, commit_json['error']))

    commit = commit_json['commit']

    date = isodate.parse_datetime(commit['committed_date'])

    if revision:
        # Overwrite any existing data we might have for this revision since
        # we never want our records to be out of sync with the actual VCS:

        # We need to convert the timezone-aware date to a naive (i.e.
        # timezone-less) date in UTC to avoid killing MySQL:
        revision.date = date.astimezone(isodate.tzinfo.Utc()).replace(tzinfo=None)
        revision.author = commit['author']['name']
        revision.message = commit['message']
        revision.full_clean()
        revision.save()

    return {'date':         date,
            'message':      commit['message'],
            'body':         "", # TODO: pretty-print diffs
            'author':       commit['author']['name'],
            'author_email': commit['author']['email'],
            'commitid':     commit['id'],
            'short_commit_id': commit['id'][0:7],
            'links': {'Github': 'http://github.com%s' % commit['url']},
            'parents':      commit['parents']}

def getlogs(endrev, startrev):
    if endrev != startrev:
        revisions = endrev.branch.revisions.filter(
                        date__lte=endrev.date, date__gte=startrev.date)
    else:
        revisions = [i for i in (startrev, endrev) if i.commitid]

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
    #TODO: get all revisions between endrev and startrev,
    # not only those present in the Codespeed DB

    for revision in revisions:
        last_rev_data = retrieve_revision(revision.commitid, username, project, revision)
        logs.append(last_rev_data)
        revision_count += 1
        ancestor_found = (startrev.commitid in [rev['id'] for rev in last_rev_data['parents']])
    
    # Simple approach to find the startrev, stop after found or after
    # #GITHUB_REVISION_LIMIT revisions are fetched
    while (revision_count < GITHUB_REVISION_LIMIT 
            and not ancestor_found
            and len(last_rev_data['parents']) > 0):
        last_rev_data = retrieve_revision(last_rev_data['parents'][0]['id'], username, project)
        logs.append(last_rev_data)
        revision_count += 1
        ancestor_found = (startrev.commitid in [rev['id'] for rev in last_rev_data['parents']])
    
    return sorted(logs, key=lambda i: i['date'], reverse=True)
