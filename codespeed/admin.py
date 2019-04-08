# -*- coding: utf-8 -*-

from django import forms
from django.contrib import admin

from codespeed.models import (Project, Revision, Executable, Benchmark, Branch,
                              Result, Environment, Report)


class ProjectForm(forms.ModelForm):

    default_branch = forms.CharField(max_length=32, required=False)

    def clean(self):
        if not self.cleaned_data.get('default_branch'):
            repo_type = self.cleaned_data['repo_type']
            if repo_type in [Project.GIT, Project.GITHUB]:
                self.cleaned_data['default_branch'] = "master"
            elif repo_type == Project.MERCURIAL:
                self.cleaned_data['default_branch'] = "default"
            elif repo_type == Project.SUBVERSION:
                self.cleaned_data['default_branch'] = "trunk"
            else:
                self.add_error('default_branch', 'This field is required.')

    class Meta:
        model = Project
        fields = '__all__'


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'repo_type', 'repo_path', 'track')

    form = ProjectForm


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'project')
    list_filter = ('project',)


@admin.register(Revision)
class RevisionAdmin(admin.ModelAdmin):
    list_display = ('commitid', 'branch', 'tag', 'date')
    list_filter = ('branch__project', 'branch', 'tag', 'date')
    search_fields = ('commitid', 'tag')


@admin.register(Executable)
class ExecutableAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'id', 'project')
    list_filter = ('project',)
    ordering = ['name']
    search_fields = ('name', 'description', 'project__name')


@admin.register(Benchmark)
class BenchmarkAdmin(admin.ModelAdmin):
    list_display = ('name', 'benchmark_type', 'data_type', 'description',
                    'units_title', 'units', 'lessisbetter',
                    'default_on_comparison')
    list_filter = ('data_type', 'lessisbetter')
    ordering = ['name']
    search_fields = ('name', 'description')


@admin.register(Environment)
class EnvironmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'cpu', 'memory', 'os', 'kernel')
    ordering = ['name']
    search_fields = ('name', 'cpu', 'memory', 'os', 'kernel')


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ('revision', 'benchmark', 'executable', 'environment',
                    'value', 'date')
    list_filter = ('environment', 'executable', 'date', 'benchmark')


def recalculate_report(modeladmin, request, queryset):
    for report in queryset:
        report.save()


recalculate_report.short_description = "Recalculate reports"


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('revision', 'summary', 'colorcode')
    list_filter = ('environment', 'executable')
    ordering = ['-revision']
    actions = [recalculate_report]
