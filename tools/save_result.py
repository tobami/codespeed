# -*- coding: utf-8 -*-
from datetime import datetime
import urllib, urllib2

BASEURL = 'http://localhost:8080/'# This will be pyspeed.pypy.org/

def add_result():
    data = {
        'revision_number': '23238',
        'revision_project': 'pypy',
        'revision_date': "2009-11-15 18:11:29", # Optional. Make mandatory?
        'interpreter_name': 'pypy-c-jit',
        'interpreter_coptions': 'gc=Boehm',
        'benchmark_name': 'Richards',
        'benchmark_type': 'P',# Optional. Default is T for Trunk. (Trunk, Debug, Python, Multilanguage)
        'environment': "Dual Core Linux",
        'result_key': 'total',
        'result_value': 400,
        'result_type': 'M',# Optional. Default is 'T' for Time in milliseconds. (Time, Memory, Score)
        'result_date': datetime.today(),
    }
    
    # TODO add HTTPError try
    params = urllib.urlencode(data)
    f = urllib2.urlopen(BASEURL + 'result/add/', params)
    response = f.read()
    print "Server response:", response
    f.close()

if __name__ == "__main__":
    add_result()
