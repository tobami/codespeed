import os, datetime
from subprocess import Popen, PIPE
from speedcenter import settings


path = settings.BASEDIR + '/repos/'
    
def updaterepo(repo):
    repodir = path + repo.split('/')[-1] + "/"
    if os.path.exists(repodir):
        # Update repo
        cmd = "hg pull -u"
        p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE, cwd=repodir)
        stdout, stderr = p.communicate()
        if stderr:
            return [{'error': True, 'message': stderr}]
        else:
            return [{'error': False}]
    else:
        # Clone repo
        cmd = "hg clone %s" % repo
        p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE, cwd=path)
        stdout, stderr = p.communicate()
        if stderr:
            return [{'error': True, 'message': stderr}]
        else:
            return [{'error': False}]

def getlogs(endrev, startrev):
    repodir = path + endrev.project.repo_path.split('/')[-1] + "/"
    if not os.path.exists(repodir):
        updaterepo(endrev.project.repo_path)
    
    cmd = "hg log -r %s:%s -b default --template '{rev}:{node|short}\n{author|person} / {author|user}\n{date}\n{desc}\n=newlog=\n'" % (endrev.commitid, startrev.commitid)
    p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE, cwd=repodir)
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
