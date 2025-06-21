from django.http import HttpResponseBadRequest
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from rest_framework import status
from rest_framework.views import APIView

from track_save.webscraping.webscraping_factory import get_scraper

class WebscrapingAPIView(APIView):
  """
  GET /api/scrape/?site=kabum&query=placa+de+video
  """
  @require_GET
  def get_all_by_scraper(request, user_id):
    site  = request.query_params.get("site")
    query = request.query_params.get("query")
    if not site or not query:
      return HttpResponseBadRequest("Parâmetros 'site' e 'query' são obrigatórios")

    try:
      scraper = get_scraper(site, query=query)
    except ValueError as e:
      return JsonResponse({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    # roda o scraping
    data = scraper.run()
    return JsonResponse(data, safe=False, status=status.HTTP_200_OK)
