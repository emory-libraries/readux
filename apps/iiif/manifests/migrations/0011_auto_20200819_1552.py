# Generated by Django 2.2.10 on 2020-08-19 15:52

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('manifests', '0010_auto_20200730_1757'),
    ]

    operations = [
        migrations.AlterField(
            model_name='manifest',
            name='start_canvas',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='start_canvas', to='canvases.Canvas'),
        ),
    ]
