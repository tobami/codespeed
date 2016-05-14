# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('codespeed', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='benchmark',
            name='data_type',
            field=models.CharField(default='U', max_length=1, choices=[('U', 'Mean'), ('M', 'Median')]),
        ),
        migrations.AddField(
            model_name='result',
            name='q1',
            field=models.FloatField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='result',
            name='q3',
            field=models.FloatField(null=True, blank=True),
        ),
    ]
