# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from django.core.urlresolvers import reverse
from django.views.generic import TemplateView
from tastypie.api import Api

from codespeed.feeds import LatestEntries
from codespeed.api import (UserResource, EnvironmentResource,
                           ProjectResource, ExecutableResource, ReportResource,
                           BenchmarkResource, ResultResource, BranchResource,
                           RevisionResource, ResultBundleResource)

feeds = {'latest': LatestEntries}

rest_api = Api(api_name='v1')
rest_api.register(EnvironmentResource())
rest_api.register(UserResource())
rest_api.register(ProjectResource())
rest_api.register(ExecutableResource())
rest_api.register(BenchmarkResource())
rest_api.register(ResultResource())
rest_api.register(BranchResource())
rest_api.register(RevisionResource())
rest_api.register(ReportResource())
rest_api.register(ResultBundleResource())

urlpatterns = patterns('',
    (r'^$', TemplateView.as_view(template_name='home.html')),
    (r'^about/$', TemplateView.as_view(template_name='about.html')),
    # RSS for reports
    (r'^feeds/(?P<url>.*)/$', LatestEntries()),
)

urlpatterns += patterns('codespeed.views',
    url(r'^reports/$', 'reports', name='reports'),
    url(r'^changes/$', 'changes', name='changes'),
    url(r'^changes/table/$', 'getchangestable', name='getchangestable'),
    url(r'^changes/logs/$', 'displaylogs', name='displaylogs'),
    url(r'^timeline/$', 'timeline', name='timeline'),
    url(r'^timeline/json/$', 'gettimelinedata', name='gettimelinedata'),
    url(r'^comparison/$', 'comparison', name='comparison'),
    url(r'^comparison/json/$', 'getcomparisondata', name='getcomparisondata'),
)

urlpatterns += patterns('codespeed.views',
    # URLs for adding results
    (r'^result/add/json/$', 'add_json_results'),
    (r'^result/add/$',      'add_result'),
    (r'^api/', include(rest_api.urls)),
)
