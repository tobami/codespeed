# -*- coding: utf-8 -*-
from django.db import models

class Revision(models.Model):
    def __unicode__(self):
        return str(self.number)
    number = models.IntegerField()
    project = models.CharField(max_length=50)
    tag = models.CharField(max_length=50, blank=True)
    message = models.CharField(max_length=200, blank=True)
    date = models.DateTimeField(blank=True, null=True)
    class Meta:
        unique_together = ("number", "project")

class Interpreter(models.Model):
    def __unicode__(self):
        return str(self.name + " " + str(self.coptions))
    name = models.CharField(max_length=50)
    coptions = models.CharField("compile options", max_length=100)
    
    class Meta:
        unique_together = ("name", "coptions")


class Benchmark(models.Model):
    TYPES = (
        ('T', 'Trunk'),
        ('D', 'Debug'),
        ('P', 'Python'),
        ('M', 'Multilanguage'),
    )
    def __unicode__(self):
        return str(self.name)
    name = models.CharField(unique=True, max_length=50)
    benchmark_type = models.CharField(max_length=1, choices=TYPES, default='T')
    description = models.CharField(max_length=200, blank=True)


class Environment(models.Model):
    def __unicode__(self):
        return str(self.name)
    name = models.CharField(unique=True,max_length=50)
    cpu = models.CharField(max_length=20)
    memory = models.CharField(max_length=20)
    os = models.CharField(max_length=20)


class Result(models.Model):
    TYPES = (
        ('T', 'Time'),
        ('M', 'Memory'),
        ('S', 'Score'),
    )
    value = models.FloatField(blank=True, null=True)
    date = models.DateTimeField(blank=True, null=True)
    result_type = models.CharField(max_length=1, choices=TYPES, default='T')
    revision = models.ForeignKey(Revision)
    interpreter = models.ForeignKey(Interpreter)
    benchmark = models.ForeignKey(Benchmark)
    environment = models.ForeignKey(Environment)
    
    class Meta:
        unique_together = ("revision", "interpreter", "benchmark", "environment" , "result_type")
    