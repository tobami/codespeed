# -*- coding: utf-8 -*-
####################################################
# Sample script that shows how to save result data #
####################################################
from datetime import datetime
import urllib
import urllib2

# You need to enter the real URL and have the server running
CODESPEED_URL = 'http://localhost:8000/'

current_date = datetime.today()

# Mandatory fields
data = {
    'commitid': '14',
    'branch': 'default',  # Always use default for trunk/master/tip
    'project': 'MyProject',
    'executable': 'myexe O3 64bits',
    'benchmark': 'float',
    'environment': "Dual Core",
    'result_value': 4000,
}

# Optional fields
data.update({
    'revision_date': current_date,  # Optional. Default is taken either
                                    # from VCS integration or from current date
    'result_date': current_date,  # Optional, default is current date
    'std_dev': 1.11111,  # Optional. Default is blank
    'max': 4001.6,  # Optional. Default is blank
    'min': 3995.1,  # Optional. Default is blank
})


def add(data):
    params = urllib.urlencode(data)
    response = "None"
    print "Saving result for executable %s, revision %s, benchmark %s" % (
        data['executable'], data['commitid'], data['benchmark'])
    try:
        f = urllib2.urlopen(CODESPEED_URL + 'result/add/', params)
    except urllib2.HTTPError as e:
        print str(e)
        print e.read()
        return
    response = f.read()
    f.close()
    print "Server (%s) response: %s\n" % (CODESPEED_URL, response)

if __name__ == "__main__":
    add(data)
