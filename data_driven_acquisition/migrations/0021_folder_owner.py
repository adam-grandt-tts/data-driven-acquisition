# Generated by Django 2.2.9 on 2020-02-04 15:43

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('data_driven_acquisition', '0020_auto_20200127_2220'),
    ]

    operations = [
        migrations.AddField(
            model_name='folder',
            name='owner',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='acquisitions', to=settings.AUTH_USER_MODEL),
        ),
    ]
