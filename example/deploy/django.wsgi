import os, sys

current_dir = os.path.abspath( os.path.dirname(__file__).replace('\\','/') )
dirs = current_dir.split("/")
del(dirs[-1])
codespeed_dir = "/".join(dirs)
del(dirs[-1])
project_dir = "/".join(dirs)

sys.path.append(project_dir)
sys.path.append(codespeed_dir)
os.environ['DJANGO_SETTINGS_MODULE'] = 'speedcenter.settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
