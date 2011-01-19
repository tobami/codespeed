from subprocess import Popen, PIPE
import datetime
import os

from django.conf import settings


def updaterepo(project, update=True):
    repo_name = os.path.splitext(project.repo_path.split(os.sep)[-1])[0]
    working_copy = os.path.join(settings.REPOSITORY_BASE_PATH, repo_name)

    if os.path.exists(working_copy):
        if not update:
            return
        else:
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
        stdout, stderr = p.communicate()

        if stderr:
            if p.returncode != 0:
                raise RuntimeError("%s returned %s: %s" % (" ".join(cmd),
                                                            p.returncode,
                                                            stderr))
        else:
            return [{'error': False}]

def getlogs(endrev, startrev):
    updaterepo(endrev.project, update=False)

    # TODO: Move all of this onto the model so we can avoid needing to repeat it:
    repo_name = os.path.splitext(endrev.project.repo_path.split(os.sep)[-1])[0]
    working_copy = os.path.join(settings.REPOSITORY_BASE_PATH, repo_name)

    cmd = ["git", "log",
            # Tab separated host, author date as Unix timestamp, author
            # name, and subject - see PRETTY FORMATS in git-log(1):
            '--format=format:%H%x09%at%x09%an%x09%s']

    if endrev.commitid != startrev.commitid:
        cmd.append("%s...%s" % (startrev.commitid, endrev.commitid))
    else:
        cmd.append("-1") # Only return one commit
        cmd.append(endrev.commitid)

    p = Popen(cmd, stdout=PIPE, stderr=PIPE, cwd=working_copy)

    stdout, stderr = p.communicate()

    if p.returncode != 0:
        raise RuntimeError("%s returned %s: %s" % (" ".join(cmd),
                                                    p.returncode,
                                                    stderr))
    logs = []

    for log in stdout.split("\n"):
        commit_id, date_t, author, subject = log.split('\t', 4)

        date = datetime.datetime.fromtimestamp(int(date_t)).strftime("%Y-%m-%d %H:%M:%S")

        logs.append({'date': date, 'author': author, 'message': subject,
                        'commitid': commit_id})

    return logs
