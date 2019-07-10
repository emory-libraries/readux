from django.conf.urls import url, include
from django.urls import path
from . import views

urlpatterns = [
  path('iiif/<version>/<pid>/manifest', views.ManifestDetail.as_view(), name="ManifestRender"),
  path('iiif/<version>/<pid>/export', views.ManifestExport.as_view(), name="ManifestExport"),
  path('vol/<volume>/citation.ris', views.ManifestRis.as_view(), name='ris' ),
]