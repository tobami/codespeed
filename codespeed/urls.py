# -*- coding: utf-8 -*-
from django.conf.urls import url
from django.views.generic import TemplateView

from codespeed import views
from codespeed.feeds import LatestEntries, LatestSignificantEntries

urlpatterns = [
    url(r'^$', TemplateView.as_view(template_name='home.html'), name='home'),
    url(r'^about/$',
        TemplateView.as_view(template_name='about.html'), name='about'),
    # RSS for reports
    url(r'^feeds/latest/$', LatestEntries(), name='latest-results'),
    url(r'^feeds/latest_significant/$', LatestSignificantEntries(),
        name='latest-significant-results'),
]

urlpatterns += [
    url(r'^reports/$', views.reports, name='reports'),
    url(r'^changes/$', views.changes, name='changes'),
    url(r'^changes/table/$', views.getchangestable, name='getchangestable'),
    url(r'^changes/logs/$', views.displaylogs, name='displaylogs'),
    url(r'^timeline/$', views.timeline, name='timeline'),
    url(r'^timeline/json/$', views.gettimelinedata, name='gettimelinedata'),
    url(r'^comparison/$', views.comparison, name='comparison'),
    url(r'^comparison/json/$', views.getcomparisondata, name='getcomparisondata'),
    url(r'^makeimage/$', views.makeimage, name='makeimage'),
]

urlpatterns += [
    # URLs for adding results
    url(r'^result/add/json/$', views.add_json_results, name='add-json-results'),
    url(r'^result/add/$', views.add_result, name='add-result'),
]
