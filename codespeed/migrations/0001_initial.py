# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Benchmark',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=100)),
                ('benchmark_type', models.CharField(default='C', max_length=1, choices=[('C', 'Cross-project'), ('O', 'Own-project')])),
                ('description', models.CharField(max_length=300, blank=True)),
                ('units_title', models.CharField(default='Time', max_length=30)),
                ('units', models.CharField(default='seconds', max_length=20)),
                ('lessisbetter', models.BooleanField(default=True, verbose_name='Less is better')),
                ('default_on_comparison', models.BooleanField(default=True, verbose_name='Default on comparison page')),
                ('parent', models.ForeignKey(default=None, to='codespeed.Benchmark', blank=True, help_text='allows to group benchmarks in hierarchies', null=True, verbose_name='parent')),
            ],
        ),
        migrations.CreateModel(
            name='Branch',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=20)),
            ],
            options={
                'verbose_name_plural': 'branches',
            },
        ),
        migrations.CreateModel(
            name='Environment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=100)),
                ('cpu', models.CharField(max_length=100, blank=True)),
                ('memory', models.CharField(max_length=100, blank=True)),
                ('os', models.CharField(max_length=100, blank=True)),
                ('kernel', models.CharField(max_length=100, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Executable',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=30)),
                ('description', models.CharField(max_length=200, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=30)),
                ('repo_type', models.CharField(default='N', max_length=1, verbose_name='Repository type', choices=[('N', 'none'), ('G', 'git'), ('H', 'Github.com'), ('M', 'mercurial'), ('S', 'subversion')])),
                ('repo_path', models.CharField(max_length=200, verbose_name='Repository URL', blank=True)),
                ('repo_user', models.CharField(max_length=100, verbose_name='Repository username', blank=True)),
                ('repo_pass', models.CharField(max_length=100, verbose_name='Repository password', blank=True)),
                ('commit_browsing_url', models.CharField(max_length=200, verbose_name='Commit browsing URL', blank=True)),
                ('track', models.BooleanField(default=True, verbose_name='Track changes')),
            ],
        ),
        migrations.CreateModel(
            name='Report',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('summary', models.CharField(max_length=64, blank=True)),
                ('colorcode', models.CharField(default='none', max_length=10)),
                ('_tablecache', models.TextField(blank=True)),
                ('environment', models.ForeignKey(related_name='reports', to='codespeed.Environment')),
                ('executable', models.ForeignKey(related_name='reports', to='codespeed.Executable')),
            ],
        ),
        migrations.CreateModel(
            name='Result',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('value', models.FloatField()),
                ('std_dev', models.FloatField(null=True, blank=True)),
                ('val_min', models.FloatField(null=True, blank=True)),
                ('val_max', models.FloatField(null=True, blank=True)),
                ('date', models.DateTimeField(null=True, blank=True)),
                ('benchmark', models.ForeignKey(related_name='results', to='codespeed.Benchmark')),
                ('environment', models.ForeignKey(related_name='results', to='codespeed.Environment')),
                ('executable', models.ForeignKey(related_name='results', to='codespeed.Executable')),
            ],
        ),
        migrations.CreateModel(
            name='Revision',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('commitid', models.CharField(max_length=42)),
                ('tag', models.CharField(max_length=20, blank=True)),
                ('date', models.DateTimeField(null=True)),
                ('message', models.TextField(blank=True)),
                ('author', models.CharField(max_length=100, blank=True)),
                ('branch', models.ForeignKey(related_name='revisions', to='codespeed.Branch')),
                ('project', models.ForeignKey(related_name='revisions', blank=True, to='codespeed.Project', null=True)),
            ],
        ),
        migrations.AddField(
            model_name='result',
            name='revision',
            field=models.ForeignKey(related_name='results', to='codespeed.Revision'),
        ),
        migrations.AddField(
            model_name='report',
            name='revision',
            field=models.ForeignKey(related_name='reports', to='codespeed.Revision'),
        ),
        migrations.AddField(
            model_name='executable',
            name='project',
            field=models.ForeignKey(related_name='executables', to='codespeed.Project'),
        ),
        migrations.AddField(
            model_name='branch',
            name='project',
            field=models.ForeignKey(related_name='branches', to='codespeed.Project'),
        ),
        migrations.AlterUniqueTogether(
            name='revision',
            unique_together=set([('commitid', 'branch')]),
        ),
        migrations.AlterUniqueTogether(
            name='result',
            unique_together=set([('revision', 'executable', 'benchmark', 'environment')]),
        ),
        migrations.AlterUniqueTogether(
            name='report',
            unique_together=set([('revision', 'executable', 'environment')]),
        ),
        migrations.AlterUniqueTogether(
            name='executable',
            unique_together=set([('name', 'project')]),
        ),
        migrations.AlterUniqueTogether(
            name='branch',
            unique_together=set([('name', 'project')]),
        ),
    ]
