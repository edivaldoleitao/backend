import json
from datetime import datetime
from django.http import HttpResponseBadRequest, HttpResponseNotAllowed, HttpResponseNotFound, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from api.entities.favorite import Favorite
from track_save.api.controllers.favorite_controller import (create_favorite, delete_favorite,
                                                            get_all_favorites, get_favorite_by_id,
                                                            update_favorite)

# POST /api/favorites/create/
@csrf_exempt
@require_POST
def create_favorite_view(request):
    try:
        data = json.loads(request.body)
        # converte created_at
        try:
            dt = datetime.strptime(data.get("created_at"), "%Y-%m-%d").date()
        except (TypeError, ValueError):
            return HttpResponseBadRequest("created_at deve ser YYYY-MM-DD")

        fav = create_favorite(
            user_id=data.get("user_id"),
            product_id=data.get("product_id"),
            created_at=dt,
        )
        return JsonResponse(
            {
                "id": fav.id,
                "user": fav.user.id,
                "product": fav.product.id,
                "created_at": fav.created_at.isoformat(),
            },
            status=201,
        )

    except json.JSONDecodeError:
        return HttpResponseBadRequest("JSON inválido")
    except Favorite.DoesNotExist:
        return HttpResponseNotFound("Usuário ou Produto não encontrado")
    except ValueError as e:
        return HttpResponseBadRequest(str(e))
    except Exception as e:
        return HttpResponseBadRequest(f"Erro interno: {e}")


# GET /api/favorites/
@csrf_exempt
@require_GET
def list_favorites_view(request):
    try:
        lst = get_all_favorites()
        if not lst:
            return HttpResponseNotFound("Nenhum favorito cadastrado")
        return JsonResponse({"favorites": lst}, safe=False, status=200)
    except Exception as e:
        return HttpResponseBadRequest(f"Erro interno: {e}")


# GET /api/favorites/<id>/
@csrf_exempt
@require_GET
def get_favorite_view(request, fav_id):
    try:
        data = get_favorite_by_id(fav_id)
        return JsonResponse(data, status=200)
    except Favorite.DoesNotExist:
        return HttpResponseNotFound("Favorite não encontrado")
    except Exception as e:
        return HttpResponseBadRequest(f"Erro interno: {e}")


# PUT /api/favorites/update/<id>/
@csrf_exempt
def update_favorite_view(request, fav_id):
    if request.method not in ["POST", "PUT"]:
        return HttpResponseNotAllowed(["POST", "PUT"])
    try:
        data = json.loads(request.body)
        # converte created_at se fornecido
        if "created_at" in data:
            try:
                data["created_at"] = datetime.strptime(
                    data["created_at"], "%Y-%m-%d"
                ).date()
            except (TypeError, ValueError):
                return HttpResponseBadRequest("created_at deve ser YYYY-MM-DD")

        fav = update_favorite(fav_id, **data)
        return JsonResponse(
            {
                "id": fav.id,
                "user": fav.user.id,
                "product": fav.product.id,
                "created_at": fav.created_at.isoformat(),
            },
            status=200,
        )

    except json.JSONDecodeError:
        return HttpResponseBadRequest("JSON inválido")
    except Favorite.DoesNotExist:
        return HttpResponseNotFound("Favorite não encontrado")
    except ValueError as e:
        return HttpResponseBadRequest(str(e))
    except Exception as e:
        return HttpResponseBadRequest(f"Erro interno: {e}")


# DELETE /api/favorites/delete/<id>/
@csrf_exempt
def delete_favorite_view(request, fav_id):
    if request.method != "DELETE":
        return HttpResponseNotAllowed(["DELETE"])
    try:
        msg = delete_favorite(fav_id)
        return JsonResponse({"message": msg}, status=200)
    except Favorite.DoesNotExist:
        return HttpResponseNotFound("Favorite não encontrado")
    except Exception as e:
        return HttpResponseBadRequest(f"Erro interno: {e}")
