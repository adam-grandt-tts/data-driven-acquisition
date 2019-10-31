# Generated by Django 2.2.6 on 2019-10-29 20:54

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('data_driven_acquisition', '0006_auto_20191029_1820'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='packagetemplate',
            options={'get_latest_by': 'created_at', 'permissions': (('can_deploy', 'Can deploy package from template'),)},
        ),
        migrations.RemoveField(
            model_name='packagetemplate',
            name='root_package_path',
        ),
        migrations.AddField(
            model_name='packagetemplate',
            name='package_root_path',
            field=models.CharField(default='asdf', help_text='The path to the package locairton in the repository', max_length=1024),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='folder',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='subfolders', to='data_driven_acquisition.Folder'),
        ),
    ]