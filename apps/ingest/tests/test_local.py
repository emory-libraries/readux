""" Tests for local ingest """
from os import listdir
from os.path import exists, join
from uuid import UUID
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from apps.iiif.manifests.models import ImageServer
from ..models import Local
from ..tasks import create_manifest, create_canvas_task

class LocalTest(TestCase):
    """ Tests for ingest.models.Local """
    def setUp(self):
        """ Set instance variables. """
        self.fixture_path = join(settings.APPS_DIR, 'ingest/fixtures/')

    def test_bundle_upload(self):
        """ It should upload the zip files, unzip relevent files, and clean up. """
        for bundle in ['bundle.zip', 'nested_volume.zip', 'csv_meta.zip']:
            local = Local()
            local.bundle = SimpleUploadedFile(
                name=bundle,
                content=open(join(self.fixture_path, bundle), 'rb').read()
            )
            local.save()
            assert all(item.is_dir() for item in local.bundle_dirs)
            image_directory_path = local.image_directory
            ocr_directory_path = local.ocr_directory
            assert exists(join(local.image_directory, 'not_image.txt')) is False
            assert exists(join(local.ocr_directory, '00000008.jpg')) is False
            assert exists(join(local.image_directory, '00000008.jpg'))
            assert exists(join(local.ocr_directory, '00000008.tsv'))
            local.clean_up()
            assert exists(image_directory_path) is False
            assert exists(ocr_directory_path) is False
            assert exists(local.bundle.path) is False # pylint: disable=no-member

    def test_metadata_from_excel(self):
        """ It should create a manifest with metadat supplied in an Excel file. """
        local = Local()
        local.bundle = SimpleUploadedFile(
            name='bundle.zip',
            content=open(join(self.fixture_path, 'bundle.zip'), 'rb').read()
        )
        local.save()
        local.manifest = create_manifest(local)

        for key in local.metadata.keys():
            assert local.metadata[key] == getattr(local.manifest, key)

    def test_metadata_from_csv(self):
        """ It should create a manifest with metadat supplied in a CSV file. """
        local = Local()
        local.bundle = SimpleUploadedFile(
            name='csv_meta.zip',
            content=open(join(self.fixture_path, 'csv_meta.zip'), 'rb').read()
        )
        local.save()
        local.manifest = create_manifest(local)

        for key in local.metadata.keys():
            assert local.metadata[key] == getattr(local.manifest, key)

    def test_no_metadata_file(self):
        """ It should create a Manifest even when no metadata file is supplied. """
        local = Local()
        local.bundle = SimpleUploadedFile(
            name='no_meta_file.zip',
            content=open(join(self.fixture_path, 'no_meta_file.zip'), 'rb').read()
        )
        local.save()
        local.manifest = create_manifest(local)

        assert UUID(local.manifest.pid).version == 4

    def test_single_image(self):
        """
        The Zipfile library does not make an `infolist` object for a directory if
        the directory only has one file. Special code was added to handel this case.
        """
        image_server = ImageServer(server_base='https://fake.io')
        image_server.save()
        local = Local(image_server=image_server)
        local.bundle = SimpleUploadedFile(
            name='single-image.zip',
            content=open(join(self.fixture_path, 'single-image.zip'), 'rb').read()
        )
        local.save()
        assert all(not item.is_dir() for item in local.zip_ref.infolist())
        assert all(not item.is_dir() for item in local.bundle_dirs)
        assert len(local.bundle_dirs) == 2
        image_directory_path = local.image_directory
        ocr_directory_path = local.ocr_directory
        assert exists(join(local.ocr_directory, '0011.jpg')) is False
        assert exists(join(local.image_directory, '0011.jpg'))
        assert exists(join(local.ocr_directory, '0011.tsv'))
        local.clean_up()
        assert exists(image_directory_path) is False
        assert exists(ocr_directory_path) is False
        assert exists(local.bundle.path) is False # pylint: disable=no-member

    def test_removing_junk(self):
        """
        Any hidden files should be removed.
        """
        image_server = ImageServer(server_base='https://fake.io')
        image_server.save()
        local = Local(image_server=image_server)
        local.bundle = SimpleUploadedFile(
            name='bundle_with_junk.zip',
            content=open(join(self.fixture_path, 'bundle_with_junk.zip'), 'rb').read()
        )
        local.save()
        files = local.zip_ref.namelist()

        assert 'ocr/.junk.tsv' in [f for f in files if 'junk' in f]
        assert 'images/.00000010.jpg' in [f for f in files if '.0' in f]
        assert exists(join(local.image_directory, '.00000010.jpg')) is False
        assert exists(join(local.image_directory, '.junk.tsv')) is False

    def test_removing_underscores(self):
        """
        Any hidden files should be removed.
        """
        image_server = ImageServer(server_base='https://fake.io')
        image_server.save()
        local = Local(image_server=image_server)
        local.bundle = SimpleUploadedFile(
            name='bundle_with_underscores.zip',
            content=open(join(self.fixture_path, 'bundle_with_underscores.zip'), 'rb').read()
        )
        local.save()
        files = local.zip_ref.namelist()
        assert len([f for f in files if '_' in f]) == 10
        assert len([f for f in files if '-' in f]) == 0
        assert len([f for f in listdir(local.image_directory) if '_' in f]) == 0
        assert len([f for f in listdir(local.ocr_directory) if '_' in f]) == 0
        assert len([f for f in listdir(local.image_directory) if '-' in f]) == 5
        assert len([f for f in listdir(local.ocr_directory) if '-' in f]) == 5