# Generated by Django 2.1.2 on 2018-11-14 20:38

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('manifests', '0002_manifest_pid'),
    ]

    operations = [
        migrations.CreateModel(
            name='Note',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(max_length=255)),
                ('language', models.CharField(default='en', max_length=10)),
            ],
        ),
        migrations.AddField(
            model_name='manifest',
            name='author',
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name='manifest',
            name='published_city',
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name='manifest',
            name='published_date',
            field=models.CharField(default='1798-1875', max_length=25),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='manifest',
            name='publisher',
            field=models.CharField(default='American Sunday-School Union', max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='note',
            name='manifest',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='manifests.Manifest'),
        ),
    ]