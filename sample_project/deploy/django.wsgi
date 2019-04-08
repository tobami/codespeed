# -*- coding: utf-8 -*-

"""
WSGI config
"""

import os
import sys

current_dir = os.path.abspath(os.path.dirname(__file__).replace('\\','/'))
dirs = current_dir.split(os.path.sep)
del(dirs[-1])
codespeed_dir = os.path.sep.join(dirs)
del(dirs[-1])
project_dir = os.path.sep.join(dirs)

sys.path.append(project_dir)
sys.path.append(codespeed_dir)
os.environ['DJANGO_SETTINGS_MODULE'] = codespeed_dir.split(os.path.sep)[-1] + '.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

