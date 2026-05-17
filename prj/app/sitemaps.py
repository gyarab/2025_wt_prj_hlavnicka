from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Prvek, Seznam, Stitek

class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = 'daily'

    def items(self):
        return ['home', 'about', 'api_playground']

    def location(self, item):
        return reverse(item)

class PrvekSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        # Pouze nesmazané prvky, které nemají vlastníka (jsou veřejné)
        return Prvek.objects.filter(smazano=False, vlastnik__isnull=True)

    def lastmod(self, obj):
        return obj.datum_upravy

class SeznamSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        # Pouze seznamy bez vlastníka
        return Seznam.objects.filter(vlastnik__isnull=True)

class StitekSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.5

    def items(self):
        # Pouze štítky bez vlastníka
        return Stitek.objects.filter(vlastnik__isnull=True)
