# -*- coding: utf-8 -*-
import simplejson, urllib2
import sys
from xml.dom.minidom import parse
from datetime import datetime
import saveresults

RESULTS_URL = 'http://buildbot.pypy.org/bench_results/'
START_REV = 1
PROJECT = "pypy"
INTERP = "pypy-c-jit"

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
finally:
    datasource.close()
    
# read json result and save to speed.pypy.org
for filename in filelist:
    print "Reading %s..." % filename
    f = urllib2.urlopen(RESULTS_URL + filename)
    result = simplejson.load(f)
    f.close()
    # FIXME: get creation date of file instead of today()
    #os.path.ctime()    - get creation time 
    current_date = datetime.today()
    proj = PROJECT
    revision = result['revision']
    interpreter = INTERP
    int_options = "gc=hybrid"
    if 'branch' in result:
        branch = result['branch']
    else: branch = 'trunk'
    options = ""
    if result.has_key('options'): options = result['options']
    
    saveresults.save(proj, revision, result['results'], options, branch, interpreter, int_options)
print "\nOK"
