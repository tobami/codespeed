    # -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from django.views.generic import list_detail
from django.views.generic.simple import direct_to_template, redirect_to
from pyspeed.codespeed.models import Result, Revision, Interpreter
from pyspeed import settings

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
    #(r'^$', direct_to_template, {'template': 'base.html'}),
    (r'^$', redirect_to, {'url': '/overview'}),
)

urlpatterns += patterns('pyspeed.codespeed.views',
    (r'^overview/$', 'overview'),
    (r'^overview/table/$', 'overviewtable'),
    (r'^timeline/$', 'timeline'),
    (r'^timeline/json/$', 'getdata'),
    (r'^results/$', 'results'),
    (r'^results/table/$', 'resultstable'),
    # URL interface for adding results
    (r'^result/add/$', 'addresult'),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    )
