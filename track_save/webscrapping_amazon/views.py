from django.http import HttpResponseBadRequest
from django.http import HttpResponseNotAllowed
from django.http import HttpResponseNotFound
from django.http import JsonResponse
from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.views import APIView

from .scraper.armazena_tera_amazon import get_amazon_terabyte


class WebscrappingAmazonTera(APIView):
    @api_view(["GET"])
    def armazena_tera_amazon():
        terabyte, amazon = get_amazon_terabyte()
        return JsonResponse(
            {
                "name": amazon[0]["Marca"],
            },
            status=201,
        )
