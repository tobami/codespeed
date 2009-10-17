# -*- coding: utf-8 -*-
from django.db import models

class Interpreter(models.Model):
    def __unicode__(self):
        return str(self.name + " rev" + str(self.revision))
    name = models.CharField(max_length=50)
    revision = models.IntegerField()
    tag = models.CharField(max_length=50, blank=True)
    coptions = models.CharField("compile options", max_length=100, blank=True)
    class Meta:
        unique_together = (("name", "revision", "coptions"),)


class Benchmark(models.Model):
    def __unicode__(self):
        return str(self.name)
    name = models.CharField(unique=True, max_length=50)
    multi = models.BooleanField("is multilanguage", default=False)
    description = models.CharField(max_length=200, blank=True)


class Environment(models.Model):
    def __unicode__(self):
        return str(self.name)
    name = models.CharField(max_length=50)
    cpu = models.CharField(max_length=20)
    memory = models.CharField(max_length=20)
    os = models.CharField(max_length=20)


class Result(models.Model):
    TYPES = (
        ('T', 'Time'),
        ('M', 'Memory'),
        ('S', 'Score'),
    )
    key = models.CharField('test', max_length=20)
    value = models.FloatField()
    date = models.DateTimeField()
    result_type = models.CharField(max_length=1, choices=TYPES, default='T')
    interpreter = models.ForeignKey(Interpreter)
    benchmark = models.ForeignKey(Benchmark)
    environment = models.ForeignKey(Environment)
