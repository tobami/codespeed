# -*- coding: utf-8 -*-
from datetime import datetime
import urllib, urllib2

SPEEDURL = 'http://localhost:8000/'# This will be pyspeed.pypy.org/

data = {
    'commitid': '23238',
    'project': 'pypy',
    'branch': 'trunk',
    'revision_date': "2009-11-15 18:11:29", # Optional. Make mandatory?
    'interpreter_name': 'pypy-c-jit',
    'interpreter_coptions': 'gc=Hybrid',
    'benchmark': 'Richards',
    'benchmark_type': 'C',# Optional. Default is C for Cross-project.
    'environment': "bigdog",
    'result_value': 400,
    'result_date': datetime.today(),
}

def add(data):
    params = urllib.urlencode(data)
    f = None
    response = "None"
    print "Interpreter %s, revision %s, benchmark %s" % (data['interpreter_name'], data['commitid'], data['benchmark'])
    try:
        f = urllib2.urlopen(SPEEDURL + 'result/add/', params)
        response = f.read()
        f.close()
    except urllib2.URLError, e:
        if hasattr(e, 'reason'):
            response = '\n  We failed to reach a server\n'
            response += '  Reason: ' + str(e.reason)
        elif hasattr(e, 'code'):
            response = '\n  The server couldn\'t fulfill the request\n'
            response += '  Error code: ' + str(e)
    print "Server (%s) response: %s\n" % (SPEEDURL, response)

if __name__ == "__main__":
    add(data)
