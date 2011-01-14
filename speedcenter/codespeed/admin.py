# -*- coding: utf-8 -*-
from codespeed.models import Project, Revision, Executable, Benchmark
from codespeed.models import Result, Environment, Report
from django.contrib import admin

class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'repo_type', 'repo_path', 'track')
    
admin.site.register(Project, ProjectAdmin)

class RevisionAdmin(admin.ModelAdmin):
    list_display = ('commitid', 'project', 'tag', 'date')
    list_filter  = ('project', 'tag', 'date')
    search_fields = ['commitid']

admin.site.register(Revision, RevisionAdmin)

class ExecutableAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'id')

admin.site.register(Executable, ExecutableAdmin)

class BenchmarkAdmin(admin.ModelAdmin):
    list_display = ('name', 'benchmark_type', 'description', 'units_title', 'units', 'lessisbetter')
    ordering = ['name']

admin.site.register(Benchmark, BenchmarkAdmin)

class EnvironmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'cpu', 'memory', 'os', 'kernel')

admin.site.register(Environment, EnvironmentAdmin)

class ResultAdmin(admin.ModelAdmin):
    list_display = ('revision', 'benchmark', 'executable', 'environment', 'value', 'date', 'environment')
    list_filter  = ('date', 'executable', 'benchmark', 'environment')

admin.site.register(Result, ResultAdmin)

class ReportAdmin(admin.ModelAdmin):
    list_display = ('revision', 'summary', 'colorcode')
    ordering = ['-revision']
    
admin.site.register(Report, ReportAdmin)