import os, datetime
from subprocess import Popen, PIPE
from django.conf import settings


def updaterepo(project, update=True):
    repo_name = os.path.splitext(project.repo_path.split(os.sep)[-1])[0]
    working_copy = os.path.join(settings.REPOSITORY_BASE_PATH, repo_name)

    if os.path.exists(working_copy):
        if not update:
            return

        p = Popen(['hg', 'pull', '-u'], stdout=PIPE, stderr=PIPE,
                    cwd=working_copy)
        stdout, stderr = p.communicate()

        if p.returncode != 0 or stderr:
            raise RuntimeError("hg pull returned %s: %s" % (p.returncode,
                                                                stderr))
        else:
            return [{'error': False}]
    else:
        # Clone repo
        cmd = ['hg', 'clone', project.repo_path, repo_name]

        p = Popen(cmd, stdout=PIPE, stderr=PIPE,
                    cwd=settings.REPOSITORY_BASE_PATH)

        stdout, stderr = p.communicate()

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

    cmd = "hg log -r %s:%s -b default --template '{rev}:{node|short}\n{author|person} / {author|user}\n{date}\n{desc}\n=newlog=\n'" % (endrev.commitid, startrev.commitid)
    p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE, cwd=working_copy)
    stdout, stderr = p.communicate()
    if stderr:
        return [{'error': True, 'message': stderr}]
    else:
        logs = []
        for log in stdout.split("=newlog=\n"):
            commitid, author, date, message = ("","","","")
            elements = []
            elements = log.split('\n')[:-1]
            if len(elements) < 4:
                # Don't save "malformed" log
                continue
            else:
                commitid = elements.pop(0)
                author = elements.pop(0)
                date = elements.pop(0)
                # All other newlines should belong to the description text. Join.
                message = '\n'.join(elements)

                # Parse date
                date = date.split('-')[0]
                date = datetime.datetime.fromtimestamp(float(date)).strftime("%Y-%m-%d %H:%M:%S")

                # Add changeset info
                logs.append({
                    'date': date, 'author': author,
                    'message': message,'commitid': commitid})
    return logs
