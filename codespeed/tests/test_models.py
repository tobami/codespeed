# -*- coding: utf-8 -*-
import os

from django.conf import settings
from django.test import TestCase, override_settings

from codespeed.models import (Project, Report, Revision, Branch, Environment,
                              Benchmark, Executable, Result)
from datetime import timedelta, datetime


@override_settings(CHANGE_THRESHOLD=3.0, TREND_THRESHOLD=5.0)
class TestReport(TestCase):

    def setUp(self):
        self.days = 0
        self.starttime = datetime.now() + timedelta(days=-100)

        Project(repo_type='G', name='pro',
                repo_path='/home/foo/codespeed').save()
        self.pro = Project.objects.get(name='pro')

        Branch(project=self.pro, name='branch').save()
        self.b = Branch.objects.get(name='branch')

        Environment(name='Walden Pond').save()
        Executable(name='walden', project=self.pro).save()
        Benchmark(name='TestBench').save()

        self.env = Environment.objects.get(name='Walden Pond')
        self.exe = Executable.objects.get(name='walden')
        self.bench = Benchmark.objects.get(name='TestBench')

    def test_average_change_bad(self):
        self.make_result(12)
        s2 = self.make_result(15)
        rep = self.make_report(s2)
        self.assertEqual(rep.colorcode, 'red')

    def test_average_change_good(self):
        self.make_result(15)
        s2 = self.make_result(12)
        rep = self.make_report(s2)
        self.assertEqual(rep.colorcode, 'green')

    def test_within_threshold_none(self):
        self.make_result(15)
        s2 = self.make_result(15.2)
        rep = self.make_report(s2)
        self.assertEqual(rep.colorcode, 'none')

    def test_initial_revision_none(self):
        s2 = self.make_result(15)
        rep = self.make_report(s2)
        self.assertEqual(rep.colorcode, 'none')

    def test_bench_change_good(self):
        b1 = self.make_bench('b1')

        s1 = self.make_result(15)
        self.make_result(15, rev=s1, benchmark=b1)

        s2 = self.make_result(14.54)
        self.make_result(15, rev=s2, benchmark=b1)

        rep = self.make_report(s2)
        self.assertEqual(rep.colorcode, 'green')
        self.assertIn(self.bench.name, rep.summary)

    def test_bench_change_bad(self):
        b1 = self.make_bench('b1')

        s1 = self.make_result(15)
        self.make_result(15, rev=s1, benchmark=b1)

        s2 = self.make_result(15.46)
        self.make_result(15, rev=s2, benchmark=b1)

        rep = self.make_report(s2)
        self.assertEqual(rep.colorcode, 'red')
        self.assertIn(self.bench.name, rep.summary)

    # NOTE: Don't need to test with multiple projects since the calculation of
    # urgency doesn't take projects into account

    def test_average_change_beats_bench_change(self):
        b1 = self.make_bench('b1')

        s1 = self.make_result(15)
        self.make_result(15, rev=s1, benchmark=b1)

        s2 = self.make_result(14)
        self.make_result(15, rev=s2, benchmark=b1)

        rep = self.make_report(s2)
        self.assertIn('Average', rep.summary)

    def test_good_benchmark_change_beats_bad_average_trend(self):
        changes = self.make_bad_trend()
        b1 = self.make_bench('b1')
        for x in changes:
            s1 = self.make_result(x)
            if x != changes[-1]:
                self.make_result(x, rev=s1, benchmark=b1)
        self.make_result(changes[-2] * .97, rev=s1, benchmark=b1)
        rep = self.make_report(s1)
        self.assertEquals('green', rep.colorcode)
        self.assertIn('b1', rep.summary)

    def test_good_average_change_beats_bad_average_trend(self):
        changes = self.make_bad_trend()
        b1 = self.make_bench('b1')
        for x in changes:
            s1 = self.make_result(x)
            if x != changes[-1]:
                self.make_result(x, rev=s1, benchmark=b1)
        self.make_result(changes[-2] * .92, rev=s1, benchmark=b1)
        rep = self.make_report(s1)
        self.assertEquals('green', rep.colorcode)
        self.assertIn('Average', rep.summary)

    def test_good_change_beats_good_trend(self):
        changes = self.make_good_trend()
        b1 = self.make_bench('b1')
        for x in changes:
            s1 = self.make_result(x)
            if x != changes[-1]:
                self.make_result(x, rev=s1, benchmark=b1)
        self.make_result(changes[-2] * .95, rev=s1, benchmark=b1)
        rep = self.make_report(s1)
        self.assertIn('b1', rep.summary)
        self.assertNotIn('trend', rep.summary)

    def test_bad_trend_beats_good_trend(self):
        good_changes = self.make_good_trend()
        bad_changes = self.make_bad_trend()

        b1 = self.make_bench('b1')
        for i in range(len(good_changes)):
            s1 = self.make_result(good_changes[i])
            self.make_result(bad_changes[i], rev=s1, benchmark=b1)

        rep = self.make_report(s1)
        self.assertIn('trend', rep.summary)
        self.assertIn('b1', rep.summary)
        self.assertIn('yellow', rep.colorcode)

    def test_bad_change_beats_good_trend(self):
        changes = self.make_good_trend()
        b1 = self.make_bench('b1')
        for x in changes:
            s1 = self.make_result(x)
            if x != changes[-1]:
                self.make_result(x, rev=s1, benchmark=b1)
        self.make_result(changes[-2] * 1.05, rev=s1, benchmark=b1)
        rep = self.make_report(s1)
        self.assertIn('b1', rep.summary)
        self.assertNotIn('trend', rep.summary)
        self.assertEquals('red', rep.colorcode)

    def test_bad_beats_good_change(self):
        b1 = self.make_bench('b1')

        s1 = self.make_result(12)
        self.make_result(12, rev=s1, benchmark=b1)

        s2 = self.make_result(15)
        self.make_result(9, rev=s2, benchmark=b1)

        rep = self.make_report(s2)
        self.assertEqual(rep.colorcode, 'red')

    def test_bigger_bad_beats_smaller_bad(self):
        b1 = self.make_bench('b1')
        b2 = self.make_bench('b2')

        s1 = self.make_result(1.0)
        self.make_result(1.0, rev=s1, benchmark=b1)
        self.make_result(1.0, rev=s1, benchmark=b2)

        s2 = self.make_result(1.0)
        self.make_result(1.04, rev=s2, benchmark=b1)
        self.make_result(1.03, rev=s2, benchmark=b2)

        rep = self.make_report(s2)
        self.assertIn('b1', rep.summary)
        self.assertEquals('red', rep.colorcode)

    def test_multiple_quantities(self):
        b1 = self.make_bench('b1', quantity='Space', units='bytes')
        s1 = self.make_result(1.0)
        self.make_result(1.0, rev=s1, benchmark=b1)

        s2 = self.make_result(1.4)
        self.make_result(1.5, rev=s2, benchmark=b1)

        rep = self.make_report(s2)
        self.assertRegexpMatches(rep.summary, '[sS]pace')
        self.assertEquals('red', rep.colorcode)

    def make_result(self, value, rev=None, benchmark=None):
        from uuid import uuid4

        if not benchmark:
            benchmark = self.bench

        if not rev:
            commitdate = self.starttime + timedelta(days=self.days)
            cid = str(uuid4())
            Revision(commitid=cid, date=commitdate, branch=self.b,
                     project=self.pro).save()
            rev = Revision.objects.get(commitid=cid)

        Result(value=value, revision=rev, executable=self.exe,
               environment=self.env, benchmark=benchmark).save()
        self.days += 1
        return rev

    def make_report(self, revision):
        Report(revision=revision, environment=self.env,
               executable=self.exe).save()
        return Report.objects.get(revision=revision)

    def make_bench(self, name, quantity='Time', units='seconds'):
        Benchmark(name=name, units_title=quantity, units=units).save()
        return Benchmark.objects.get(name=name)

    def make_bad_trend(self):
        return self.make_trend(1)

    def make_good_trend(self):
        return self.make_trend(-1)

    def make_trend(self, direction):
        return [1 + direction * x * 1.25 *
                settings.TREND_THRESHOLD / 100 / settings.TREND
                for x in range(settings.TREND)]


class TestProject(TestCase):

    def setUp(self):
        self.github_project = Project(
            name='Some Project',
            repo_type='H',
            repo_path='https://github.com/tobami/codespeed.git'
        )
        self.git_project = Project(
            repo_type='G',
            repo_path='/home/foo/codespeed'
        )

    def test_str(self):
        self.assertEqual(str(self.github_project), 'Some Project')

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
