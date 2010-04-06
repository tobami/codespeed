# -*- coding: utf-8 -*-
from codespeed.models import Project, Revision, Commitlog, Executable, Benchmark, Result, Environment
from django.contrib import admin

class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'rcType', 'rcURL', 'isdefault')
    
admin.site.register(Project, ProjectAdmin)

class CommitlogAdmin(admin.ModelAdmin):
    list_display = ('revision', 'commitid', 'author', 'date', 'message')
    list_filter  = ('revision', 'author')
    
admin.site.register(Commitlog, CommitlogAdmin)

class RevisionAdmin(admin.ModelAdmin):
    list_display = ('commitid', 'project', 'branch', 'tag', 'date')
    list_filter  = ('project', 'tag')
    
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
    list_display = ('revision', 'benchmark', 'value', 'executable', 'date')
    list_filter  = ('date', 'executable', 'benchmark')

admin.site.register(Result, ResultAdmin)
