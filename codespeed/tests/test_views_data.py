# -*- coding: utf-8 -*-
from django.test import TestCase

from codespeed.models import Project, Executable, Branch, Revision
from codespeed.views import getbaselineexecutables


class TestGetBaselineExecutables(TestCase):
    """Test helper functions in codespeed.views"""

    def setUp(self):
        self.project = Project.objects.create(name='Test')
        self.executable = Executable.objects.create(
            name='TestExecutable', project=self.project)
        self.branch = Branch.objects.create(name='master',
                                            project=self.project)

    def test_get_baseline_executables(self):
        # No revisions, no baseline
        result = getbaselineexecutables()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['executable'], 'none')

        # Check that a tagged revision will be included as baseline
        revision1 = Revision.objects.create(commitid='1', tag='0.1',
                                            branch=self.branch)
        result = getbaselineexecutables()
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['executable'], 'none')
        self.assertEqual(result[1]['executable'], self.executable)
        self.assertEqual(result[1]['revision'], revision1)

        Revision.objects.create(commitid='2', tag='0.2', branch=self.branch)
        result = getbaselineexecutables()
        self.assertEqual(len(result), 3)

        # An untagged revision will not be available as baseline
        Revision.objects.create(commitid='3', branch=self.branch)
        result = getbaselineexecutables()
        self.assertEqual(len(result), 3)
