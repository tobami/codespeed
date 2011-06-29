from django.contrib.syndication.views import Feed
from codespeed.models import Report
from django.conf import settings


class LatestEntries(Feed):
    title = settings.WEBSITE_NAME
    link = "/changes/"
    description = "Last benchmark runs"

    def items(self):
        return Report.objects.order_by('-revision__date')[:10]
