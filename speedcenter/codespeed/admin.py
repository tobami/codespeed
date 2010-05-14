# -*- coding: utf-8 -*-
from codespeed.models import Project, Revision, Executable, Benchmark, Result, Environment
from django.contrib import admin

class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'repo_type', 'repo_path', 'track')
    
admin.site.register(Project, ProjectAdmin)

class RevisionAdmin(admin.ModelAdmin):
    list_display = ('commitid', 'project', 'tag', 'date')
    list_filter  = ('project', 'tag', 'date')
    
admin.site.register(Revision, RevisionAdmin)

class ExecutableAdmin(admin.ModelAdmin):
    list_display = ('name', 'coptions', 'id')

admin.site.register(Executable, ExecutableAdmin)

class BenchmarkAdmin(admin.ModelAdmin):
    list_display = ('name', 'benchmark_type', 'description', 'units', 'lessisbetter')

admin.site.register(Benchmark, BenchmarkAdmin)

class EnvironmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'cpu', 'memory', 'os', 'kernel')

admin.site.register(Environment, EnvironmentAdmin)

class ResultAdmin(admin.ModelAdmin):
    list_display = ('revision', 'benchmark', 'executable', 'environment', 'value', 'date')
    list_filter  = ('date', 'executable', 'benchmark')

admin.site.register(Result, ResultAdmin)
