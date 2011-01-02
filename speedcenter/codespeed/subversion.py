# -*- coding: utf-8 -*-
'''Subversion commit logs support'''
from datetime import datetime


def updaterepo():
    '''Not needed for a remote subversion repo'''
    return [{'error': False}]

def getlogs(newrev, startrev):
    import pysvn
    
    logs = []
    log_messages = []
    loglimit = 200
    
    def get_login(realm, username, may_save):
        return True, newrev.project.repo_user, newrev.project.repo_pass, False
    
    client = pysvn.Client()
    if newrev.project.repo_user != "":
        client.callback_get_login = get_login
    
    try:
        log_messages = \
            client.log(
                newrev.project.repo_path,
                revision_start=pysvn.Revision(
                        pysvn.opt_revision_kind.number, startrev.commitid
                ),
                revision_end=pysvn.Revision(
                    pysvn.opt_revision_kind.number, newrev.commitid
                )
            )
    except pysvn.ClientError:
        return [
            {'error': True,
            'message': "Could not resolve '" + newrev.project.repo_path + "'"}]
    except ValueError:
        return [{
            'error': True,
            'message': "'%s' is an invalid subversion revision number" % newrev.commitid
        }]
    log_messages.reverse()
    s = len(log_messages)
    while s > loglimit:
        log_messages = log_messages[:s]
        s = len(log_messages) - 1
    
    for log in log_messages:
        try:
            author = log.author
        except AttributeError:
            author = ""
        date = datetime.fromtimestamp(log.date).strftime("%Y-%m-%d %H:%M:%S")
        message = log.message
        # Add log unless it is the last commit log, which has already been tested
        logs.append({
            'date': date, 'author': author, 'message': message,
            'commitid': log.revision.number})
    return logs
