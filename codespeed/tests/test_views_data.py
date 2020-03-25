# -*- coding: utf-8 -*-
from django.test import TestCase
from django.test import override_settings

from codespeed.models import Project, Executable, Branch, Revision
from codespeed.views import getbaselineexecutables
from codespeed.views import getcomparisonexes
from codespeed.views_data import get_sanitized_executable_name_for_timeline_view
from codespeed.views_data import get_sanitized_executable_name_for_comparison_view


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


class TestGetComparisonExes(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name='Test')
        self.executable_1 = Executable.objects.create(
            name='TestExecutable1', project=self.project)
        self.executable_2 = Executable.objects.create(
            name='TestExecutable2', project=self.project)
        self.branch_master = Branch.objects.create(name='master',
                                                   project=self.project)
        self.branch_custom = Branch.objects.create(name='custom',
                                                   project=self.project)

        self.revision_1_master = Revision.objects.create(
            branch=self.branch_master, commitid='1')
        self.revision_1_custom = Revision.objects.create(
            branch=self.branch_custom, commitid='1')

    def _insert_mock_revision_objects(self):
        self.rev_v4 = Revision.objects.create(
            branch=self.branch_master, commitid='4', tag='v4.0.0')
        self.rev_v5 = Revision.objects.create(
            branch=self.branch_master, commitid='5', tag='v5.0.0')
        self.rev_v6 = Revision.objects.create(
            branch=self.branch_master, commitid='6', tag='v6.0.0')

    def test_get_comparisonexes_master_default_branch(self):
        # Standard "master" default branch is used
        self.project.default_branch = 'master'
        self.project.save()

        executables, exe_keys = getcomparisonexes()
        self.assertEqual(len(executables), 1)
        self.assertEqual(len(executables[self.project]), 4)
        self.assertEqual(len(exe_keys), 4)

        self.assertEqual(executables[self.project][0]['executable'],
                         self.executable_1)
        self.assertEqual(executables[self.project][0]['revision'],
                         self.revision_1_master)
        self.assertEqual(executables[self.project][0]['key'],
                         '1+L+master')
        self.assertEqual(executables[self.project][0]['name'],
                         'TestExecutable1 latest')
        self.assertEqual(executables[self.project][0]['revision'],
                         self.revision_1_master)

        self.assertEqual(executables[self.project][1]['key'],
                         '2+L+master')
        self.assertEqual(executables[self.project][1]['name'],
                         'TestExecutable2 latest')

        self.assertEqual(executables[self.project][2]['key'],
                         '1+L+custom')
        self.assertEqual(executables[self.project][2]['name'],
                         'TestExecutable1 latest in branch \'custom\'')

        self.assertEqual(executables[self.project][3]['key'],
                         '2+L+custom')
        self.assertEqual(executables[self.project][3]['name'],
                         'TestExecutable2 latest in branch \'custom\'')

        self.assertEqual(exe_keys[0], '1+L+master')
        self.assertEqual(exe_keys[1], '2+L+master')

    def test_get_comparisonexes_custom_default_branch(self):
        # Custom default branch is used
        self.project.default_branch = 'custom'
        self.project.save()

        executables, exe_keys = getcomparisonexes()
        self.assertEqual(len(executables), 1)
        self.assertEqual(len(executables[self.project]), 4)
        self.assertEqual(len(exe_keys), 4)

        self.assertEqual(executables[self.project][0]['executable'],
                         self.executable_1)
        self.assertEqual(executables[self.project][0]['revision'],
                         self.revision_1_master)
        self.assertEqual(executables[self.project][0]['key'],
                         '1+L+master')
        self.assertEqual(executables[self.project][0]['name'],
                         'TestExecutable1 latest in branch \'master\'')
        self.assertEqual(executables[self.project][0]['revision'],
                         self.revision_1_master)

        self.assertEqual(executables[self.project][1]['key'],
                         '2+L+master')
        self.assertEqual(executables[self.project][1]['name'],
                         'TestExecutable2 latest in branch \'master\'')

        self.assertEqual(executables[self.project][2]['key'],
                         '1+L+custom')
        self.assertEqual(executables[self.project][2]['name'],
                         'TestExecutable1 latest')

        self.assertEqual(executables[self.project][3]['key'],
                         '2+L+custom')
        self.assertEqual(executables[self.project][3]['name'],
                         'TestExecutable2 latest')

        self.assertEqual(exe_keys[0], '1+L+master')
        self.assertEqual(exe_keys[1], '2+L+master')
        self.assertEqual(exe_keys[2], '1+L+custom')
        self.assertEqual(exe_keys[3], '2+L+custom')

    def test_get_comparisonexes_branch_filtering(self):
        # branch1 and branch3 have display_on_comparison_page flag set to False
        # so they shouldn't be included in the result
        branch1 = Branch.objects.create(name='branch1', project=self.project,
                                        display_on_comparison_page=False)
        branch2 = Branch.objects.create(name='branch2', project=self.project,
                                        display_on_comparison_page=True)
        branch3 = Branch.objects.create(name='branch3', project=self.project,
                                        display_on_comparison_page=False)

        Revision.objects.create(branch=branch1, commitid='1')
        Revision.objects.create(branch=branch2, commitid='1')
        Revision.objects.create(branch=branch3, commitid='1')

        executables, exe_keys = getcomparisonexes()
        self.assertEqual(len(executables), 1)
        self.assertEqual(len(executables[self.project]), 6)
        self.assertEqual(len(exe_keys), 6)

        expected_exe_keys = [
            '1+L+master',
            '2+L+master',
            '1+L+custom',
            '2+L+custom',
            '1+L+branch2',
            '2+L+branch2'
        ]
        self.assertEqual(exe_keys, expected_exe_keys)

        for index, exe_key in enumerate(expected_exe_keys):
            self.assertEqual(executables[self.project][index]['key'], exe_key)

    def test_get_comparisonexes_tag_name_filtering_no_filter_specified(self):
        # Insert some mock revisions with tags
        self._insert_mock_revision_objects()

        # No COMPARISON_TAGS filters specified, all the tags should be included
        executables, exe_keys = getcomparisonexes()
        self.assertEqual(len(executables), 1)
        self.assertEqual(len(executables[self.project]), 2 * 2 + 2 * 3)
        self.assertEqual(len(exe_keys), 2 * 2 + 2 * 3)

        self.assertExecutablesListContainsRevision(executables[self.project],
                                                   self.rev_v4)
        self.assertExecutablesListContainsRevision(executables[self.project],
                                                   self.rev_v5)
        self.assertExecutablesListContainsRevision(executables[self.project],
                                                   self.rev_v6)

    def test_get_comparisonexes_tag_name_filtering_single_tag_specified(self):
        # Insert some mock revisions with tags
        self._insert_mock_revision_objects()

        # Only a single tag should be included
        with override_settings(COMPARISON_COMMIT_TAGS=['v4.0.0']):
            executables, exe_keys = getcomparisonexes()
            self.assertEqual(len(executables), 1)
            self.assertEqual(len(executables[self.project]), 2 * 2 + 2 * 1)
            self.assertEqual(len(exe_keys), 2 * 2 + 2 * 1)

            self.assertExecutablesListContainsRevision(
                executables[self.project], self.rev_v4)
            self.assertExecutablesListDoesntContainRevision(
                executables[self.project], self.rev_v5)
            self.assertExecutablesListDoesntContainRevision(
                executables[self.project], self.rev_v6)

    def test_get_comparisonexes_tag_name_filtering_empty_list_specified(self):
        # Insert some mock revisions with tags
        self._insert_mock_revision_objects()

        # No tags should be included
        with override_settings(COMPARISON_COMMIT_TAGS=[]):
            executables, exe_keys = getcomparisonexes()
            self.assertEqual(len(executables), 1)
            self.assertEqual(len(executables[self.project]), 2 * 2)
            self.assertEqual(len(exe_keys), 2 * 2)

            self.assertExecutablesListDoesntContainRevision(
                executables[self.project], self.rev_v4)
            self.assertExecutablesListDoesntContainRevision(
                executables[self.project], self.rev_v5)
            self.assertExecutablesListDoesntContainRevision(
                executables[self.project], self.rev_v6)

    def assertExecutablesListContainsRevision(self, executables, revision):
        found = self._executable_list_contains_revision(executables=executables,
                                                        revision=revision)

        if not found:
            self.assertFalse("Didn't find revision \"%s\" in executable list \"%s\"" %
                             (str(revision), str(executables)))

    def assertExecutablesListDoesntContainRevision(self, executables, revision):
        found = self._executable_list_contains_revision(executables=executables,
                                                        revision=revision)

        if found:
            self.assertFalse("Found revision \"%s\", but didn't expect it" %
                             (str(revision)))

    def _executable_list_contains_revision(self, executables, revision):
        for executable in executables:
            if executable['revision'] == revision:
                return True

        return False


class UtilityFunctionsTestCase(TestCase):
    @override_settings(TIMELINE_EXECUTABLE_NAME_MAX_LEN=22)
    def test_get_sanitized_executable_name_for_timeline_view(self):
        executable = Executable(name='a' * 22)
        name = get_sanitized_executable_name_for_timeline_view(executable)
        self.assertEqual(name, 'a' * 22)

        executable = Executable(name='a' * 25)
        name = get_sanitized_executable_name_for_timeline_view(executable)
        self.assertEqual(name, 'a' * 22 + '...')

    @override_settings(COMPARISON_EXECUTABLE_NAME_MAX_LEN=20)
    def test_get_sanitized_executable_name_for_comparison_view(self):
        executable = Executable(name='b' * 20)
        name = get_sanitized_executable_name_for_comparison_view(executable)
        self.assertEqual(name, 'b' * 20)

        executable = Executable(name='b' * 25)
        name = get_sanitized_executable_name_for_comparison_view(executable)
        self.assertEqual(name, 'b' * 20 + '...')
