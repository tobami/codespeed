#!/usr/bin/env python

# -*- coding: utf-8 -*-

"""
Submit a single result via the RESTful API using requests

Note, that is just an example. You need to add an user
to get the apikey via the /admin
All resources in the result_data dict need to exist.
"""
import json
import requests

def get_data():
    result_data = {
        'commitid': '/api/v1/revision/2/',
        'branch': '/api/v1/branch/1/', # Always use default for trunk/master/tip
        'project': '/api/v1/project/2/',
        'executable': '/api/v1/executable/1/',
        'benchmark': '/api/v1/benchmark/1/',
        'environment': '/api/v1/environment/2/',
        'result_value': 4000,
        }
    headers = {'content-type': 'application/json',
               'Authorization': 'ApiKey apiuser2:2ee0fa1a175ccc3b88b245e799d70470e5d53430'}
    url = 'http://localhost:8000/api/v1/benchmark-result/'
    return(url, result_data, headers)


def main():
    url, result_data, headers = get_data()
    print "{0}: {1}".format(url, result_data)
    r = requests.post(url, data=json.dumps(result_data), headers=headers)
    print r


if __name__ == "__main__":
    main()
