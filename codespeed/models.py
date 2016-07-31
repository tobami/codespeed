# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import os
import json

from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.conf import settings
from django.db import models
from django.utils.encoding import python_2_unicode_compatible

from .commits.github import GITHUB_URL_RE


@python_2_unicode_compatible
class Project(models.Model):
    NO_LOGS = 'N'
    GIT = 'G'
    GITHUB = 'H'
    MERCURIAL = 'M'
    SUBVERSION = 'S'
    REPO_TYPES = (
        (NO_LOGS, 'none'),
        (GIT, 'git'),
        (GITHUB, 'Github.com'),
        (MERCURIAL, 'mercurial'),
        (SUBVERSION, 'subversion'),
    )

    name = models.CharField(unique=True, max_length=30)
    repo_type = models.CharField(
        "Repository type", max_length=1, choices=REPO_TYPES, default=NO_LOGS)
    repo_path = models.CharField("Repository URL", blank=True, max_length=200)
    repo_user = models.CharField("Repository username",
                                 blank=True, max_length=100)
    repo_pass = models.CharField("Repository password",
                                 blank=True, max_length=100)
    commit_browsing_url = models.CharField("Commit browsing URL",
                                           blank=True, max_length=200)
    track = models.BooleanField("Track changes", default=True)

    def __str__(self):
        return self.name

    @property
    def repo_name(self):
        # name not defined for None, GitHub or Subversion
        if self.repo_type in ('N', 'H', 'S'):
            error = 'Not supported for %s project' % self.get_repo_type_display()
            raise AttributeError(error)

        return os.path.splitext(self.repo_path.split(os.sep)[-1])[0]

    @property
    def working_copy(self):
        # working copy exists for mercurial and git only
        if self.repo_type in ('N', 'H', 'S'):
            error = 'Not supported for %s project' % self.get_repo_type_display()
            raise AttributeError(error)

        return os.path.join(settings.REPOSITORY_BASE_PATH, self.repo_name)

    def save(self, *args, **kwargs):
        """Provide a default for commit browsing url in github repositories."""
        if not self.commit_browsing_url and self.repo_type == self.GITHUB:
            m = GITHUB_URL_RE.match(self.repo_path)
            if m:
                url = 'https://github.com/%s/%s/commit/{commitid}' % (
                    m.group('username'), m.group('project')
                )
                self.commit_browsing_url = url
        super(Project, self).save(*args, **kwargs)


@python_2_unicode_compatible
class Branch(models.Model):
    name = models.CharField(max_length=20)
    project = models.ForeignKey(Project, related_name="branches")

    def __str__(self):
        return self.project.name + ":" + self.name

    class Meta:
        unique_together = ("name", "project")
        verbose_name_plural = "branches"


@python_2_unicode_compatible
class Revision(models.Model):
    # git and mercurial's SHA-1 length is 40
    commitid = models.CharField(max_length=42)
    tag = models.CharField(max_length=20, blank=True)
    date = models.DateTimeField(null=True)
    message = models.TextField(blank=True)
    project = models.ForeignKey(Project, related_name="revisions",
                                null=True, blank=True)
    author = models.CharField(max_length=100, blank=True)
    branch = models.ForeignKey(Branch, related_name="revisions")

    def get_short_commitid(self):
        return self.commitid[:10]

    def get_browsing_url(self):
        return self.branch.project.commit_browsing_url.format(**self.__dict__)

    def __str__(self):
        if self.date is None:
            date = None
        else:
            date = self.date.strftime("%b %d, %H:%M")
        string = " - ".join(filter(None, (date, self.commitid, self.tag)))
        if self.branch.name != settings.DEF_BRANCH:
            string += " - " + self.branch.name
        return string

    class Meta:
        unique_together = ("commitid", "branch")

    def clean(self):
        if not self.commitid or self.commitid == "None":
            raise ValidationError("Invalid commit id %s" % self.commitid)
        if self.branch.project.repo_type == "S":
            try:
                long(self.commitid)
            except ValueError:
                raise ValidationError("Invalid SVN commit id %s" % self.commitid)


