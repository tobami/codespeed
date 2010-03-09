# -*- coding: utf-8 -*-
from codespeed.models import Revision, Interpreter, Benchmark, Result, Environment
from django.contrib import admin

class RevisionAdmin(admin.ModelAdmin):
    list_display = ('number', 'project', 'tag', 'date')
    
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
            list_display = ('revision', 'benchmark', 'value', 'result_type', 'interpreter', 'date')

admin.site.register(Result, ResultAdmin)
