# Generated by Django 2.1.15 on 2020-02-24 11:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('codespeed', '0003_project_default_branch'),
    ]

    operations = [
        migrations.AddField(
            model_name='branch',
            name='display_on_comparison_page',
            field=models.BooleanField(default=True, verbose_name='True to display this branch on the comparison page'),
        ),
    ]