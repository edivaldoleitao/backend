# Create your views here.

import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .agents.agent_upgrade import generate_schema_string
from .agents.agent_upgrade import processar_upgrade
from .agents.agent_use import generate_schema_string
from .agents.agent_use import processar_recomendacao

schema_str = generate_schema_string("api")


@csrf_exempt
def agent_use(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "JSON inválido"}, status=400)
        print("TESTEEEE")
        resultado = processar_recomendacao(data, schema_str)

        return JsonResponse(resultado, safe=False)

    return JsonResponse({"error": "Método não permitido"}, status=405)


@csrf_exempt
def agent_upgrade(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            setup = data.get("setup")
            descricao = data.get("descricao")

            if not setup or not descricao:
                return JsonResponse(
                    {"error": "Campos 'setup' e 'descricao' são obrigatórios."},
                    status=400,
                )

            # Chama o agent que agora usa a API de busca
            resultado = processar_upgrade(setup, descricao, schema_str)

            return JsonResponse(resultado, safe=False)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Método não permitido"}, status=405)
