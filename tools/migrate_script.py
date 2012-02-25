# -*- coding: utf-8 -*-
"""Adds the default branch to all existing revisions

Note: This file is assumed to be in the same directory
as the project settings.py. Otherwise you have to set the
shell environment DJANGO_SETTINGS_MODULE
"""
import sys
import os


## Setup to import models from Django app ##
def import_from_string(name):
    """helper to import module from a given string"""

    components = name.split('.')[1:]
    return reduce(lambda mod, y: getattr(mod, y), components, __import__(name))

sys.path.append(os.path.abspath('..'))

if 'DJANGO_SETTINGS_MODULE' in os.environ:
    settings = import_from_string(os.environ['DJANGO_SETTINGS_MODULE'])
else:
    try:
        import settings  # Assumed to be in the same directory.
    except ImportError:
        import sys
        sys.stderr.write(
            "Error: Can't find the file 'settings.py' in the directory "
            "containing %r. It appears you've customized things.\nYou'll have "
            "to run django-admin.py, passing it your settings module.\n(If the"
            " file settings.py does indeed exist, it's causing an ImportError "
            "somehow.)\n" % __file__)
        sys.exit(1)

from django.core.management import setup_environ
setup_environ(settings)

from codespeed.models import Revision, Branch


def main():
    """add default branch to revisions"""
    branches = Branch.objects.filter(name='default')

    for branch in branches:
        for rev in Revision.objects.filter(project=branch.project):
            rev.branch = branch
            rev.save()

if __name__ == '__main__':
    main()
