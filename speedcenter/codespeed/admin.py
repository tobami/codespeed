# -*- coding: utf-8 -*-
from codespeed.models import Revision, Interpreter, Benchmark, Result, Environment
from django.contrib import admin

class RevisionAdmin(admin.ModelAdmin):
    list_display = ('number', 'project', 'branch', 'tag', 'date')
    list_filter  = ('project', 'tag')
    
admin.site.register(Revision, RevisionAdmin)

class InterpreterAdmin(admin.ModelAdmin):
    list_display = ('name', 'coptions', 'id')

admin.site.register(Interpreter, InterpreterAdmin)

class BenchmarkAdmin(admin.ModelAdmin):
    list_display = ('name', 'benchmark_type', 'description', 'units', 'lessisbetter')

admin.site.register(Benchmark, BenchmarkAdmin)

class EnvironmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'cpu', 'memory', 'os', 'kernel')

admin.site.register(Environment, EnvironmentAdmin)

class ResultAdmin(admin.ModelAdmin):
    list_display = ('revision', 'benchmark', 'value', 'interpreter', 'date')
    list_filter  = ('date', 'interpreter', 'benchmark')

admin.site.register(Result, ResultAdmin)
