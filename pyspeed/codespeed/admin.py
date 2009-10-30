# -*- coding: utf-8 -*-
from pyspeed.codespeed.models import Revision, Interpreter, Benchmark, Result, Environment
from django.contrib import admin

class RevisionAdmin(admin.ModelAdmin):
    list_display = ('number', 'project', 'tag')
    
admin.site.register(Revision, RevisionAdmin)

class InterpreterAdmin(admin.ModelAdmin):
    list_display = ('name', 'coptions')

admin.site.register(Interpreter, InterpreterAdmin)

class BenchmarkAdmin(admin.ModelAdmin):
    list_display = ('name', 'benchmark_type', 'description')

admin.site.register(Benchmark, BenchmarkAdmin)

class EnvironmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'cpu', 'memory', 'os')

admin.site.register(Environment, EnvironmentAdmin)

class ResultAdmin(admin.ModelAdmin):
            list_display = ('key', 'value', 'result_type', 'revision', 'interpreter', 'benchmark', 'date')

admin.site.register(Result, ResultAdmin)
