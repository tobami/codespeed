import datetime
import logging
import os

from subprocess import Popen, PIPE
from django.conf import settings
from .exceptions import CommitLogError

logger = logging.getLogger(__name__)


def execute_command(cmd, cwd):
    p = Popen(cmd, stdout=PIPE, stderr=PIPE, cwd=cwd)
    stdout, stderr = p.communicate()
    stdout = stdout.decode('utf8') if stdout is not None else stdout
    stderr = stderr.decode('utf8') if stderr is not None else stderr
    return (p, stdout, stderr)


def updaterepo(project, update=True):
    if os.path.exists(project.working_copy):
        if not update:
            return

        p, _, stderr = execute_command(['git', 'pull'], cwd=project.working_copy)

        if p.returncode != 0:
            raise CommitLogError("git pull returned %s: %s" % (p.returncode,
                                                               stderr))
        else:
            return [{'error': False}]
    else:
        cmd = ['git', 'clone', project.repo_path, project.repo_name]
        p, stdout, stderr = execute_command(cmd, settings.REPOSITORY_BASE_PATH)
        logger.debug('Cloning Git repo {0} for project {1}'.format(
            project.repo_path, project))

        if p.returncode != 0:
            raise CommitLogError("%s returned %s: %s" % (
                " ".join(cmd), p.returncode, stderr))
        else:
            return [{'error': False}]


def getlogs(endrev, startrev):
    updaterepo(endrev.branch.project, update=False)

    # NULL separated values delimited by 0x1e record separators
    # See PRETTY FORMATS in git-log(1):
    if hasattr(settings, 'GIT_USE_COMMIT_DATE') and settings.GIT_USE_COMMIT_DATE:
        logfmt = '--format=format:%h%x00%H%x00%ct%x00%an%x00%ae%x00%s%x00%b%x1e'
    else:
        logfmt = '--format=format:%h%x00%H%x00%at%x00%an%x00%ae%x00%s%x00%b%x1e'

    cmd = ["git", "log", logfmt]

    if endrev.commitid != startrev.commitid:
        cmd.append("%s...%s" % (startrev.commitid, endrev.commitid))
    else:
        cmd.append("-1")  # Only return one commit
        cmd.append(endrev.commitid)

    working_copy = endrev.branch.project.working_copy
    p, stdout, stderr = execute_command(cmd, working_copy)

    if p.returncode != 0:
        raise CommitLogError("%s returned %s: %s" % (
                             " ".join(cmd), p.returncode, stderr))
    logs = []
    for log in filter(None, stdout.split('\x1e')):
        (short_commit_id, commit_id, date_t, author_name, author_email,
            subject, body) = map(lambda s: s.strip(), log.split('\x00', 7))

        cmd = ["git", "tag", "--points-at", commit_id]

        try:
            p, stdout, stderr = execute_command(cmd, working_copy)
        except Exception:
            logger.debug('Failed to get tag', exc_info=True)

        tag = stdout.strip() if p.returncode == 0 else ""
        date = datetime.datetime.fromtimestamp(
            int(date_t)).strftime("%Y-%m-%d %H:%M:%S")

        logs.append({
            'date': date,
            'message': subject,
            'commitid': commit_id,
            'author': author_name,
            'author_email': author_email,
            'body': body,
            'short_commit_id': short_commit_id,
            'tag': tag
        })

    return logs
