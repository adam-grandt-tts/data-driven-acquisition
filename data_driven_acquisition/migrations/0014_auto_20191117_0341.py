# Generated by Django 2.2.6 on 2019-11-17 03:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_driven_acquisition', '0013_auto_20191115_2316'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='packageproperty',
            name='options',
        ),
        migrations.AddField(
            model_name='packageproperty',
            name='options_list',
            field=models.TextField(blank=True, help_text='Enter each option in a line.', null=True),
        ),
        migrations.AlterField(
            model_name='packageproperty',
            name='property_type',
            field=models.CharField(choices=[('String', 'String'), ('Text', 'Text'), ('Number', 'Number'), ('Integer', 'Integer'), ('Boolean', 'Boolean'), ('List', 'List')], default='Document', max_length=15),
        ),
    ]
