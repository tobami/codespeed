import sys
import os
## Setup to import models from Django app ##
sys.path.append(os.path.abspath('..'))
os.environ['DJANGO_SETTINGS_MODULE'] ='speedcenter.settings'

from django.core.management import setup_environ
from speedcenter import settings
from speedcenter.codespeed.models import Branch, Project
setup_environ(settings)

projects = Project.objects.all()

for proj in projects:
    trunk = Branch(name='trunk', project = proj)
    trunk.save()
