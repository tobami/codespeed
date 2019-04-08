# -*- coding: utf-8 -*-
"""
Create the default branch for all existing projects
Starting v 0.8.0 that is mandatory.

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
from codespeed.models import Branch, Project


def main():
    """Add Branch default to projects if not there"""
    projects = Project.objects.all()

    for proj in projects:
        if not proj.branches.filter(name='default'):
            trunk = Branch(name='default', project=proj)
            trunk.save()
            print "Created branch 'default' for project {0}".format(proj)


if __name__ == '__main__':
    main()
