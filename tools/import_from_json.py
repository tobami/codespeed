# -*- coding: utf-8 -*-
import simplejson, urllib, urllib2
import sys
from xml.dom.minidom import parse
from datetime import datetime

RESULTS_URL = 'http://buildbot.pypy.org/bench_results/'
SPEEDURL = 'http://speed.pypy.org/'
SAVE_CPYTHON = False
START_REV = 71943
INTERP = "pypy-c-jit"

def saveresult(data):
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

# get json filenames
filelist = []
try:
    datasource = urllib2.urlopen(RESULTS_URL)
    dom = parse(datasource)
    for elem in dom.getElementsByTagName('td'):
        for e in elem.childNodes:
            if len(e.childNodes):
                filename = e.firstChild.toxml()
                if e.tagName == "a" and ".json" in filename:
                    if int(filename.replace(".json", "")) >= START_REV:
                        filelist.append(filename)
    datasource.close()
except urllib2.URLError, e:
    response = "None"
    if hasattr(e, 'reason'):
        response = '\n  We failed to reach ' + RESULTS_URL + '\n'
        response += '  Reason: ' + str(e.reason)
    elif hasattr(e, 'code'):
        response = '\n  The server couldn\'t fulfill the request\n'
        response += '  Error code: ' + str(e)
    print "Results Server (%s) response: %s\n" % (RESULTS_URL, response)
    sys.exit(1)

# read json result and save to speed.pypy.org
for filename in filelist:
    print "Reading %s..." % filename
    f = urllib2.urlopen(RESULTS_URL + filename)
    result = simplejson.load(f)
    f.close()
    current_date = datetime.today()
    proj = 'pypy'
    revision = result['revision']
    interpreter = INTERP
    int_options = "gc=hybrid"
    if result.has_key('branch'):
        if result['branch'] != 'trunk':
            interpreter = result['branch']
            int_options = ""
    if SAVE_CPYTHON:
        proj = 'cpython'
        interpreter = 'cpython'
        int_options = 'default'
        revision = 262
    
    for b in result['results']:
        bench_name = b[0]
        res_type = b[1]
        results = b[2]
        value = 0
        if res_type == "SimpleComparisonResult":
            if SAVE_CPYTHON:
                value = results['base_time']   
            else:
                value = results['changed_time']
        elif res_type == "ComparisonResult":
            if SAVE_CPYTHON:
                value = results['avg_base']
            else:
                value = results['avg_changed']
        else:
            print "ERROR: result type unknown", b[1]
            sys.exit(1)
        data = {
            'revision_number': revision,
            'revision_project': proj,
            'interpreter_name': interpreter,
            'interpreter_coptions': int_options,
            'benchmark_name': bench_name,
            'environment': "bigdog",
            'result_value': value,
            'result_date': current_date,
        }
        saveresult(data)
print "\nOK"
