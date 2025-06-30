import json
from datetime import datetime

from django.http import HttpResponseBadRequest
from django.http import HttpResponseNotAllowed
from django.http import HttpResponseNotFound
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from django.views.decorators.http import require_POST

from api.controllers.price_controller import create_price
from api.controllers.price_controller import delete_price
from api.controllers.price_controller import get_all_prices
from api.controllers.price_controller import get_all_prices_with_product
from api.controllers.price_controller import get_price_by_id
from api.controllers.price_controller import update_price
from api.entities.price import Price
from api.entities.product import ProductStore


# criar Price
@csrf_exempt
@require_POST
def create_price_view(request):
    try:
        data = json.loads(request.body)

        # converte a string em date
        date_str = data.get("collection_date")
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return HttpResponseBadRequest(
                "collection_date deve estar no formato YYYY-MM-DD"
            )

        p = create_price(
            product_store_id=data.get("product_store_id"),
            value=data.get("value"),
            collection_date=date_obj,
        )

        return JsonResponse(
            {
                "id": p.id,
                "product_store": p.product_store.id,
                "value": str(p.value),
                "collection_date": p.collection_date.isoformat(),
            },
            status=201,
        )

    except json.JSONDecodeError:
        return HttpResponseBadRequest("JSON inválido")
    except ProductStore.DoesNotExist:
        return HttpResponseNotFound("ProductStore não encontrado")
    except ValueError as e:
        return HttpResponseBadRequest(str(e))
    except Exception as e:
        return HttpResponseBadRequest(f"Erro interno: {e}")


# listar todos os Prices
@csrf_exempt
@require_GET
def list_prices(request):
    try:
        lst = get_all_prices()
        if not lst:
            return HttpResponseNotFound("Nenhum Price cadastrado")
        return JsonResponse({"prices": lst}, safe=False, status=200)
    except Exception as e:
        return HttpResponseBadRequest(f"Erro interno: {e}")


# buscar Price por ID
@csrf_exempt
@require_GET
def get_price(request, price_id):
    try:
        data = get_price_by_id(price_id)
        return JsonResponse(data, status=200)
    except Price.DoesNotExist:
        return HttpResponseNotFound("Price não encontrado")
    except Exception as e:
        return HttpResponseBadRequest(f"Erro interno: {e}")


# atualizar Price
@csrf_exempt
def update_price_view(request, price_id):
    if request.method not in ["POST", "PUT"]:
        return HttpResponseNotAllowed(["POST", "PUT"])

    try:
        data = json.loads(request.body)

        # ——— converte collection_date de string para date ———
        if "collection_date" in data:
            try:
                data["collection_date"] = datetime.strptime(
                    data["collection_date"], "%Y-%m-%d"
                ).date()
            except (ValueError, TypeError):
                return HttpResponseBadRequest(
                    "collection_date deve estar no formato YYYY-MM-DD"
                )

        p = update_price(price_id, **data)

        return JsonResponse(
            {
                "id": p.id,
                "product_store": p.product_store.id,
                "value": str(p.value),
                # agora p.collection_date é um date de verdade
                "collection_date": p.collection_date.isoformat(),
            },
            status=200,
        )

    except json.JSONDecodeError:
        return HttpResponseBadRequest("JSON inválido")
    except Price.DoesNotExist:
        return HttpResponseNotFound("Price não encontrado")
    except ProductStore.DoesNotExist:
        # caso você aceite trocar o product_store_id via update
        return HttpResponseNotFound("ProductStore não encontrado")
    except ValueError as e:
        return HttpResponseBadRequest(str(e))
    except Exception as e:
        return HttpResponseBadRequest(f"Erro interno: {e}")


# excluir Price
@csrf_exempt
def delete_price_view(request, price_id):
    if request.method != "DELETE":
        return HttpResponseNotAllowed(["DELETE"])
    try:
        msg = delete_price(price_id)
        return JsonResponse({"message": msg}, status=200)
    except Price.DoesNotExist:
        return HttpResponseNotFound("Price não encontrado")
    except Exception as e:
        return HttpResponseBadRequest(f"Erro interno: {e}")


@csrf_exempt
@require_GET
def get_all_prices_with_product_data(request):
    """
    Retorna todos os Prices com dados dos produtos.
    """
    try:
        lst = get_all_prices_with_product()
        if not lst:
            return HttpResponseNotFound("Nenhum Price cadastrado")
        return JsonResponse({"products": lst}, safe=False, status=200)
    except Exception as e:
        return HttpResponseBadRequest(f"Erro interno: {e}")
