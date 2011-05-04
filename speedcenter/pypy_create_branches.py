import sys
import os
## Setup to import models from Django app ##
sys.path.append(os.path.abspath('..'))
os.environ['DJANGO_SETTINGS_MODULE'] ='speedcenter.settings'

from django.core.management import setup_environ
from speedcenter import settings
from speedcenter.codespeed.models import Project, Branch
setup_environ(settings)

pypy, cpython = Project.objects.all()
pypy_trunk = Branch(name="trunk", project=pypy)
cpython_trunk = Branch(name="trunk", project=cpython)

pypy_trunk.save()
cpython_trunk.save()
