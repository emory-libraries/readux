from django.contrib.postgres.fields import JSONField
from django.db import models
from django.conf import settings
from django.db.models import signals
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from abc import abstractmethod
import json
import uuid
import logging

logger = logging.getLogger(__name__)

class AbstractAnnotation(models.Model):
    OCR = 'cnt:ContentAsText'
    TEXT = 'dctypes:Text'
    TYPE_CHOICES = (
        (OCR, 'ocr'),
        (TEXT, 'text')
    )
    
    COMMENTING = 'oa:commenting'
    PAINTING = 'sc:painting'
    MOTIVATION_CHOICES = (
        (COMMENTING, 'commenting'),
        (PAINTING, 'painting')
    )

    PLAIN = 'text/plain'
    HTML = 'text/html'
    FORMAT_CHOICES = (
        (PLAIN, 'plain text'),
        (HTML, 'html')
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    x = models.IntegerField()
    y = models.IntegerField()
    w = models.IntegerField()
    h = models.IntegerField()
    order = models.IntegerField(default=0)
    content = models.CharField(max_length=1000)
    resource_type = models.CharField(max_length=50, choices=TYPE_CHOICES, default=TEXT)
    motivation = models.CharField(max_length=50, choices=MOTIVATION_CHOICES, default=PAINTING)
    format = models.CharField(max_length=20, choices=FORMAT_CHOICES, default=PLAIN)
    canvas = models.ForeignKey('canvases.Canvas', on_delete=models.CASCADE, null=True)
    language = models.CharField(max_length=10, default='en')
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True)
    oa_annotation = JSONField(default=dict, blank=False)
    # TODO Should we keep this for annotations from Mirador, or just get rid of it?
    svg = models.TextField()
    item = None

    ordering = ['order']

    def parse_mirador_annotation(self):
        dimensions = None
        if 'default' in self.oa_annotation['on'][0]['selector'].keys():
            dimensions = self.oa_annotation['on'][0]['selector']['default']['value'].split('=')[-1].split(',')
        elif 'value' in self.oa_annotation['on'][0]['selector']['item'].keys():
            dimensions = self.oa_annotation['on'][0]['selector']['item']['value'].split('=')[-1].split(',')
        if dimensions is not None:
            self.x = dimensions[0]
            self.y = dimensions[1]
            self.w = dimensions[2]
            self.h = dimensions[3]


    def __str__(self):
        return str(self.pk)
    
    class Meta:
        abstract = True

class Annotation(AbstractAnnotation):
    class Meta:
        ordering = ['order']
        abstract = False

@receiver(signals.pre_save, sender=Annotation)
def set_span_element(sender, instance, **kwargs):
    if (instance.resource_type in (sender.OCR,)) or (instance.oa_annotation == '{"annotatedBy": {"name": "ocr"}}'):
        try:
            instance.oa_annotation['annotatedBy'] = {'name': 'ocr'}
            character_count = len(instance.content)
            # 1.6 is a "magic number" that seems to work pretty well ¯\_(ツ)_/¯
            font_size = instance.h / 1.6
            # Assuming a character's width is half the height. This was my first guess.
            # This should give us how long all the characters will be.
            string_width = (font_size / 2) * character_count
            # And this is what we're short.
            space_to_fill = instance.w - string_width
            # Divide up the space to fill and space the letters.
            letter_spacing = space_to_fill / character_count
            # Percent of letter spacing of overall width.
            # This is used by OpenSeadragon. OSD will update the letter spacing relative to
            # the width of the overlayed element when someone zooms in and out.
            relative_letter_spacing = letter_spacing / instance.w
            instance.content = "<span id='{pk}' style='height: {h}px; width: {w}px; font-size: {f}px; letter-spacing: {s}px' data-letter-spacing='{p}'>{content}</span>".format(pk=instance.pk, h=str(instance.h), w=str(instance.w), content=instance.content, f=str(font_size), s=str(letter_spacing), p=str(relative_letter_spacing))
        except ValueError as error:
            instance.content = ""
            logger.warn("WARNING: {e}".format(e=error))
