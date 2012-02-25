# encoding: utf-8

from urlparse import urljoin
import logging
import platform
import urllib
import sys


def save_to_speedcenter(url=None, project=None, commitid=None, executable=None,
                        benchmark=None, result_value=None, **kwargs):
    """Save a benchmark result to your speedcenter server

    Mandatory:

    :param url:
        Codespeed server endpoint
        (e.g. `http://codespeed.example.org/result/add/`)
    :param project:
        Project name
    :param commitid:
        VCS identifier
    :param executable:
        The executable name
    :param benchmark:
        The name of this particular benchmark
    :param float result_value:
        The benchmark result

    Optional:

    :param environment:
        System description
    :param date revision_date:
        Optional, default will be either VCS commit, if available, or the
        current date
    :param date result_date:
        Optional
    :param float std_dev:
        Optional
    :param float max:
        Optional
    :param float min:
        Optional
    """

    data = {
        'project': project,
        'commitid': commitid,
        'executable': executable,
        'benchmark': benchmark,
        'result_value': result_value,
    }

    data.update(kwargs)

    if not data.get('environment', None):
        data['environment'] = platform.platform(aliased=True)

    f = urllib.urlopen(url, urllib.urlencode(data))

    response = f.read()
    status = f.getcode()

    f.close()

    if status == 202:
        logging.debug("Server %s: HTTP %s: %s", url, status, response)
    else:
        raise IOError("Server %s returned HTTP %s" % (url, status))


if __name__ == "__main__":
    from optparse import OptionParser

    parser = OptionParser()
    parser.add_option("--benchmark")
    parser.add_option("--commitid")
    parser.add_option("--environment",
        help="Use a custom Codespeed environment")
    parser.add_option("--executable")
    parser.add_option("--max", type="float")
    parser.add_option("--min", type="float")
    parser.add_option("--project")
    parser.add_option("--branch")
    parser.add_option("--result-date")
    parser.add_option("--result-value", type="float")
    parser.add_option("--revision_date")
    parser.add_option("--std-dev", type="float")
    parser.add_option("--url",
        help="URL of your Codespeed server (e.g. http://codespeed.example.org)")

    (options, args) = parser.parse_args()

    if args:
        parser.error("All arguments must be provided as command-line options")

    # Yes, the optparse manpage has a snide comment about "required options"
    # being gramatically dubious. Yes, it's still wrong about not needing to
    # do this.
    required = ('url', 'environment', 'project', 'commitid', 'executable',
                'benchmark', 'result_value')

    if not all(getattr(options, i) for i in required):
        parser.error("The following parameters must be provided:\n\t%s" % "\n\t".join(
            "--%s".replace("_", "-") % i for i in required))

    kwargs = {}
    for k, v in options.__dict__.items():
        if v is not None:
            kwargs[k] = v
    kwargs.setdefault('branch', 'default')

    if not kwargs['url'].endswith("/result/add/"):
        kwargs['url'] = urljoin(kwargs['url'], '/result/add/')

    try:
        save_to_speedcenter(**kwargs)
        sys.exit(0)
    except StandardError, e:
        logging.error("Error saving results: %s", e)
        sys.exit(1)
