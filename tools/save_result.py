# -*- coding: utf-8 -*-
from datetime import datetime
import urllib, urllib2

SPEEDURL = 'http://localhost:8080/'# This will be pyspeed.pypy.org/

data = {
    'revision_number': '23238',
    'revision_project': 'pypy',
    'revision_date': "2009-11-15 18:11:29", # Optional. Make mandatory?
    'interpreter_name': 'pypy-c-jit',
    'interpreter_coptions': 'gc=Hybrid',
    'benchmark_name': 'Richards',
    'benchmark_type': 'P',# Optional. Default is T for Trunk. (Trunk, Debug, Python, Multilanguage)
    'environment': "Dual Core Linux",
    'result_value': 400,
    'result_type': 'M',# Optional. Default is 'T' for Time in milliseconds. (Time, Memory, Score)
    'result_date': datetime.today(),
}

def add(data):
    params = urllib.urlencode(data)
    f = None
    response = "None"
    print "Interpreter %s, revision %s, benchmark %s" % (data['interpreter_name'], data['revision_number'], data['benchmark_name'])
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
    add_result(data)
