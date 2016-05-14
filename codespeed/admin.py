# -*- coding: utf-8 -*-

from codespeed.models import (Project, Revision, Executable, Benchmark, Branch,
                              Result, Environment, Report)

from django.contrib import admin


class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'repo_type', 'repo_path', 'track')

admin.site.register(Project, ProjectAdmin)


class BranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'project')
    list_filter = ('project',)

admin.site.register(Branch, BranchAdmin)


class RevisionAdmin(admin.ModelAdmin):
    list_display = ('commitid', 'branch', 'tag', 'date')
    list_filter = ('branch__project', 'branch', 'tag', 'date')
    search_fields = ('commitid', 'tag')

admin.site.register(Revision, RevisionAdmin)


class ExecutableAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'id', 'project')
    list_filter = ('project',)
    ordering = ['name']
    search_fields = ('name', 'description', 'project__name')

admin.site.register(Executable, ExecutableAdmin)


class BenchmarkAdmin(admin.ModelAdmin):
    list_display = ('name', 'benchmark_type', 'data_type', 'description',
                    'units_title', 'units', 'lessisbetter',
                    'default_on_comparison')
    list_filter = ('data_type','lessisbetter')
    ordering = ['name']
    search_fields = ('name', 'description')

admin.site.register(Benchmark, BenchmarkAdmin)


class EnvironmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'cpu', 'memory', 'os', 'kernel')
    ordering = ['name']
    search_fields = ('name', 'cpu', 'memory', 'os', 'kernel')

admin.site.register(Environment, EnvironmentAdmin)


class ResultAdmin(admin.ModelAdmin):
    list_display = ('revision', 'benchmark', 'executable', 'environment',
                    'value', 'date')
    list_filter = ('environment', 'executable', 'date', 'benchmark')

admin.site.register(Result, ResultAdmin)


def recalculate_report(modeladmin, request, queryset):
    for report in queryset:
        report.save()
recalculate_report.short_description = "Recalculate reports"


class ReportAdmin(admin.ModelAdmin):
    list_display = ('revision', 'summary', 'colorcode')
    list_filter = ('environment', 'executable')
    ordering = ['-revision']
    actions = [recalculate_report]

admin.site.register(Report, ReportAdmin)
