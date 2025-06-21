from django.shortcuts import render

# Create your views here.

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

from .agents.agent_use import processar_recomendacao

@csrf_exempt
def agent_use(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "JSON inválido"}, status=400)

        resultado = processar_recomendacao(data)

        return JsonResponse(resultado, safe=False)

    return JsonResponse({"error": "Método não permitido"}, status=405)