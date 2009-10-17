# -*- coding: utf-8 -*-
from pyspeed.codespeed.models import Interpreter, Benchmark, Result, Environment
from django.contrib import admin

class InterpreterAdmin(admin.ModelAdmin):
    list_display = ('name', 'revision', 'tag', 'coptions')

admin.site.register(Interpreter, InterpreterAdmin)

class BenchmarkAdmin(admin.ModelAdmin):
    list_display = ('name', 'multi', 'description')

admin.site.register(Benchmark, BenchmarkAdmin)

class EnvironmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'cpu', 'memory', 'os')

admin.site.register(Environment, EnvironmentAdmin)

class ResultAdmin(admin.ModelAdmin):
    list_display = ('key', 'value', 'result_type', 'interpreter', 'benchmark', 'date')

admin.site.register(Result, ResultAdmin)
