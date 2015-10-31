# -*- coding: utf-8 -*-
import os

from django.conf import settings
from django.test import TestCase

from codespeed.models import Project


class TestProject(TestCase):

    def setUp(self):
        self.github_project = Project(
            repo_type='H', repo_path='https://github.com/tobami/codespeed.git')
        self.git_project = Project(repo_type='G',
                                   repo_path='/home/foo/codespeed')

    def test_repo_name(self):
        """Test that only projects with local repositories have a repo_name attribute
        """
        self.assertEqual(self.git_project.repo_name, 'codespeed')

        self.assertRaises(AttributeError, getattr,
                          self.github_project, 'repo_name')

    def test_working_copy(self):
        """Test that only projects with local repositories have a working_copy
        attribute

        """
        self.assertEqual(self.git_project.working_copy,
                         os.path.join(settings.REPOSITORY_BASE_PATH,
                                      self.git_project.repo_name))

        self.assertRaises(
            AttributeError, getattr, self.github_project, 'working_copy')

    def test_github_browsing_url(self):
        """If empty, the commit browsing url will be filled in with a default
        value when using github repository.
        """

        # It should work with https:// as well as git:// urls
        self.github_project.save()
        self.assertEquals(self.github_project.commit_browsing_url,
                          'https://github.com/tobami/codespeed.git/'
                          'commit/{commitid}')

        self.github_project.repo_path = 'git://github.com/tobami/codespeed.git'
        self.github_project.save()
        self.assertEquals(self.github_project.commit_browsing_url,
                          'https://github.com/tobami/codespeed.git/'
                          'commit/{commitid}')

        # If filled in, commit browsing url should not change
        self.github_project.commit_browsing_url = 'https://example.com/{commitid}'
        self.github_project.save()
        self.assertEquals(self.github_project.commit_browsing_url,
                          'https://example.com/{commitid}')
