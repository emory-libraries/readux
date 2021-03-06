# pylint: disable = attribute-defined-outside-init, too-few-public-methods
"""Module for serializing IIIF Annotation"""
from django.core.serializers.base import SerializerDoesNotExist
from apps.iiif.serializers.base import Serializer as JSONSerializer
import config.settings.local as settings

class Serializer(JSONSerializer):
    """
    Serialize a :class:`apps.iiif.annotation.models.Annotation`
    object based on the IIIF Presentation API

    IIIF V2 Annotation List https://iiif.io/api/presentation/2.1/#annotation-list
    """
    def _init_options(self):
        super()._init_options()
        self.owners = self.json_kwargs.pop('owners', 0)

    def get_dump_object(self, obj):
        """
        Serialize an :class:`apps.iiif.annotation.models.Annotation`
        based on the IIIF presentation API

        :param obj: Annotation to be serialized.
        :type obj: :class:`apps.iiif.annotation.models.Annotation`
        :return: Serialzed annotation.
        :rtype: dict
        """
        # TODO: Add more validation checks before trying to serialize.
        if ((self.version == 'v2') or (self.version is None)):
            name = 'OCR'
            if obj.owner_id:
                name = obj.owner.username if  obj.owner.name == '' else obj.owner.name
            data = {
                "@context": "http://iiif.io/api/presentation/2/context.json",
                "@id": str(obj.pk),
                "@type": "oa:Annotation",
                "motivation": obj.motivation,
                "annotatedBy": {
                    "name": name
                },
                "resource": {
                    "@type": obj.resource_type,
                    "format": "text/html",
                    "chars": obj.content,
                    "language": obj.language
                },
                "on": {
                    "full": '{h}/iiif/{v}/{m}/canvas/{c}'.format(
                        h=settings.HOSTNAME,
                        v=self.version,
                        m=obj.canvas.manifest.pid,
                        c=obj.canvas.pid
                    ),
                    "@type": "oa:SpecificResource",
                    "within": {
                        "@id": '{h}/iiif/{v}/{c}/manifest'.format(
                            h=settings.HOSTNAME,
                            v=self.version,
                            c=obj.canvas.manifest.pid
                        ),
                        "@type": "sc:Manifest"
                    },
                    "selector": {
                        "@type": "oa:FragmentSelector",
                        "value": 'xywh={x},{y},{w},{h}'.format(
                            x=str(obj.x),
                            y=str(obj.y),
                            w=str(obj.w),
                            h=str(obj.h)
                        )
                    }
                }
            }
            if hasattr(obj, 'style') and obj.style is not None:
                data['stylesheet'] = self.__serialize_style(obj)

            if obj.item is not None:
                data['on']['selector']['item'] = self.__serialize_item(obj)
            else:
                data['on']['selector']['item'] = {'@type': 'oa:FragmentSelector'}

            if hasattr(obj, 'tags') and obj.tags.exists():
                data['motivation'] = data['motivation'].split(',')
                data['resource'] = [data['resource']]
                for tag in obj.tags.all():
                    wa_tag = {
                        "@type": "oa:Tag",
                        "chars": tag.name
                    }
                    data['resource'].append(wa_tag) # pylint: disable= no-member

            return data
        return None

        # TODO: write serializer for v3 of the IIIF Presentation API.
        # elif (self.version == 'v3'):
        #     return None

    # TODO: is this needed?
    @classmethod
    def __serialize_item(cls, obj):
        return obj.item

    @classmethod
    def __serialize_style(cls, obj):
        """
        Private function to serialize the stylesheet data.

        :param obj: Annotation to be serialized
        :type obj: :class:`apps.iiif.annotation.models.Annotation`
        :return: Stylesheet data compliant with the web annotation standard.
        :rtype: dict
        """
        return {
            "type": "CssStylesheet",
            "value": obj.style
        }

class Deserializer:
    """Deserialize IIIF Annotation

    :raises SerializerDoesNotExist: Not yet implemented.
    """
    def __init__(self, *args, **kwargs):
        raise SerializerDoesNotExist("annotation is a serialization-only serializer")