@python_2_unicode_compatible
class Executable(models.Model):
    name = models.CharField(max_length=30)
    description = models.CharField(max_length=200, blank=True)
    project = models.ForeignKey(Project, related_name="executables")

    class Meta:
        unique_together = ('name', 'project')

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class Benchmark(models.Model):
    B_TYPES = (
        ('C', 'Cross-project'),
        ('O', 'Own-project'),
    )
    D_TYPES = (
        ('U', 'Mean'),
        ('M', 'Median'),
    )

    name = models.CharField(unique=True, max_length=100)
    parent = models.ForeignKey(
        'self', verbose_name="parent",
        help_text="allows to group benchmarks in hierarchies",
        null=True, blank=True, default=None)
    benchmark_type = models.CharField(max_length=1, choices=B_TYPES, default='C')
    data_type = models.CharField(max_length=1, choices=D_TYPES, default='U')
    description = models.CharField(max_length=300, blank=True)
    units_title = models.CharField(max_length=30, default='Time')
    units = models.CharField(max_length=20, default='seconds')
    lessisbetter = models.BooleanField("Less is better", default=True)
    default_on_comparison = models.BooleanField(
        "Default on comparison page", default=True)

    def __str__(self):
        return self.name

    def clean(self):
        if self.default_on_comparison and self.benchmark_type != 'C':
            raise ValidationError("Only cross-project benchmarks are shown "
                                  "on the comparison page. Deactivate "
                                  "'default_on_comparison' first.")


@python_2_unicode_compatible
class Environment(models.Model):
    name = models.CharField(unique=True, max_length=100)
    cpu = models.CharField(max_length=100, blank=True)
    memory = models.CharField(max_length=100, blank=True)
    os = models.CharField(max_length=100, blank=True)
    kernel = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class Result(models.Model):
    value = models.FloatField()
    std_dev = models.FloatField(blank=True, null=True)
    val_min = models.FloatField(blank=True, null=True)
    val_max = models.FloatField(blank=True, null=True)
    q1 = models.FloatField(blank=True, null=True)
    q3 = models.FloatField(blank=True, null=True)
    date = models.DateTimeField(blank=True, null=True)
    revision = models.ForeignKey(Revision, related_name="results")
    executable = models.ForeignKey(Executable, related_name="results")
    benchmark = models.ForeignKey(Benchmark, related_name="results")
    environment = models.ForeignKey(Environment, related_name="results")

    def __str__(self):
        return u"%s: %s" % (self.benchmark.name, self.value)

    class Meta:
        unique_together = ("revision", "executable", "benchmark", "environment")


