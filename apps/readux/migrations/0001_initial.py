# Generated by Django 2.1.2 on 2019-08-22 16:59

from django.conf import settings
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('annotations', '0003_auto_20190822_1659'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('canvases', '0002_canvas_is_starting_page'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserAnnotation',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('x', models.IntegerField()),
                ('y', models.IntegerField()),
                ('w', models.IntegerField()),
                ('h', models.IntegerField()),
                ('order', models.IntegerField(default=0)),
                ('content', models.CharField(max_length=1000)),
                ('resource_type', models.CharField(choices=[('cnt:ContentAsText', 'ocr'), ('dctypes:Text', 'text')], default='dctypes:Text', max_length=50)),
                ('motivation', models.CharField(choices=[('oa:commenting', 'commenting'), ('sc:painting', 'painting')], default='sc:painting', max_length=50)),
                ('format', models.CharField(choices=[('text/plain', 'plain text'), ('text/html', 'html')], default='text/plain', max_length=20)),
                ('language', models.CharField(default='en', max_length=10)),
                ('oa_annotation', django.contrib.postgres.fields.jsonb.JSONField(default=dict)),
                ('svg', models.TextField()),
                ('start_offset', models.IntegerField(default=None, null=True)),
                ('end_offset', models.IntegerField(default=None, null=True)),
                ('canvas', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='canvases.Canvas')),
                ('end_selector', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='end_selector', to='annotations.Annotation')),
                ('owner', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('start_selector', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='start_selector', to='annotations.Annotation')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
