from django.urls import path
from .views import WebscrapingAPIView

app_name = "webscraping"

urlpatterns = [
  # GET /webscraping/?site=kabum&query=...
  path("", WebscrapingAPIView.as_view(), name="webscraping_api"),
]