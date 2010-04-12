# -*- coding: utf-8 -*-
from django.db import models

class Project(models.Model):
    REPOSITORY_TYPES = (
        ('N', 'none'),
        ('G', 'git'),
        ('S', 'svn'),
    )
    def __unicode__(self):
        return str(self.name)
    name = models.CharField(unique=True, max_length=20)
    repository_type = models.CharField(max_length=1, choices=REPOSITORY_TYPES, default='N')
    repository_path = models.CharField(blank=True, null=True, max_length=40)
    isdefault = models.BooleanField(default=False)


class Revision(models.Model):
    def __unicode__(self):
        return str(self.date) + " - " + self.commitid
    commitid = models.CharField(max_length=40)#git's SHA-1 length is 40
    project = models.ForeignKey(Project)
    branch = models.CharField(max_length=20, default='trunk')
    tag = models.CharField(max_length=20, blank=True)
    date = models.DateTimeField(null=True)
    message = models.TextField(blank=True)
    author = models.CharField(max_length=20, blank=True)
    
    class Meta:
        unique_together = ("commitid", "branch", "project")


class Executable(models.Model):
    def __unicode__(self):
        return str(self.name + " " + str(self.coptions))
    name = models.CharField(max_length=50)
    coptions = models.CharField("compile options", max_length=100)
    project = models.ForeignKey(Project)
    
    class Meta:
        unique_together = ("name", "coptions")


class Benchmark(models.Model):
    B_TYPES = (
        ('C', 'Cross-project'),
        ('O', 'Own-project'),
    )
    def __unicode__(self):
        return str(self.name)
    name = models.CharField(unique=True, max_length=50)
    benchmark_type = models.CharField(max_length=1, choices=B_TYPES, default='C')
    description = models.CharField(max_length=200, blank=True)
    units = models.CharField(max_length=10, default='seconds')
    lessisbetter = models.BooleanField(default=True)


class Environment(models.Model):
    def __unicode__(self):
        return str(self.name)
    name = models.CharField(unique=True,max_length=50)
    cpu = models.CharField(max_length=20, blank=True)
    memory = models.CharField(max_length=20, blank=True)
    os = models.CharField(max_length=20, blank=True)
    kernel = models.CharField(max_length=20, blank=True)


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
    
    class Meta:
        unique_together = ("revision", "executable", "benchmark", "environment")
