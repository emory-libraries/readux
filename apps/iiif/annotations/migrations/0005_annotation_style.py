# Generated by Django 2.1.2 on 2019-12-16 13:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0004_auto_20190920_1313'),
    ]

    operations = [
        migrations.AddField(
            model_name='annotation',
            name='style',
            field=models.CharField(blank=True, max_length=1000, null=True),
        ),
    ]
