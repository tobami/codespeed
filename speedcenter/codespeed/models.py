# -*- coding: utf-8 -*-
from django.db import models

class Project(models.Model):
    REPO_TYPES = (
        ('N', 'none'),
        ('G', 'git'),
        ('S', 'svn'),
    )
    
    name = models.CharField(unique=True, max_length=30)
    repo_type = models.CharField("Repository type", max_length=1, choices=REPO_TYPES, default='N')
    repo_path = models.CharField("Repository URL", blank=True, max_length=200)
    repo_user = models.CharField("Repository username", blank=True, max_length=100)
    repo_pass = models.CharField("Repository password", blank=True, max_length=100)
    track = models.BooleanField("Track changes", default=False)
    
    def __unicode__(self):
        return str(self.name)


class Revision(models.Model):
    commitid = models.CharField(max_length=42)#git and mercurial's SHA-1 length is 40
    project = models.ForeignKey(Project)
    tag = models.CharField(max_length=25, blank=True)
    date = models.DateTimeField(null=True)
    message = models.TextField(blank=True)
    author = models.CharField(max_length=25, blank=True)

    def __unicode__(self):
        return self.date.strftime("%Y-%m-%d %H:%M") + " - " + self.commitid
    
    class Meta:
        unique_together = ("commitid", "project")


class Executable(models.Model):
    name = models.CharField(unique=True, max_length=30)
    description = models.CharField(max_length=200, blank=True)
    project = models.ForeignKey(Project)
    
    def __unicode__(self):
        return str(self.name)


class Benchmark(models.Model):
    B_TYPES = (
        ('C', 'Cross-project'),
        ('O', 'Own-project'),
    )
    
    name = models.CharField(unique=True, max_length=30)
    benchmark_type = models.CharField(max_length=1, choices=B_TYPES, default='C')
    description = models.CharField(max_length=200, blank=True)
    units_title = models.CharField(max_length=20, default='Time')
    units = models.CharField(max_length=10, default='seconds')
    lessisbetter = models.BooleanField(default=True)
    
    def __unicode__(self):
        return str(self.name)


class Environment(models.Model):
    name = models.CharField(unique=True,max_length=50)
    cpu = models.CharField(max_length=20, blank=True)
    memory = models.CharField(max_length=20, blank=True)
    os = models.CharField(max_length=20, blank=True)
    kernel = models.CharField(max_length=20, blank=True)
    
    def __unicode__(self):
        return str(self.name)


class Result(models.Model):
    value = models.FloatField()
    std_dev = models.FloatField(blank=True, null=True)
    val_min = models.FloatField(blank=True, null=True)
    val_max = models.FloatField(blank=True, null=True)
    date = models.DateTimeField(blank=True, null=True)
    revision = models.ForeignKey(Revision)
    executable = models.ForeignKey(Executable)
    benchmark = models.ForeignKey(Benchmark)
    environment = models.ForeignKey(Environment)
    
    def __unicode__(self):
        return str(self.benchmark.name) + " " + str(self.value)
    
    class Meta:
        unique_together = ("revision", "executable", "benchmark", "environment")
