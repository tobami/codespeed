# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import subprocess
import tempfile
import os

from django.test import TestCase, override_settings
from django.urls import reverse

from codespeed.models import (Project, Benchmark, Revision, Branch, Executable,
                              Environment, Result, Report)

hgdir = ''

def setUpModule():
    global hgdir
    hgdir = tempfile.TemporaryDirectory()
    subprocess.check_call(['hg', 'init'], cwd=hgdir.name)
    # Add some commits
    readme = os.path.join(hgdir.name, 'README.md')
    file1 = os.path.join(hgdir.name, 'file1.py')
    with open(readme, 'w') as hg_file:
        hg_file.write('readme')
    subprocess.check_call(['hg', 'add', readme], cwd=hgdir.name)
    subprocess.check_call(['hg', 'commit', '-m', "first commit"], cwd=hgdir.name)
    with open(file1, 'w') as hg_file:
        hg_file.write('value = 10')
    subprocess.check_call(['hg', 'add', file1], cwd=hgdir.name)
    subprocess.check_call(['hg', 'commit', '-m', "second commit"], cwd=hgdir.name)

def tearDownModule():
    hgdir.cleanup()

class TestMercurial(TestCase):

    def setUp(self):
        self.days = 0
        self.hgdir = hgdir.name
        self.starttime = datetime.now() + timedelta(days=-100)

        Project(repo_type='M', name='pro',
                repo_path=str(self.hgdir)).save()
        self.pro = Project.objects.get(name='pro')

        Branch(project=self.pro, name='default').save()
        self.b = Branch.objects.get(name='default')

        Environment(name='Walden Pond').save()
        Executable(name='walden', project=self.pro).save()
        Benchmark(name='TestBench').save()

        self.env = Environment.objects.get(name='Walden Pond')
        self.exe = Executable.objects.get(name='walden')
        self.bench = Benchmark.objects.get(name='TestBench')
        cmd = ['hg', '-R', self.hgdir, 'id', '-r', '1']
        self.cid = subprocess.check_output(cmd).split()[0]
        Revision(commitid=self.cid.decode('utf-8'), date=self.starttime, branch=self.b,
                 project=self.pro).save()

    def test_hg(self):
        response = self.client.get(reverse('displaylogs'), {'revisionid':1})
        assert response.status_code == 200, 'expected 200 got %d' % response.status_code
