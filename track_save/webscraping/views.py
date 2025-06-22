from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from track_save.webscraping.webscraping_factory import get_scraper
from track_save.webscraping.enums import Categories

class WebscrapingAPIView(APIView):
  @api_view(['POST'])
  def run_scraper(request):
    """
    Espera um JSON:
      {
        "name": "kabum",
        "category": "GPU"
      }
    Retorna a lista de produtos já em JSON.
    """
    name     = request.data.get('name')
    category = request.data.get('category')

    if not name or not category:
      return Response(
      {'detail': 'Campos "name" e "category" são obrigatórios.'},
      status=status.HTTP_400_BAD_REQUEST
      )

    # valida categoria
    try:
      cat_enum = Categories[category.upper()]
    except KeyError:
      return Response(
      {'detail': f'Categoria "{category}" inválida.'},
      status=status.HTTP_400_BAD_REQUEST
      )

    # instancia o scraper
    try:
      scraper = get_scraper(name, category=cat_enum)
    except ValueError as e:
      return Response(
      {'detail': str(e)},
      status=status.HTTP_404_NOT_FOUND
      )

    # executa e captura erros
    try:
      data = scraper.run()
    except Exception as e:
      return Response(
      {'detail': f'Erro no scraper: {e}'},
      status=status.HTTP_500_INTERNAL_SERVER_ERROR
      )

    return Response(data, status=status.HTTP_200_OK)
