# -*- coding: utf-8 -*-
import urllib, urllib2
from datetime import datetime
import logging, logging.handlers

## SETUP LOGS ##
LOG_FILENAME = 'pyspeed.log'
logger = logging.getLogger('MyLogger')
logger.setLevel(logging.DEBUG)
# Add the log message handler to the logger
handler = logging.handlers.RotatingFileHandler(
    LOG_FILENAME, maxBytes=100000, backupCount=1)
logger.addHandler(handler)
################

SPEEDURL = "http://localhost:8080/"# This will be pyspeed.pypy.org/
HOST = "Dual Core Linux"

def save(revision, results, options, branch):
    #Parse data
    data = {}
    current_date = datetime.today()
    proj = "pypy"
    interpreter = "pypy-c-jit"
    int_options = "gc=hybrid"
    if branch != "" and branch != "trunk":
        interpreter = branch
        int_options = ""
        
    for b in results:
        bench_name = b[0]
        res_type = b[1]
        results = b[2]
        value = 0
        if res_type == "SimpleComparisonResult":
            value = results['changed_time']
        elif res_type == "ComparisonResult":
            value = results['avg_changed']
        else:
            logger.critical("ERROR: result type unknown " + b[1])
            return 1
        data = {
            'revision_number': revision,
            'revision_project': proj,
            'interpreter_name': interpreter,
            'interpreter_coptions': int_options,
            'benchmark_name': bench_name,
            'environment': HOST,
            'result_value': value,
            'result_date': current_date,
        }
        send(data)
    return 0
    
def send(data):
    #save results
    params = urllib.urlencode(data)
    f = None
    response = "None"
    info = "Saving result for " + data['interpreter_name'] + " revision "
    info += str(data['revision_number']) + ", benchmark " + data['benchmark_name']
    logger.info(info)
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
        logger.critical("Server (%s) response: %s\n" % (SPEEDURL, response))
        return 1   
