# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'Revision.author'
        db.alter_column(u'codespeed_revision', 'author', self.gf('django.db.models.fields.CharField')(max_length=100))

        # Changing field 'Environment.kernel'
        db.alter_column(u'codespeed_environment', 'kernel', self.gf('django.db.models.fields.CharField')(max_length=100))

        # Changing field 'Environment.name'
        db.alter_column(u'codespeed_environment', 'name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100))

        # Changing field 'Environment.memory'
        db.alter_column(u'codespeed_environment', 'memory', self.gf('django.db.models.fields.CharField')(max_length=100))

        # Changing field 'Environment.os'
        db.alter_column(u'codespeed_environment', 'os', self.gf('django.db.models.fields.CharField')(max_length=100))

        # Changing field 'Environment.cpu'
        db.alter_column(u'codespeed_environment', 'cpu', self.gf('django.db.models.fields.CharField')(max_length=100))

        # Changing field 'Benchmark.name'
        db.alter_column(u'codespeed_benchmark', 'name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100))

    def backwards(self, orm):

        # Changing field 'Revision.author'
        db.alter_column(u'codespeed_revision', 'author', self.gf('django.db.models.fields.CharField')(max_length=30))

        # Changing field 'Environment.kernel'
        db.alter_column(u'codespeed_environment', 'kernel', self.gf('django.db.models.fields.CharField')(max_length=30))

        # Changing field 'Environment.name'
        db.alter_column(u'codespeed_environment', 'name', self.gf('django.db.models.fields.CharField')(max_length=30, unique=True))

        # Changing field 'Environment.memory'
        db.alter_column(u'codespeed_environment', 'memory', self.gf('django.db.models.fields.CharField')(max_length=30))

        # Changing field 'Environment.os'
        db.alter_column(u'codespeed_environment', 'os', self.gf('django.db.models.fields.CharField')(max_length=30))

        # Changing field 'Environment.cpu'
        db.alter_column(u'codespeed_environment', 'cpu', self.gf('django.db.models.fields.CharField')(max_length=30))

        # Changing field 'Benchmark.name'
        db.alter_column(u'codespeed_benchmark', 'name', self.gf('django.db.models.fields.CharField')(max_length=30, unique=True))

    models = {
        u'codespeed.benchmark': {
            'Meta': {'object_name': 'Benchmark'},
            'benchmark_type': ('django.db.models.fields.CharField', [], {'default': "'C'", 'max_length': '1'}),
            'default_on_comparison': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lessisbetter': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': u"orm['codespeed.Benchmark']", 'null': 'True', 'blank': 'True'}),
            'units': ('django.db.models.fields.CharField', [], {'default': "'seconds'", 'max_length': '20'}),
            'units_title': ('django.db.models.fields.CharField', [], {'default': "'Time'", 'max_length': '30'})
        },
        u'codespeed.branch': {
            'Meta': {'unique_together': "(('name', 'project'),)", 'object_name': 'Branch'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'branches'", 'to': u"orm['codespeed.Project']"})
        },
        u'codespeed.environment': {
            'Meta': {'object_name': 'Environment'},
            'cpu': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kernel': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'memory': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'os': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'})
        },
        u'codespeed.executable': {
            'Meta': {'unique_together': "(('name', 'project'),)", 'object_name': 'Executable'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'executables'", 'to': u"orm['codespeed.Project']"})
        },
        u'codespeed.project': {
            'Meta': {'object_name': 'Project'},
            'commit_browsing_url': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'}),
            'repo_pass': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'repo_path': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'repo_type': ('django.db.models.fields.CharField', [], {'default': "'N'", 'max_length': '1'}),
            'repo_user': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'track': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        u'codespeed.report': {
            'Meta': {'unique_together': "(('revision', 'executable', 'environment'),)", 'object_name': 'Report'},
            '_tablecache': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'colorcode': ('django.db.models.fields.CharField', [], {'default': "'none'", 'max_length': '10'}),
            'environment': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'reports'", 'to': u"orm['codespeed.Environment']"}),
            'executable': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'reports'", 'to': u"orm['codespeed.Executable']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'revision': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'reports'", 'to': u"orm['codespeed.Revision']"}),
            'summary': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'})
        },
        u'codespeed.result': {
            'Meta': {'unique_together': "(('revision', 'executable', 'benchmark', 'environment'),)", 'object_name': 'Result'},
            'benchmark': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'results'", 'to': u"orm['codespeed.Benchmark']"}),
            'date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'environment': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'results'", 'to': u"orm['codespeed.Environment']"}),
            'executable': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'results'", 'to': u"orm['codespeed.Executable']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'revision': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'results'", 'to': u"orm['codespeed.Revision']"}),
            'std_dev': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'val_max': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'val_min': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'value': ('django.db.models.fields.FloatField', [], {})
        },
        u'codespeed.revision': {
            'Meta': {'unique_together': "(('commitid', 'branch'),)", 'object_name': 'Revision'},
            'author': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'branch': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'revisions'", 'to': u"orm['codespeed.Branch']"}),
            'commitid': ('django.db.models.fields.CharField', [], {'max_length': '42'}),
            'date': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'revisions'", 'null': 'True', 'to': u"orm['codespeed.Project']"}),
            'tag': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'})
        }
    }

    complete_apps = ['codespeed']