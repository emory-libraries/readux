# Generated by Django 2.2.10 on 2021-01-08 19:22

import apps.ingest.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ingest', '0003_auto_20210108_1619'),
    ]

    operations = [
        migrations.AlterField(
            model_name='local',
            name='temp_file_path',
            field=models.FilePathField(default=apps.ingest.models.make_temp_file, path='/tmp/tmptgz6a_hb'),
        ),
    ]
