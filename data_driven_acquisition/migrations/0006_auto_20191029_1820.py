# Generated by Django 2.2.6 on 2019-10-29 18:20

import django.contrib.postgres.fields.hstore
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('data_driven_acquisition', '0005_auto_20191029_1531'),
    ]

    operations = [
        migrations.AddField(
            model_name='packagetemplate',
            name='properties',
            field=django.contrib.postgres.fields.hstore.HStoreField(blank=True, null=True),
        ),
        migrations.DeleteModel(
            name='ACL',
        ),
    ]
