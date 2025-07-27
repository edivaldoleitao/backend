import json
from datetime import datetime

from api.entities.favorite import Favorite
from django.http import HttpResponseBadRequest
from django.http import HttpResponseNotAllowed
from django.http import HttpResponseNotFound
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from django.views.decorators.http import require_http_methods
from django.views.decorators.http import require_POST

from track_save.api.controllers.preference_controller import create_preference
from track_save.api.controllers.preference_controller import get_preferences
from track_save.api.controllers.preference_controller import update_preference_orcamento


@csrf_exempt
@require_POST
def create_preference_view(request):
    try:
        data = json.loads(request.body)

        preference = create_preference(
            id_user=data.get("id_user"),
            marca=data.get("marca"),
            orcamento=data.get("orcamento"),
            build_ids=data.get("build"),
        )
        if not preference:
            return HttpResponseBadRequest("Erro ao criar preferência")

        # Monta resposta com produtos do build
        build_data = [{"id": p.id, "nome": p.name} for p in preference.build.all()]

        return JsonResponse(
            {
                "id": preference.id,
                "user": preference.user.id,
                "marca": preference.marca,
                "orcamento": str(preference.orcamento),
                "build": build_data,
            },
            status=201,
        )

    except json.JSONDecodeError:
        return HttpResponseBadRequest("JSON inválido")
    except Exception as e:
        return HttpResponseBadRequest(f"Erro interno: {e}")


@csrf_exempt
@require_GET
def get_preference_view(request):
    try:
        preferences = get_preferences()

        pref = [
            {
                "email": p.user.email,
                "marca": p.marca,
                "orcamento": p.orcamento,
                "build": [{"id": prod.id, "nome": prod.name} for prod in p.build.all()],
            }
            for p in preferences
        ]
        return JsonResponse(
            pref,
            safe=False,
        )

    except json.JSONDecodeError:
        return HttpResponseBadRequest("JSON inválido")
    except Favorite.DoesNotExist:
        return HttpResponseNotFound("Usuário ou Produto não encontrado")
    except ValueError as e:
        return HttpResponseBadRequest(str(e))
    except Exception as e:
        return HttpResponseBadRequest(f"Erro interno: {e}")


@csrf_exempt
@require_http_methods(["PATCH"])
def update_preference_orcamento_view(request, pk):
    try:
        data = json.loads(request.body)
        novo_orcamento = data.get("orcamento")
        if novo_orcamento is None:
            return HttpResponseBadRequest("Informe um valor para 'orcamento'.")

        preference = update_preference_orcamento(pk, novo_orcamento)
        if not preference:
            return HttpResponseNotFound("Preferência não encontrada")

        return JsonResponse(
            {
                "id": preference.id,
                "user": preference.user.email,
                "marca": preference.marca,
                "orcamento": preference.orcamento,
                "build": [p.id for p in preference.build.all()],
            },
            status=200,
        )
    except json.JSONDecodeError:
        return HttpResponseBadRequest("JSON inválido")
    except Exception as e:
        return HttpResponseBadRequest(f"Erro interno: {e}")
