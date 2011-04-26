from django.contrib.syndication.feeds import Feed
from speedcenter.codespeed.models import Report
from speedcenter.codespeed import settings


class LatestEntries(Feed):
    title = settings.website_name
    link = "/changes/"
    description = "Last benchmark runs"

    def items(self):
        return Report.objects.order_by('-revision__date')[:10]
