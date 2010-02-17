    # -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from django.views.generic import list_detail
from django.views.generic.simple import direct_to_template
from pyspeed.codespeed.models import Result, Revision, Interpreter
from pyspeed import settings

result_list = {
    'queryset': Result.objects.order_by('-date'),
    'template_name': 'result_list.html',
    'template_object_name': 'result',
}

def getresults():
    #Function so that results are not cached
    return Result.objects.filter(revision__project=settings.PROJECT_NAME)

def getinterpreters():
    #Function so that interpreters are not cached
    return Interpreter.objects.filter(name__startswith=settings.PROJECT_NAME)

revision_list = {
    'queryset': Revision.objects.filter(project=settings.PROJECT_NAME).order_by('-date').filter(),
    'template_name': 'revision_list.html',
    'template_object_name': 'revision',
    'extra_context': {
        'result_list': getresults(),
        'interpreter_list': getinterpreters(),
    }
}

urlpatterns = patterns('',
    (r'^$', direct_to_template, {'template': 'base.html'}),
)

urlpatterns += patterns('pyspeed.codespeed.views',
    (r'^overview/$', 'overview'),
    (r'^overview/table/$', 'overviewtable'),
    (r'^results/$', list_detail.object_list, result_list),
    (r'^revision/$', list_detail.object_list, revision_list),
    # URL interface for adding results
    (r'^result/add/$', 'addresult'),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    )