@python_2_unicode_compatible
class Report(models.Model):
    revision = models.ForeignKey(Revision, related_name="reports")
    environment = models.ForeignKey(Environment, related_name="reports")
    executable = models.ForeignKey(Executable, related_name="reports")
    summary = models.CharField(max_length=64, blank=True)
    colorcode = models.CharField(max_length=10, default="none")
    _tablecache = models.TextField(blank=True)

    def __str__(self):
        return u"Report for %s" % self.revision

    class Meta:
        unique_together = ("revision", "executable", "environment")

    def save(self, *args, **kwargs):
        tablelist = self.get_changes_table(force_save=True)
        max_change, max_change_ben, max_change_color = 0, None, "none"
        max_trend, max_trend_ben, max_trend_color = 0, None, "none"
        average_change, average_change_units, average_change_color = 0, None, "none"
        average_trend, average_trend_units, average_trend_color = 0, None, "none"

        # Get default threshold values
        change_threshold = 3.0
        trend_threshold = 5.0
        if (hasattr(settings, 'CHANGE_THRESHOLD') and
                settings.CHANGE_THRESHOLD is not None):
            change_threshold = settings.CHANGE_THRESHOLD
        if hasattr(settings, 'TREND_THRESHOLD') and settings.TREND_THRESHOLD:
            trend_threshold = settings.TREND_THRESHOLD

        # Fetch big changes for each unit type and each benchmark
        for units in tablelist:
            # Total change
            val = units['totals']['change']
            if val == "-":
                continue
            color = self.getcolorcode(val, units['lessisbetter'],
                                      change_threshold)
            if self.is_big_change(val, color, average_change, average_change_color):
                # Do update biggest total change
                average_change = val
                average_change_units = units['units_title']
                average_change_color = color
            # Total trend
            val = units['totals']['trend']
            if val != "-":
                color = self.getcolorcode(val, units['lessisbetter'],
                                          trend_threshold)
                if self.is_big_change(val, color, average_trend, average_trend_color):
                    # Do update biggest total trend change
                    average_trend = val
                    average_trend_units = units['units_title']
                    average_trend_color = color
            for row in units['rows']:
                # Single change
                val = row['change']
                if val == "-":
                    continue
                color = self.getcolorcode(val, units['lessisbetter'],
                                          change_threshold)
                if self.is_big_change(val, color, max_change, max_change_color):
                    # Do update biggest single change
                    max_change = val
                    max_change_ben = row['bench_name']
                    max_change_color = color
                # Single trend
                val = row['trend']
                if val == "-":
                    continue
                color = self.getcolorcode(val, units['lessisbetter'], trend_threshold)
                if self.is_big_change(val, color, max_trend, max_trend_color):
                    # Do update biggest single trend change
                    max_trend = val
                    max_trend_ben = row['bench_name']
                    max_trend_color = color
        # Reinitialize
        self.summary = ""
        self.colorcode = "none"

        # Save summary in order of priority
        # (changes results before trends, averages before individual results)

        # Average change
        if average_change_color != "none":
            self.summary = "Average %s %s" % (
                average_change_units.lower(),
                self.updown(average_change))
            self.colorcode = average_change_color

        # Single benchmark change
        elif max_change_color != "none":
            self.summary = "%s %s" % (
                max_change_ben,
                self.updown(max_change))
            self.colorcode = max_change_color

        # Average trend
        elif average_trend_color != "none":
            self.summary = "Average %s trend %s" % (
                average_trend_units.lower(),
                self.updown(average_trend))
            # use lighter colors for trend results:
            if average_trend_color == "red":
                self.colorcode = "yellow"
            elif average_trend_color == "green":
                self.colorcode = "lightgreen"

        # Single benchmark trend
        elif max_trend_color != "none":
            self.summary = "%s trend %s" % (
                max_trend_ben,
                self.updown(max_trend))
            # use lighter colors for trend results:
            if max_trend_color == "red":
                self.colorcode = "yellow"
            elif max_trend_color == "green":
                self.colorcode = "lightgreen"

        super(Report, self).save(*args, **kwargs)

    def updown(self, val):
        """Substitutes plus/minus with up/down"""
        direction = val >= 0 and "up" or "down"
        aval = abs(val)
        if aval == float("inf"):
            return u"%s ∞%%" % direction
        else:
            return "%s %.1f%%" % (direction, aval)

    def is_big_change(self, val, color, current_val, current_color):
        if color == "red" and current_color != "red":
            return True
        elif color == "red" and abs(val) > abs(current_val):
            return True
        elif (color == "green" and current_color != "red" and
                abs(val) > abs(current_val)):
            return True
        else:
            return False

    def getcolorcode(self, val, lessisbetter, threshold):
        if lessisbetter:
            val = -val
        if val < -threshold:
            return "red"
        elif val > threshold:
            return "green"
        else:
            return "none"

    def get_changes_table(self, trend_depth=10, force_save=False):
        # Determine whether required trend value is the default one
        default_trend = 10
        if hasattr(settings, 'TREND') and settings.TREND:
            default_trend = settings.TREND
        # If the trend is the default and a forced save is not required
        # just return the cached changes table
        if not force_save and trend_depth == default_trend:
            return self._get_tablecache()
        # Otherwise generate a new changes table
        # Get latest revisions for this branch (which also sets the project)
        try:
            lastrevisions = Revision.objects.filter(
                branch=self.revision.branch
            ).filter(
                date__lte=self.revision.date
            ).order_by('-date')[:trend_depth + 1]
            # Same as self.revision unless in a different branch
            lastrevision = lastrevisions[0]
        except:
            return []
        change_list = []
        pastrevisions = []
        if len(lastrevisions) > 1:
            changerevision = lastrevisions[1]
            change_list = Result.objects.filter(
                revision=changerevision
            ).filter(
                environment=self.environment
            ).filter(
                executable=self.executable
            )
            pastrevisions = lastrevisions[trend_depth - 2:trend_depth + 1]

        result_list = Result.objects.filter(
            revision=lastrevision
        ).filter(
            environment=self.environment
        ).filter(
            executable=self.executable
        )

        tablelist = []
        for units_title in Benchmark.objects.all().values_list(
                'units_title', flat=True).distinct():
            currentlist = []
            units = ""
            hasmin = False
            hasmax = False
            has_stddev = False
            smallest = 1000
            totals = {'change': [], 'trend': []}
            for bench in Benchmark.objects.filter(units_title=units_title):
                units = bench.units
                lessisbetter = bench.lessisbetter
                resultquery = result_list.filter(benchmark=bench)
                if not len(resultquery):
                    continue

                resobj = resultquery.filter(benchmark=bench)[0]

                std_dev = resobj.std_dev
                if std_dev is not None:
                    has_stddev = True
                else:
                    std_dev = "-"

                val_min = resobj.val_min
                if val_min is not None:
                    hasmin = True
                else:
                    val_min = "-"

                val_max = resobj.val_max
                if val_max is not None:
                    hasmax = True
                else:
                    val_max = "-"

                # Calculate percentage change relative to previous result
                result = resobj.value
                change = "-"
                if len(change_list):
                    c = change_list.filter(benchmark=bench)
                    if c.count() and result is not None:
                        if c[0].value != 0:
                            change = (result - c[0].value) * 100 / c[0].value
                            totals['change'].append(result / c[0].value)
                        elif c[0].value == 0:
                            if result == 0:
                                # 0/0 = 1, in our world
                                change = 0
                                totals['change'].append(1)
                            else:
                                # n/0 = ∞
                                change = float("inf")
                                totals['change'].append(float("inf"))
                        else:
                            # no previous result, no change available
                            pass

                # Calculate trend:
                # percentage change relative to average of 3 previous results
                # Calculate past average
                average = 0
                averagecount = 0
                if len(pastrevisions):
                    for rev in pastrevisions:
                        past_rev = Result.objects.filter(
                            revision=rev
                        ).filter(
                            environment=self.environment
                        ).filter(
                            executable=self.executable
                        ).filter(benchmark=bench)
                        if past_rev.count():
                            average += past_rev[0].value
                            averagecount += 1
                trend = "-"
                if average:
                    average = average / averagecount
                    trend = (result - average) * 100 / average
                    totals['trend'].append(result / average)

                # Retain lowest number different than 0
                # to be used later for calculating significant digits
                if result < smallest and result:
                    smallest = result

                currentlist.append({
                    'bench_name': bench.name,
                    'bench_description': bench.description,
                    'result': result,
                    'std_dev': std_dev,
                    'val_min': val_min,
                    'val_max': val_max,
                    'change': change,
                    'trend': trend
                })

            # Compute Arithmetic averages
            for key in totals.keys():
                if len(totals[key]):
                    totals[key] = float(sum(totals[key]) / len(totals[key]))
                else:
                    totals[key] = "-"

            if totals['change'] != "-":
                # Transform ratio to percentage
                totals['change'] = (totals['change'] - 1) * 100
            if totals['trend'] != "-":
                # Transform ratio to percentage
                totals['trend'] = (totals['trend'] - 1) * 100

            # Calculate significant digits
            digits = 2
            while smallest < 1:
                smallest *= 10
                digits += 1

            tablelist.append({
                'units': units,
                'units_title': units_title,
                'lessisbetter': lessisbetter,
                'has_stddev': has_stddev,
                'hasmin': hasmin,
                'hasmax': hasmax,
                'precission': digits,
                'totals': totals,
                'rows': currentlist
            })
        if force_save:
            self._save_tablecache(tablelist)
        return tablelist

    def get_absolute_url(self):
        return reverse("changes") + "?rev=%s&exe=%s&env=%s" % (
            self.revision.commitid, self.executable.id, self.environment.name)

    def item_description(self):
        if self.summary == "":
            return "no significant changes"
        else:
            return self.summary

    def _save_tablecache(self, data):
        self._tablecache = json.dumps(data)

    def _get_tablecache(self):
        if self._tablecache == '':
            return {}
        return json.loads(self._tablecache)
