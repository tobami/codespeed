# -*- coding: utf-8 -*-

import os.path

from django.conf.urls.defaults import *
from django.contrib import admin
import settings

admin.autodiscover()

urlpatterns = patterns('',
    (r'^admin/', include(admin.site.urls)),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^media/(?P<path>.*)$', 'django.views.static.serve',
         {'document_root': settings.MEDIA_ROOT}),
        (r'^admin_media/(?P<path>.*)$', 'django.views.static.serve',
         {'document_root':
              os.path.join(os.path.dirname(admin.__file__), 'media')}),
    )
urlpatterns += patterns('',
    (r'^', include('codespeed.urls')),
)
