# -*- coding: utf-8 -*-
####################################################
# Sample script that shows how to save result data #
####################################################
from datetime import datetime
import urllib, urllib2

CODESPEED_URL = 'http://localhost:8000/'

data = {
    'commitid': '23238',
    'project': 'pypy',
    'revision_date': "2009-11-15 18:11:29", # Optional. Default is taken
                                            # either from VCS integration or from current date
    'executable_name': 'pypy-c-jit',
    'executable_coptions': 'gc=Hybrid', # Optional default is blank
    'benchmark': 'Richards',
    'benchmark_type': 'C', # Optional. Default is C for Cross-project.
    'environment': "bigdog",
    'result_value': 400,
    'result_date': datetime.today(), # Optional
    'units': "fps", # Optional. Default is seconds
    'lessisbetter': False, # Optional. Default is True
    'std_dev': 1.11111, # Optional. Default is blank
    'max': 2, # Optional. Default is blank
    'min': 1.0, # Optional. Default is blank
}

def add(data):
    params = urllib.urlencode(data)
    f = None
    response = "None"
    print "Executable %s, revision %s, benchmark %s" % (data['executable_name'], data['commitid'], data['benchmark'])
    try:
        f = urllib2.urlopen(CODESPEED_URL + 'result/add/', params)
        response = f.read()
        f.close()
    except urllib2.URLError, e:
        if hasattr(e, 'reason'):
            response = '\n  We failed to reach a server\n'
            response += '  Reason: ' + str(e.reason)
        elif hasattr(e, 'code'):
            response = '\n  The server couldn\'t fulfill the request\n'
            response += '  Error code: ' + str(e)
    print "Server (%s) response: %s\n" % (CODESPEED_URL, response)

if __name__ == "__main__":
    add(data)
