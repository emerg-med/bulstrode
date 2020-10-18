# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-03-30 07:49
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sackett', '0016_auto_20160323_1420'),
    ]

    operations = [
        migrations.AddField(
            model_name='diagnosisdata',
            name='icd10_code',
            field=models.CharField(default='', max_length=64),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='diagnosisdata',
            name='notifiable_disease',
            field=models.BooleanField(default=False),
            preserve_default=False,
        ),
    ]
