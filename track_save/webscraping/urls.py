from django.urls import path
from .views import WebscrapingAPIView

app_name = "webscraping"

urlpatterns = [
  path('scrape/', WebscrapingAPIView.run_scraper, name='api-run-scraper'),
]
