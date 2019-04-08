import timeit
import urllib
import sys


SPEEDURL = 'http://localhost:8000/'

benchmarks = ['ai', 'django',  'spambayes', 'grid']


def test_overview():
    data = {
        "trend": 10,
        "baseline": 1,
        "revision": 73893,
        "executable": "1",
        "host": "bigdog",
    }
    params = urllib.urlencode(data)
    page = urllib.urlopen(SPEEDURL + 'overview/table/?' + params)
    jsonstring = page.read()
    page.close()
    if not '<table id="results" class="tablesorter">' in jsonstring:
        print "bad overview response"
        sys.exit(1)


def test_timeline(bench):
    data = {
        "executables": "1,2,6",
        "baseline": "true",
        "benchmark": bench,
        "host": "bigdog",
        "revisions": 200
    }
    params = urllib.urlencode(data)
    page = urllib.urlopen(SPEEDURL + 'timeline/json/?' + params)
    jsonstring = page.read()
    #print jsonstring
    page.close()
    if not '"lessisbetter": " (less is better)", "baseline":' in jsonstring \
        or not', "error": "None"}' in jsonstring:
        print "bad timeline response"
        sys.exit(1)

if __name__ == "__main__":
    t = timeit.Timer('test_overview()', 'from __main__ import test_overview')
    results = t.repeat(20, 1)
    print
    print "OVERVIEW RESULTS"
    print "min:", min(results)
    print "avg:", sum(results) / len(results)
    print
    print "TIMELINE RESULTS"
    for bench in benchmarks:
        t = timeit.Timer('test_timeline("' + bench + '")',
            'from __main__ import test_timeline')
        results = t.repeat(20, 1)
        print "benchmark =", bench
        print "min:", min(results)
        print "avg:", sum(results) / len(results)
    print
