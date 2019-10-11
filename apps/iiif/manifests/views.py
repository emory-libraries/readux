from django.shortcuts import render
from django.http import JsonResponse
from django.http import HttpResponse
from django.views import View
from django.views.generic.base import TemplateView
from django.core.serializers import serialize
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Manifest
from .export import IiifManifestExport
from .export import JekyllSiteExport
from .forms import JekyllExportForm
from apps.users.models import User
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

class ManifestDetail(View):

    def get_queryset(self):
        return Manifest.objects.filter(pid=self.kwargs['pid'])

    def get(self, request, *args, **kwargs):
        manifest = self.get_queryset()[0].id
        annotators = User.objects.filter(annotation__canvas__manifest__id=manifest).distinct()
        annotators_string = ', '.join([str(i.name) for i in annotators])
        return JsonResponse(
            json.loads(
                serialize(
                    'manifest',
                    self.get_queryset(),
                    version=kwargs['version'],
                    annotators=annotators_string,
                    exportdate=datetime.utcnow()
                )
            )
        , safe=False)

class ManifestSitemap(Sitemap):
    # priority unknown
    def items(self):
        return Manifest.objects.all()

    def location(self, item):
        return reverse('ManifestRender', kwargs={'version': 'v2', 'pid': item.pid})

class ManifestRis(TemplateView):
    content_type = 'application/x-research-info-systems; charset=UTF-8'
    template_name = "citation.ris"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['volume'] = Manifest.objects.filter(pid=kwargs['volume']).first()
        return context


class ManifestExport(View):

    def get_queryset(self):
        return Manifest.objects.filter(pid=self.kwargs['pid'])

    def post(self, request, *args, **kwargs):
        # we should probably move this out of the view, into a library
        manifest = self.get_queryset()[0]
        owners = [request.user.id]

        zip = IiifManifestExport.get_zip(manifest, kwargs['version'], owners=owners)
        resp = HttpResponse(zip, content_type = "application/x-zip-compressed")
        resp['Content-Disposition'] = 'attachment; filename=iiif_export.zip'

        return resp

class JekyllExport(View):

    form_class = JekyllExportForm

    def get_queryset(self):
        return Manifest.objects.filter(pid=self.kwargs['pid'])

    def post(self, request, *args, **kwargs):
        # we should probably move this out of the view, into a library
        manifest = self.get_queryset()[0]
        logger.debug(request.POST)
        logger.debug(dir(self.args))

        export_form = JekyllExportForm(self.request.user, data=request.POST)

        # FIXME this needs to return an error.
        if not export_form.is_valid():
            logger.debug("Export form is not valid: %s", export_form.errors)
        #     # bail out
        #     return

        # if form is valid, then proceed with the export
        cleaned_data = export_form.clean()
        logger.debug("Cleaned Data: %s", dir(cleaned_data))

        export_mode = export_form.cleaned_data['mode']
    #     image_hosting = cleaned_data['image_hosting']
    #     include_images = (image_hosting == 'independently_hosted')
        deep_zoom = export_form.cleaned_data['deep_zoom']

        owners = [request.user.id] # TODO switch to form group vs. solo control


        jekyll_export = JekyllSiteExport(manifest, kwargs['version'], deep_zoom=deep_zoom, owners=owners);
        zip = jekyll_export.get_zip()
        resp = HttpResponse(zip, content_type = "application/x-zip-compressed")
        resp['Content-Disposition'] = 'attachment; filename=jekyll_site_export.zip'

        return resp

    def get_context_data(self, **kwargs):
        context_data = super(JekyllSiteExport, self).get_context_data()
        if not self.request.user.is_anonymous():
            context_data['export_form'] = self.get_form()
        raise "Helpz"
        return context_data


    def render(self, request, **kwargs):
        context_data = self.get_context_data()
        raise "Helpz"
        context_data.update(kwargs)
        return render(request, self.template_name, context_data)
