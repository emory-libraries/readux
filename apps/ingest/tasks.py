""" Common tasks for ingest. """
from os import listdir, path, remove
from uuid import uuid4
from urllib.parse import urlparse, unquote
from background_task import background
from django.apps import apps
from apps.iiif.canvases.models import Canvas
from apps.iiif.manifests.models import Manifest, RelatedLink
from .services import UploadBundle
from apps.utils.fetch import fetch_url
import logging

# Use `apps.ge_model` to avoid circular import error. Because the parameters used to
# create a background task have to be serializable, we can't just pass in the model object.
Local = apps.get_model('ingest.local') # pylint: disable = invalid-name
Remote = apps.get_model('ingest.remote')

LOGGER = logging.getLogger(__name__)
logging.getLogger("background_task").setLevel(logging.ERROR)

@background(schedule=1)
def create_canvas_task(ingest_id, is_testing=False):
    """Background task to create canvases and upload images.

    :param ingest_id: Primary key for .models.Local objects
    :type ingest_id: UUID
    :param is_testing: [description], defaults to False
    :type is_testing: bool, optional
    """
    LOGGER.debug('^^^^^Starting create canvas task^^^^^')
    ingest = Local.objects.get(pk=ingest_id)
    # if ingest.manifest is None:
    #     ingest.manifest = create_manifest(ingest)

    if path.isfile(ingest.bundle.path):
        canvas_count = len(listdir(ingest.image_directory))
        for index, image_file in enumerate(sorted(listdir(ingest.image_directory))):
            position = index + 1
            LOGGER.debug(f'^^^^ Creating canvas {position} of {canvas_count} ^^^^')
            ocr_file_name = [
                f for f in listdir(ingest.ocr_directory) if f.startswith(image_file.split('.')[0])
            ][0]

            image_file_path = path.join(ingest.image_directory, image_file)
            ocr_file_path = path.join(ingest.temp_file_path, ingest.ocr_directory, ocr_file_name)

            # The task will retry if there is an error. This prevents the creation of
            # multiple versions of the same canvas
            canvas, created = Canvas.objects.get_or_create(
                manifest=ingest.manifest,
                pid='{m}_{f}'.format(m=ingest.manifest.pid, f=image_file),
                ocr_file_path=ocr_file_path,
                position=position
            )
            if created:
                LOGGER.debug(f'^^^^ Created canvas {position} of {canvas_count} ^^^^')
                if not is_testing:
                    LOGGER.debug(f'^^^^ Uploading canvas {position} of {canvas_count} ^^^^')
                    upload = UploadBundle(canvas, image_file_path)
                    upload.upload_bundle()
                    LOGGER.debug(f'^^^^ Uploaded canvas {position} of {canvas_count} ^^^^')
                canvas.save()
                LOGGER.debug(f'^^^^ Saved canvas {position} of {canvas_count} ^^^^')
                remove(image_file_path)
                remove(ocr_file_path)

    # Sometimes, the IIIF server is not ready to process the image by the time the canvas is saved to
    # the database. As a double check loop through to make sure the height and width has been saved.
    for canvas in ingest.manifest.canvas_set.all():
        if canvas.width == 0 or canvas.height == 0:
            LOGGER.debug(f'^^^^ Re-saving canvas {canvas.position} to get height and width ^^^^')
            canvas.save()

    # Finally clean up the files and the ingest object.
    ingest.clean_up()

@background(schedule=1)
def create_remote_canvases(ingest_id):
    """Task to create Canavs objects from remote IIIF manifest

    :param ingest_id: ID for ingest
    :type ingest: UUID
    """
    # Use `apps.ge_model` to avoid circular import error. Because the parameters used to
    # create a background task have to be serializable, we can't just pass in the model object.
    remote_ingest = Remote.objects.get(pk=ingest_id)

    if remote_ingest.manifest is None:
        remote_ingest.manifest = create_manifest(remote_ingest)
        remote_ingest.save()
        remote_ingest.refresh_from_db()

    # TODO: What if there are multiple sequences? Is that even allowed in IIIF?
    for position, canvas in enumerate(remote_ingest.remote_manifest['sequences'][0]['canvases']):
        canvas_metadata = None
        # TODO: we will need some sort of check for IIIF API version, but not
        # everyone includes a context for each canvas.
        # if canvas['@context'] == 'http://iiif.io/api/presentation/2/context.json':
        canvas_metadata = parse_iiif_v2_canvas(canvas)

        if canvas_metadata is not None:
            canvas, _created = Canvas.objects.get_or_create(
                pid=canvas_metadata['pid'],
                manifest=remote_ingest.manifest,
                position=position
            )

            for (key, value) in canvas_metadata.items():
                setattr(canvas, key, value)
            canvas.save()

    remote_ingest.delete()

def create_manifest(ingest):
    """
    Create or update a Manifest from supplied metadata and images.
    :return: New or updated Manifest with supplied `pid`
    :rtype: iiif.manifest.models.Manifest
    """
    manifest = None
    # Make a copy of the metadata so we don't extract it over and over.
    metadata = ingest.metadata
    if metadata is not None:
        manifest, created = Manifest.objects.get_or_create(pid=metadata['pid'])
        for (key, value) in metadata.items():
            setattr(manifest, key, value)
        if not created:
            manifest.canvas_set.all().delete()
    else:
        manifest = Manifest(pid=str(uuid4()))

    manifest.image_server = ingest.image_server
    manifest.save()

    if isinstance(ingest, Remote):
        RelatedLink(
            manifest=manifest,
            link=ingest.remote_url,
            format='application/ld+json'
        ).save()

    return manifest

# TODO: I don't like this here while the manifest version is on the Remote model class.
def parse_iiif_v2_canvas(canvas):
    """ """
    canvas_id = canvas['@id'].split('/')
    pid = canvas_id[-1] if canvas_id[-1] != 'canvas' else canvas_id[-2]

    service = urlparse(canvas['images'][0]['resource']['service']['@id'])
    resource = unquote(service.path.split('/').pop())

    summary = canvas['description'] if 'description' in canvas.keys() else ''
    label = canvas['label'] if 'label' in canvas.keys() else ''
    return {
        'pid': pid,
        'height': canvas['height'],
        'width': canvas['width'],
        'summary': summary,
        'label': label,
        'resource': resource
    }