import datetime
import logging
import os

from subprocess import Popen, PIPE

from django.conf import settings

from .exceptions import CommitLogError

logger = logging.getLogger(__name__)


def updaterepo(project, update=True):
    if os.path.exists(project.working_copy):
        if not update:
            return

        p = Popen(['git', 'pull'], stdout=PIPE, stderr=PIPE,
                  cwd=project.working_copy)

        stdout, stderr = p.communicate()
        if p.returncode != 0:
            raise CommitLogError("git pull returned %s: %s" % (p.returncode,
                                                               stderr))
        else:
            return [{'error': False}]
    else:
        cmd = ['git', 'clone', project.repo_path, project.repo_name]
        p = Popen(cmd, stdout=PIPE, stderr=PIPE,
                  cwd=settings.REPOSITORY_BASE_PATH)
        logger.debug('Cloning Git repo {0} for project {1}'.format(
            project.repo_path, project))
        stdout, stderr = p.communicate()

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

    if hasattr(settings, 'GIT_USE_FIRST_PARENT') and settings.GIT_USE_FIRST_PARENT:
        cmd.append("--first-parent")

    if endrev.commitid != startrev.commitid:
        cmd.append("%s...%s" % (startrev.commitid, endrev.commitid))
    else:
        cmd.append("-1")  # Only return one commit
        cmd.append(endrev.commitid)

    working_copy = endrev.branch.project.working_copy
    p = Popen(cmd, stdout=PIPE, stderr=PIPE, cwd=working_copy)

    stdout, stderr = p.communicate()

    if p.returncode != 0:
        raise CommitLogError("%s returned %s: %s" % (
                             " ".join(cmd), p.returncode, stderr))
    logs = []
    for log in filter(None, stdout.split(b'\x1e')):
        (short_commit_id, commit_id, date_t, author_name, author_email,
         subject, body) = (s.strip() for s in log.split(b'\x00', 7))

        tag = ""

        cmd = ["git", "tag", "--points-at", commit_id]
        proc = Popen(cmd, stdout=PIPE, stderr=PIPE, cwd=working_copy)

        try:
            stdout, stderr = proc.communicate()
        except ValueError:
            stdout = b''
            stderr = b''

        if proc.returncode == 0:
            tag = stdout.strip()

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
