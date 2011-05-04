import sys
import os
## Setup to import models from Django app ##
sys.path.append(os.path.abspath('..'))
os.environ['DJANGO_SETTINGS_MODULE'] ='speedcenter.settings'

from django.core.management import setup_environ
from speedcenter import settings
from speedcenter.codespeed.models import Revision, Branch
setup_environ(settings)

from django.db.models import Q

branches = Branch.objects.filter(Q(name='trunk') | Q(name=''))

for branch in branches:
    for rev in Revision.objects.filter(project=branch.project):
        rev.branch = branch
        rev.save()
