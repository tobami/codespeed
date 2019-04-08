# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import logging

logger = logging.getLogger(__name__)


def get_logs(rev, startrev, update=False):
    logs = []
    project = rev.branch.project
    if project.repo_type == project.SUBVERSION:
        from .subversion import getlogs, updaterepo
    elif project.repo_type == project.MERCURIAL:
        from .mercurial import getlogs, updaterepo
    elif project.repo_type == project.GIT:
        from .git import getlogs, updaterepo
    elif project.repo_type == project.GITHUB:
        from .github import getlogs, updaterepo
    else:
        if project.repo_type not in (project.NO_LOGS, ""):
            logger.warning("Don't know how to retrieve logs from %s project",
                           project.get_repo_type_display())
        return logs

    if update:
        updaterepo(rev.branch.project)

    logs = getlogs(rev, startrev)

    # Remove last log because the startrev log shouldn't be shown
    if len(logs) > 1 and logs[-1].get('commitid') == startrev.commitid:
        logs.pop()

    return logs
