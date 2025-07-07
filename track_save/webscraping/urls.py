from django.urls import path

from .views import ScrapeAllAPIView
from .views import ScrapeByCategoryAPIView

app_name = "webscraping"

urlpatterns = [
    path("scrape/", ScrapeByCategoryAPIView.as_view(), name="api-run-scraper"),
    path("scrape/all/", ScrapeAllAPIView.as_view(), name="api-run-scraper-all"),
]
