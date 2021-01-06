# Generated by Django 2.2.10 on 2020-10-21 16:10

import apps.ingest.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ingest', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='local',
            name='temp_file_path',
            field=models.FilePathField(default=None, path=apps.ingest.models.make_temp_file),
        ),
        migrations.AlterField(
            model_name='local',
            name='bundle',
            field=models.FileField(upload_to=''),
        ),
    ]