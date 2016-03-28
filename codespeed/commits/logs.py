# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import logging

logger = logging.getLogger(__name__)


def get_logs(rev, startrev, update=False):
    logs = []

    if rev.branch.project.repo_type == 'S':
        from .subversion import getlogs, updaterepo
    elif rev.branch.project.repo_type == 'M':
        from .mercurial import getlogs, updaterepo
    elif rev.branch.project.repo_type == 'G':
        from .git import getlogs, updaterepo
    elif rev.branch.project.repo_type == 'H':
        from .github import getlogs, updaterepo
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
