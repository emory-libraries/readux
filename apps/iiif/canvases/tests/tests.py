"""
Test cases for :class:`apps.iiif.canvases`
"""
import json
import httpretty
from django.test import TestCase, Client
from django.urls import reverse
import config.settings.local as settings
from ..models import Canvas, IServer
from .. import services
from .factories import CanvasFactory
from ..apps import CanvasesConfig


class CanvasTests(TestCase):
    fixtures = ['kollections.json', 'manifests.json', 'canvases.json', 'annotations.json']

    def setUp(self):
        self.client = Client()
        self.canvas = Canvas.objects.get(pk='7261fae2-a24e-4a1c-9743-516f6c4ea0c9')
        self.manifest = self.canvas.manifest
        self.assumed_canvas_pid = 'fedora:emory:5622'
        self.assumed_volume_pid = 'readux:st7r6'
        self.assumed_iiif_base = 'https://loris.library.emory.edu'

    def test_default_iiif_image_server_url(self):
        i_server = IServer()
        assert i_server.IIIF_IMAGE_SERVER_BASE == settings.IIIF_IMAGE_SERVER_BASE

    def test_app_config(self):
        assert CanvasesConfig.verbose_name == 'Canvases'
        assert CanvasesConfig.name == 'apps.iiif.canvases'

    def test_ia_ocr_creation(self):
        valid_ia_ocr_response = {
        'ocr': [
            [
            ['III', [120, 1600, 180, 1494, 1597]]
            ],
            [
            ['chambray', [78, 1734, 116, 1674, 1734]]
            ],
            [
            ['tacos', [142, 1938, 188, 1854, 1938]]
            ],
            [
            ['freegan', [114, 2246, 196, 2156, 2245]]
            ],
            [
            ['Kombucha', [180, 2528, 220, 2444, 2528]]
            ],
            [
            ['succulents', [558, 535, 588, 501, 535]],
            ['Thundercats', [928, 534, 1497, 478, 527]]
            ],
            [
            ['poke', [557, 617, 646, 575, 614]],
            ['VHS', [700, 612, 1147, 555, 610]],
            ['chartreuse ', [1191, 616, 1209, 589, 609]],
            ['pabst', [1266, 603, 1292, 569, 603]],
            ['8-bit', [1354, 602, 1419, 549, 600]],
            ['narwhal', [1471, 613, 1566, 553, 592]],
            ['XOXO', [1609, 604, 1670, 538, 596]],
            ['post-ironic', [1713, 603, 1826, 538, 590]],
            ['synth', [1847, 588, 1859, 574, 588]]
            ],
            [
            ['lumbersexual', [1741, 2928, 1904, 2881, 2922]]
            ]
        ]
        }

        canvas = Canvas.objects.get(pid='15210893.5622.emory.edu$95')
        ocr = services.add_positional_ocr(canvas, valid_ia_ocr_response)
        assert len(ocr) == 17
        for word in ocr:
            assert 'w' in word
            assert 'h' in word
            assert 'x' in word
            assert 'y' in word
            assert 'content' in word
            assert isinstance(word['w'], int)
            assert isinstance(word['h'], int)
            assert isinstance(word['x'], int)
            assert isinstance(word['y'], int)
            assert isinstance(word['content'], str)

        canvas.save()
        # ocr_anno = canvas.annotation_set.first()
        # assert ocr_anno.w == ocr[0]['w']

    def test_fedora_ocr_creation(self):
        valid_fedora_positional_response = """523\t 116\t 151\t  45\tDistillery\r\n 704\t 117\t 148\t  52\tplaid,"\r\n""".encode('UTF-8-sig')

        ocr = services.add_positional_ocr(self.canvas, valid_fedora_positional_response)
        assert len(ocr) == 2
        for word in ocr:
            assert 'w' in word
            assert 'h' in word
            assert 'x' in word
            assert 'y' in word
            assert 'content' in word
            assert type(word['w']) == int
            assert type(word['h']) == int
            assert type(word['x']) == int
            assert type(word['y']) == int
            assert type(word['content']) == str

    def test_ocr_from_alto(self):
        alto = open('apps/iiif/canvases/fixtures/alto.xml', 'r').read()
        ocr = services.add_alto_ocr(alto)
        assert ocr[1]['content'] == 'AEN DEN LESIIU'
        assert ocr[1]['h'] == 28
        assert ocr[1]['w'] == 461
        assert ocr[1]['x'] == 814
        assert ocr[1]['y'] == 185

    @httpretty.activate
    def test_line_by_line_from_alto(self):
        alto = open('apps/iiif/canvases/fixtures/alto.xml', 'r').read()
        url = "{p}{c}/datastreams/tei/content".format(
            p=settings.DATASTREAM_PREFIX,
            c=self.canvas.pid.replace('fedora:', '')
        )
        httpretty.register_uri(httpretty.GET, url, body=alto)
        httpretty.register_uri(
            httpretty.GET,
            '{b}/{p}'.format(
                b=self.canvas.IIIF_IMAGE_SERVER_BASE.IIIF_IMAGE_SERVER_BASE,
                p=self.canvas.pid
            ),
            body=''
        )
        self.canvas.default_ocr = 'line'
        self.canvas.annotation_set.all().delete()
        self.canvas.save()
        updated_canvas = Canvas.objects.get(pk=self.canvas.pk)
        ocr = updated_canvas.annotation_set.first()
        assert 'mm' in ocr.content
        assert ocr.h == 26
        assert ocr.w == 90
        assert ocr.x == 916
        assert ocr.y == 0

        for num, anno in enumerate(updated_canvas.annotation_set.all(), start=1):
            assert anno.order == num

    @httpretty.activate
    def test_ocr_from_tsv(self):
        tsv = """content\tx\ty\tw\th\nJordan\t459\t391\t89\t43\t\n\t453\t397\t397\t3\n \t1\t2\t3\t4\n"""
        url = "https://raw.githubusercontent.com/ecds/ocr-bucket/master/{m}/boo.tsv".format(
            m=self.canvas.manifest.pid
        )

        httpretty.register_uri(httpretty.GET, url, body=tsv)
        iiif_server = IServer.objects.get(IIIF_IMAGE_SERVER_BASE='https://images.readux.ecds.emory/')
        canvas = CanvasFactory(IIIF_IMAGE_SERVER_BASE=iiif_server, manifest=self.canvas.manifest, pid='boo')
        ocr = canvas.annotation_set.all().first()
        assert ocr.h == 43
        assert ocr.w == 89
        assert ocr.x == 459
        assert ocr.y == 391
        assert 'Jordan' in ocr.content
        assert len(canvas.annotation_set.all()) == 1

    def test_no_alto_from_empty_result(self):
        ocr = services.add_alto_ocr(None)
        assert ocr is None

    def test_from_bad_alto(self):
        alto = open('apps/iiif/canvases/fixtures/bad_alto.xml', 'r').read()
        ocr = services.add_alto_ocr(alto)
        assert ocr is None

    def test_canvas_detail(self):
        kwargs = {'manifest': self.manifest.pid, 'pid': self.canvas.pid}
        url = reverse('RenderCanvasDetail', kwargs=kwargs)
        response = self.client.get(url)
        serialized_canvas = json.loads(response.content.decode('UTF-8-sig'))
        assert response.status_code == 200
        assert serialized_canvas['@id'] == self.canvas.identifier
        assert serialized_canvas['label'] == str(self.canvas.position)
        assert serialized_canvas['images'][0]['@id'] == self.canvas.anno_id
        assert serialized_canvas['images'][0]['resource']['@id'] == "%s/full/full/0/default.jpg" % (self.canvas.service_id)

    def test_canvas_list(self):
        kwargs = { 'manifest': self.manifest.pid }
        url = reverse('RenderCanvasList', kwargs=kwargs)
        response = self.client.get(url)
        canvas_list = json.loads(response.content.decode('UTF-8-sig'))

        assert response.status_code == 200
        assert len(canvas_list) == 2

    def test_properties(self):
        assert self.canvas.identifier == "%s/iiif/%s/canvas/%s" % (settings.HOSTNAME, self.assumed_volume_pid, self.assumed_canvas_pid)
        assert self.canvas.service_id == "%s/%s" % (self.assumed_iiif_base, self.assumed_canvas_pid)
        assert self.canvas.anno_id == "%s/iiif/%s/annotation/%s" % (settings.HOSTNAME, self.assumed_volume_pid, self.assumed_canvas_pid)
        assert self.canvas.thumbnail == "%s/%s/full/200,/0/default.jpg" % (self.assumed_iiif_base, self.assumed_canvas_pid)
        assert self.canvas.social_media == "%s/%s/full/600,/0/default.jpg" % (self.assumed_iiif_base, self.assumed_canvas_pid)
        assert self.canvas.twitter_media1 == "http://images.readux.ecds.emory.edu/cantaloupe/iiif/2/%s/full/600,/0/default.jpg" % (self.assumed_canvas_pid)
        assert self.canvas.twitter_media2 == "%s/%s/full/600,/0/default.jpg" % (self.assumed_iiif_base, self.assumed_canvas_pid)
        assert self.canvas.uri == "%s/iiif/%s/" % (settings.HOSTNAME, self.assumed_volume_pid)
        assert self.canvas.thumbnail_crop_landscape == "%s/%s/full/,250/0/default.jpg" % (self.assumed_iiif_base, self.assumed_canvas_pid)
        assert self.canvas.thumbnail_crop_tallwide == "%s/%s/pct:5,5,90,90/,250/0/default.jpg" % (self.assumed_iiif_base, self.assumed_canvas_pid)
        assert self.canvas.thumbnail_crop_volume == "%s/%s/pct:15,15,70,70/,600/0/default.jpg" % (self.assumed_iiif_base, self.assumed_canvas_pid)

    def test_wide_image_crops(self):
        pid = '15210893.5622.emory.edu$95'
        canvas = Canvas.objects.get(pid=pid)
        assert canvas.thumbnail_crop_landscape == "%s/%s/pct:25,0,50,100/,250/0/default.jpg" % (canvas.IIIF_IMAGE_SERVER_BASE, pid)
        assert canvas.thumbnail_crop_tallwide == "%s/%s/pct:5,5,90,90/250,/0/default.jpg" % (canvas.IIIF_IMAGE_SERVER_BASE, pid)
        assert canvas.thumbnail_crop_volume == "%s/%s/pct:25,15,50,85/,600/0/default.jpg" % (canvas.IIIF_IMAGE_SERVER_BASE, pid)

    def test_result_property(self):
        assert self.canvas.result == "a retto , dio Quef\u00eca de'"

    def test_no_alto_for_internet_archive(self):
        # iiif_server = IServer.objects.get(IIIF_IMAGE_SERVER_BASE='https://iiif.archivelab.org/iiif/')
        # canvas = CanvasFactory(IIIF_IMAGE_SERVER_BASE=iiif_server, manifest=self.canvas.manifest)
        assert services.fetch_alto_ocr(self.canvas) is None

    def test_get_image_info(self):
        self.canvas.IIIF_IMAGE_SERVER_BASE = IServer.objects.get(IIIF_IMAGE_SERVER_BASE='http://fake.info')
        self.canvas.save()
        updated_canvas = Canvas.objects.get(pk=self.canvas.pk)
        assert updated_canvas.image_info['height'] == 3000
        assert updated_canvas.image_info['width'] == 3000
