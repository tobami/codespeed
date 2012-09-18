#!/usr/bin/env python

# -*- coding: utf-8 -*-

"""
Check if an environment exists, create otherwise
"""
import json
import urllib2
from optparse import OptionParser, OptionError
from django.utils import simplejson

CODESPEED_URL='http://speedcenter'

def get_options():
    """Get the options and arguments
    """
    parser = OptionParser()

    parser.add_option("-e", "--environment", dest="environment",
                      help="name of the environment to create")

    (options, args) = parser.parse_args()

    if not options.environment:
        parser.error("No environment given")

    return options, args

def is_environment(environment):
    """check if environment does exist

        return:
            True if it exist
            False if it doesn't exist
    """
    url = CODESPEED_URL + '/api/v1/environment/'
    request = urllib2.Request(url)
    opener = urllib2.build_opener()
    try:
        raw_data = opener.open(request)
    except urllib2.HTTPError as e:
        raise e
    data = simplejson.load(raw_data)
    if environment in [ env['name'] for env in data['objects']]:
        return True
    return False

def create_environment(environment):
    """create the environment

        return:
            True if success
            False if not created
    """
    url = CODESPEED_URL + '/api/v1/environment/'
    data = json.dumps({'name': environment})
    request = urllib2.Request(url, data, {'Content-Type': 'application/json'})
    try:
        f = urllib2.urlopen(request)
        response = f.read()
        f.close()
    except urllib2.HTTPError as e:
        raise e
    return response

def main():
    (options, args) = get_options()
    if is_environment(options.environment):
        print "Found environment, doing nothing."
    else:
        print create_environment(options.environment)

if __name__ == "__main__":
    main()

