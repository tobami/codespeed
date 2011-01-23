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


def updaterepo(project, update=True):
    return


def getlogs(endrev, startrev):
    if endrev != startrev:
        raise NotImplementedError("%s:%s" % (startrev, endrev))
    else:
        commit_ids = (endrev.commitid, )
    
    m = GITHUB_URL_RE.match(endrev.project.repo_path)
    
    if not m:
        raise ValueError("Unable to parse Github URL %s" % endrev.project.repo_path)
        
    username = m.group("username")
    project = m.group("project")
    
    logs = []
    
    for commit_id in commit_ids:
        commit_url = 'http://github.com/api/v2/json/commits/show/%s/%s/%s' % (username, project, commit_id)

        commit_json = cache.get(commit_url)

        if commit_json is None:
            try:
                commit_json = json.load(urllib.urlopen(commit_url))
            except IOError, e:
                logging.exception("Unable to load %s: %s", commit_url, e, exc_info=e)
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

        logs.append({'date': date, 'message': commit['message'], 
                        'body': "", # TODO: pretty-print diffs
                        'author': commit['author']['name'],
                        'author_email': commit['author']['email'],
                        'commitid': commit['id'], 
                        'short_commit_id': commit['id'][0:7],
                        'links': {'Github': 'http://github.com%s' % commit['url']}})

    return logs
