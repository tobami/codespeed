from subprocess import Popen, PIPE
import datetime
import os
import logging

from django.conf import settings


def updaterepo(project, update=True):
    repo_name = os.path.splitext(project.repo_path.split(os.sep)[-1])[0]
    working_copy = os.path.join(settings.REPOSITORY_BASE_PATH, repo_name)

    if os.path.exists(working_copy):
        if not update:
            return

        p = Popen(['git', 'pull'], stdout=PIPE, stderr=PIPE,
                    cwd=working_copy)

        stdout, stderr = p.communicate()
        if p.returncode != 0:
            raise RuntimeError("git pull returned %s: %s" % (p.returncode,
                                                                stderr))
        else:
            return [{'error': False}]
    else:
        cmd = ['git', 'clone', project.repo_path, repo_name]
        p = Popen(cmd, stdout=PIPE, stderr=PIPE,
                    cwd=settings.REPOSITORY_BASE_PATH)
        logging.debug('Cloning Git repo {0}for project {1}'.format(
            project.repo_path, project))
        stdout, stderr = p.communicate()

        if p.returncode != 0:
            raise RuntimeError("%s returned %s: %s" % (
                " ".join(cmd), p.returncode, stderr))
        else:
            return [{'error': False}]

def getlogs(endrev, startrev):
    updaterepo(endrev.branch.project, update=False)

    # TODO: Move all of this onto the model so we can avoid needing to repeat it:
    repo_name = os.path.splitext(
        endrev.branch.project.repo_path.split(os.sep)[-1])[0]
    working_copy = os.path.join(settings.REPOSITORY_BASE_PATH, repo_name)

    cmd = ["git", "log",
            # NULL separated values delimited by 0x1e record separators
            # See PRETTY FORMATS in git-log(1):
            '--format=format:%h%x00%H%x00%at%x00%an%x00%ae%x00%s%x00%b%x1e']

    if endrev.commitid != startrev.commitid:
        cmd.append("%s...%s" % (startrev.commitid, endrev.commitid))
    else:
        cmd.append("-1") # Only return one commit
        cmd.append(endrev.commitid)

    p = Popen(cmd, stdout=PIPE, stderr=PIPE, cwd=working_copy)

    stdout, stderr = p.communicate()

    if p.returncode != 0:
        raise RuntimeError("%s returned %s: %s" % (
                            " ".join(cmd), p.returncode, stderr))
    logs = []
    for log in filter(None, stdout.split("\x1e")):
        (short_commit_id, commit_id, date_t, author_name, author_email,
            subject, body) = log.split("\x00", 7)

        date = datetime.datetime.fromtimestamp(
                                    int(date_t)).strftime("%Y-%m-%d %H:%M:%S")

        logs.append({'date': date, 'message': subject, 'body': body,
                        'author': author_name, 'author_email': author_email,
                        'commitid': commit_id, 'short_commit_id': short_commit_id})

    return logs
