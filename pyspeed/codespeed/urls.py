# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from django.views.generic import list_detail
from pyspeed.codespeed.models import Result
from pyspeed import settings

revision_info = {
    'queryset': Result.objects.filter(revision__project=settings.PROJECT_NAME).order_by('-date'),
    'template_name': 'result_list.html',
    'template_object_name': 'result',
    #'extra_context': {'book_list': Book.objects.all}
}

urlpatterns = patterns('pyspeed.codespeed.views',
    #(r'^$', 'index'),
    (r'^pypy/rev/$', list_detail.object_list, revision_info),
    # REST-like Interface for adding results
    (r'^pypy/result/$', 'addresult'),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    )
