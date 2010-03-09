    # -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from django.views.generic import list_detail
from django.views.generic.simple import direct_to_template, redirect_to
from codespeed.models import Result, Revision, Interpreter
import settings

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

urlpatterns += patterns('codespeed.views',
    (r'^overview/$', 'overview'),
    (r'^overview/table/$', 'getoverviewtable'),
    (r'^timeline/$', 'timeline'),
    (r'^timeline/json/$', 'gettimelinedata'),
    #(r'^comparison/$', 'comparison'),
    #(r'^results/$', 'results'),
    #(r'^results/table/$', 'resultstable'),
)

urlpatterns += patterns('codespeed.views',
    # URL interface for adding results
    (r'^result/add/$', 'addresult'),
)
