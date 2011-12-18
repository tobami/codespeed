#!/usr/bin/env python

# -*- coding: utf-8 -*-

"""
Create an API key for all users that are active
"""
import sys
import os

## Setup to import models from Django app ##
def import_from_string(name):
    """helper to import module from a given string"""

    components = name.split('.')[1:]
    return reduce(lambda mod, y: getattr(mod, y), components, __import__(name))

sys.path.append(os.path.abspath('..'))
if os.environ.has_key('DJANGO_SETTINGS_MODULE'):
    settings = import_from_string(os.environ['DJANGO_SETTINGS_MODULE'])
else:
    try:
        import settings # Assumed to be in the same directory.
    except ImportError:
        import sys
        sys.stderr.write(
            "Error: Can't find the file 'settings.py' in the directory "
            "containing %r. It appears you've customized things.\nYou'll have "
            "to run django-admin.py, passing it your settings module.\n(If the "
            "file settings.py does indeed exist, it's causing an ImportError "
            "somehow.)\n" % __file__)
        sys.exit(1)

from django.core.management import setup_environ
setup_environ(settings)

from django.contrib.auth.models import User
from tastypie.models import ApiKey

def main():
    for user in User.objects.all(is_active=True):
        ApiKey.objects.create(user=user) 

if __name__ == '__main__':
    main()

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 fileencoding=utf-8 :

