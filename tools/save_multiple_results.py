# -*- coding: utf-8 -*-
####################################################
# Sample script that shows how to save result data using json #
####################################################
import urllib, urllib2, json

# You need to enter the real URL and have the server running
CODESPEED_URL = 'http://localhost:8000/'

sample_data = [
    {
        "commitid": "8",
        "project": "MyProject",
        "branch": "default",
        "executable": "myexe O3 64bits",
        "benchmark": "float",
        "environment": "Dual Core",
        "result_value": 2500.0
    },
    {
        "commitid": "8",
        "project": "MyProject",
        "branch": "default",
        "executable": "myexe O3 64bits",
        "benchmark": "int",
        "environment": "Dual Core",
        "result_value": 1100
    }
]

def add(data):
    #params = urllib.urlencode(data)
    response = "None"
    try:
        f = urllib2.urlopen(
            CODESPEED_URL + 'result/add/json/', urllib.urlencode(data))
    except urllib2.HTTPError as e:
        print str(e)
        print e.read()
        return
    response = f.read()
    f.close()
    print "Server (%s) response: %s\n" % (CODESPEED_URL, response)


if __name__ == "__main__":
    data = {'json': json.dumps(sample_data)}
    add(data)
