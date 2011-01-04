# -*- coding: utf-8 -*-
################################################################################
# This script imports PyPy's result data from json files located on the server #
################################################################################
import simplejson, urllib2
import sys
from xml.dom.minidom import parse
from datetime import datetime
import saveresults, savecpython

RESULTS_URLS = {
    'pypy-c-jit': 'http://buildbot.pypy.org/bench_results/',
    'pypy-c':  'http://buildbot.pypy.org/bench_results_nojit/',
}
START_REV = 79485
END_REV = 79485
PROJECT = "PyPy"

for INTERP in RESULTS_URLS:
    RESULTS_URL = RESULTS_URLS[INTERP]
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
                        if int(filename.replace(".json", "")) >= START_REV and\
                            int(filename.replace(".json", "")) <= END_REV:
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
        proj = PROJECT
        revision = result['revision']
        interpreter = INTERP
        int_options = ""
        options = ""
        if result.has_key('options'): options = result['options']
        
        host = 'tannit'
        #saveresults.save(proj, revision, result['results'], options, interpreter, host)
        if filename == filelist[len(filelist)-1]:
            savecpython.save('cpython', '100', result['results'], options, 'cpython', host)
print "\nOK"
