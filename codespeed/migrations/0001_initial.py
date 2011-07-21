# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):

        # Adding model 'Project'
        db.create_table('codespeed_project', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=30)),
            ('repo_type', self.gf('django.db.models.fields.CharField')(default='N', max_length=1)),
            ('repo_path', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('repo_user', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('repo_pass', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('track', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('codespeed', ['Project'])

        # Adding model 'Revision'
        db.create_table('codespeed_revision', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('commitid', self.gf('django.db.models.fields.CharField')(max_length=42)),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(related_name='revisions', to=orm['codespeed.Project'])),
            ('tag', self.gf('django.db.models.fields.CharField')(max_length=20, blank=True)),
            ('date', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('message', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('author', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
        ))
        db.send_create_signal('codespeed', ['Revision'])

        # Adding unique constraint on 'Revision', fields ['commitid', 'project']
        db.create_unique('codespeed_revision', ['commitid', 'project_id'])

        # Adding model 'Executable'
        db.create_table('codespeed_executable', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=30)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(related_name='executables', to=orm['codespeed.Project'])),
        ))
        db.send_create_signal('codespeed', ['Executable'])

        # Adding model 'Benchmark'
        db.create_table('codespeed_benchmark', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=30)),
            ('benchmark_type', self.gf('django.db.models.fields.CharField')(default='C', max_length=1)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('units_title', self.gf('django.db.models.fields.CharField')(default='Time', max_length=30)),
            ('units', self.gf('django.db.models.fields.CharField')(default='seconds', max_length=20)),
            ('lessisbetter', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('codespeed', ['Benchmark'])

        # Adding model 'Environment'
        db.create_table('codespeed_environment', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=30)),
            ('cpu', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('memory', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('os', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('kernel', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
        ))
        db.send_create_signal('codespeed', ['Environment'])

        # Adding model 'Result'
        db.create_table('codespeed_result', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('value', self.gf('django.db.models.fields.FloatField')()),
            ('std_dev', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('val_min', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('val_max', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('date', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('revision', self.gf('django.db.models.fields.related.ForeignKey')(related_name='results', to=orm['codespeed.Revision'])),
            ('executable', self.gf('django.db.models.fields.related.ForeignKey')(related_name='results', to=orm['codespeed.Executable'])),
            ('benchmark', self.gf('django.db.models.fields.related.ForeignKey')(related_name='results', to=orm['codespeed.Benchmark'])),
            ('environment', self.gf('django.db.models.fields.related.ForeignKey')(related_name='results', to=orm['codespeed.Environment'])),
        ))
        db.send_create_signal('codespeed', ['Result'])

        # Adding unique constraint on 'Result', fields ['revision', 'executable', 'benchmark', 'environment']
        db.create_unique('codespeed_result', ['revision_id', 'executable_id', 'benchmark_id', 'environment_id'])

        # Adding model 'Report'
        db.create_table('codespeed_report', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('revision', self.gf('django.db.models.fields.related.ForeignKey')(related_name='reports', to=orm['codespeed.Revision'])),
            ('environment', self.gf('django.db.models.fields.related.ForeignKey')(related_name='reports', to=orm['codespeed.Environment'])),
            ('executable', self.gf('django.db.models.fields.related.ForeignKey')(related_name='reports', to=orm['codespeed.Executable'])),
            ('summary', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('colorcode', self.gf('django.db.models.fields.CharField')(default='none', max_length=10)),
            ('_tablecache', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('codespeed', ['Report'])

        # Adding unique constraint on 'Report', fields ['revision', 'executable', 'environment']
        db.create_unique('codespeed_report', ['revision_id', 'executable_id', 'environment_id'])


    def backwards(self, orm):

        # Removing unique constraint on 'Report', fields ['revision', 'executable', 'environment']
        db.delete_unique('codespeed_report', ['revision_id', 'executable_id', 'environment_id'])

        # Removing unique constraint on 'Result', fields ['revision', 'executable', 'benchmark', 'environment']
        db.delete_unique('codespeed_result', ['revision_id', 'executable_id', 'benchmark_id', 'environment_id'])

        # Removing unique constraint on 'Revision', fields ['commitid', 'project']
        db.delete_unique('codespeed_revision', ['commitid', 'project_id'])

        # Deleting model 'Project'
        db.delete_table('codespeed_project')

        # Deleting model 'Revision'
        db.delete_table('codespeed_revision')

        # Deleting model 'Executable'
        db.delete_table('codespeed_executable')

        # Deleting model 'Benchmark'
        db.delete_table('codespeed_benchmark')

        # Deleting model 'Environment'
        db.delete_table('codespeed_environment')

        # Deleting model 'Result'
        db.delete_table('codespeed_result')

        # Deleting model 'Report'
        db.delete_table('codespeed_report')


    models = {
        'codespeed.benchmark': {
            'Meta': {'object_name': 'Benchmark'},
            'benchmark_type': ('django.db.models.fields.CharField', [], {'default': "'C'", 'max_length': '1'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lessisbetter': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'}),
            'units': ('django.db.models.fields.CharField', [], {'default': "'seconds'", 'max_length': '20'}),
            'units_title': ('django.db.models.fields.CharField', [], {'default': "'Time'", 'max_length': '30'})
        },
        'codespeed.environment': {
            'Meta': {'object_name': 'Environment'},
            'cpu': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kernel': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'memory': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'}),
            'os': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'})
        },
        'codespeed.executable': {
            'Meta': {'object_name': 'Executable'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'executables'", 'to': "orm['codespeed.Project']"})
        },
        'codespeed.project': {
            'Meta': {'object_name': 'Project'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'}),
            'repo_pass': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'repo_path': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'repo_type': ('django.db.models.fields.CharField', [], {'default': "'N'", 'max_length': '1'}),
            'repo_user': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'track': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'codespeed.report': {
            'Meta': {'unique_together': "(('revision', 'executable', 'environment'),)", 'object_name': 'Report'},
            '_tablecache': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'colorcode': ('django.db.models.fields.CharField', [], {'default': "'none'", 'max_length': '10'}),
            'environment': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'reports'", 'to': "orm['codespeed.Environment']"}),
            'executable': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'reports'", 'to': "orm['codespeed.Executable']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'revision': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'reports'", 'to': "orm['codespeed.Revision']"}),
            'summary': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'})
        },
        'codespeed.result': {
            'Meta': {'unique_together': "(('revision', 'executable', 'benchmark', 'environment'),)", 'object_name': 'Result'},
            'benchmark': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'results'", 'to': "orm['codespeed.Benchmark']"}),
            'date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'environment': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'results'", 'to': "orm['codespeed.Environment']"}),
            'executable': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'results'", 'to': "orm['codespeed.Executable']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'revision': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'results'", 'to': "orm['codespeed.Revision']"}),
            'std_dev': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'val_max': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'val_min': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'value': ('django.db.models.fields.FloatField', [], {})
        },
        'codespeed.revision': {
            'Meta': {'unique_together': "(('commitid', 'project'),)", 'object_name': 'Revision'},
            'author': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'commitid': ('django.db.models.fields.CharField', [], {'max_length': '42'}),
            'date': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'revisions'", 'to': "orm['codespeed.Project']"}),
            'tag': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'})
        }
    }

    complete_apps = ['codespeed']
