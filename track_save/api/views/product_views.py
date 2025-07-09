import json

from api.controllers import product_controller
from api.entities.product import Product
from api.entities.product import ProductStore
from api.entities.product import Store
from django.http import HttpResponseBadRequest
from django.http import HttpResponseNotAllowed
from django.http import HttpResponseNotFound
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from django.views.decorators.http import require_POST


@csrf_exempt
@require_POST
def create_store(request):
    try:
        data = json.loads(request.body)
        store = product_controller.create_store(name=data.get("name"))
        return JsonResponse(
            {
                "name": store.name,
                "url_base": store.url_base,
                "is_sponsor": store.is_sponsor,
            },
            status=201,
        )

    except ValueError as e:
        return HttpResponseNotFound(str(e))
    except TypeError as e:
        return HttpResponseBadRequest(f"Erro interno: {e!s}")


@csrf_exempt
@require_GET
def get_stores(request):
    try:
        data = product_controller.get_stores()
        return JsonResponse(data, status=200, safe=False)
    except product_controller.Product.DoesNotExist:
        return HttpResponseNotFound("Produto não encontrado")
    except TypeError as e:
        return HttpResponseBadRequest(f"Erro interno: {e!s}")
    except ValueError as e:
        return HttpResponseBadRequest(str(e))


@csrf_exempt
def update_store(request, name):
    if request.method not in ["PATCH", "PUT"]:
        return HttpResponseNotAllowed(["PATCH", "PUT"])

    try:
        data = json.loads(request.body)

        store = product_controller.update_store(name, **data)

        return JsonResponse(
            {
                "name": store.name,
                "url_base": store.url_base,
                "is_sponsor": store.is_sponsor,
            },
            status=200,
        )
    except Store.DoesNotExist:
        return HttpResponseNotFound("Loja não encontrada")
    except TypeError as e:
        return HttpResponseBadRequest(f"Erro interno: {e}")
    except ValueError as e:
        return HttpResponseBadRequest(str(e))


@csrf_exempt
def delete_store(request, name):
    if request.method != "DELETE":
        return HttpResponseNotAllowed(["DELETE"])
    try:
        result = product_controller.delete_store(name=name)
    except Store.DoesNotExist:
        return HttpResponseNotFound("Store não encontrada")
    except Exception as e:  # noqa: BLE001
        return HttpResponseBadRequest(f"Erro interno: {e!s}")
    else:
        return result


# criar produto
@csrf_exempt
@require_POST
def create_product(request):
    try:
        data = json.loads(request.body)

        # separa os atributos específicos
        spec_fields = {
            key: value
            for key, value in data.items()
            if key not in ["name", "category", "description", "image_url", "brand"]
        }

        product = product_controller.create_product(
            name=data.get("name"),
            category=data.get("category").lower(),
            description=data.get("description"),
            image_url=data.get("image_url"),
            brand=data.get("brand"),
            **spec_fields,
        )

        return JsonResponse(
            {
                "id": product.pk,
                "name": product.name,
                "category": product.category,
                "description": product.description,
                "image_url": product.image_url,
                "brand": product.brand,
                "hash": product.hash,
            },
            status=201,
        )

    except json.JSONDecodeError:
        return HttpResponseBadRequest("JSON inválido")
    except Exception as e:  # noqa: BLE001
        return HttpResponseBadRequest(str(e))


@require_GET
def search_products(request):
    filters = {
        key: request.GET.get(key)
        for key in [
            "id",
            "name",
            "category",
            "store",
            "brand",
            "price_min",
            "price_max",
            "rating_min",
        ]
        if request.GET.get(key) is not None
    }

    if "price_min" in filters:
        filters["price_min"] = float(filters["price_min"])
    if "price_max" in filters:
        filters["price_max"] = float(filters["price_max"])
    if "rating_min" in filters:
        filters["rating_min"] = float(filters["rating_min"])

    try:
        result = product_controller.search_products(filters)
        return JsonResponse(result, safe=not isinstance(result, list), status=200)
    except ValueError as e:
        return HttpResponseNotFound(str(e))
    except TypeError as e:
        return HttpResponseBadRequest(f"Erro interno: {e!s}")


# buscar produto pelo id
@require_GET
def get_product_id(request, product_id):
    try:
        product = product_controller.get_product_by_id(product_id)

        return JsonResponse(
            product,
            status=200,
        )

    except product_controller.Product.DoesNotExist:
        return HttpResponseNotFound("Produto não encontrado")


# buscar produto pelo nome
@require_GET
def get_product_name(request, product_name):
    try:
        products = product_controller.get_product_by_name(product_name)

        return JsonResponse({"products": products}, safe=False, status=200)

    except product_controller.Product.DoesNotExist:
        return HttpResponseNotFound("Produto não encontrado")


# retorna todos os produtos daquela categoria
@require_GET
def get_product_category(request, product_category):
    try:
        products = product_controller.get_product_by_category(product_category)

        if not products:
            return HttpResponseNotFound("Nenhum produto encontrado nesta categoria")

        return JsonResponse({"products": products}, safe=False, status=200)

    except ValueError as e:
        return HttpResponseBadRequest(str(e))
    except Exception as e:  # noqa: BLE001
        return HttpResponseBadRequest(f"Erro interno: {e!s}")


# retorna todos os produtos do banco
@require_GET
def get_products(request):
    try:
        products = product_controller.get_all_products()

        if not products:
            return HttpResponseNotFound("Nenhum pproduto cadastrado")

        return JsonResponse({"products": products}, safe=False, status=200)

    except ValueError as e:
        return HttpResponseBadRequest(str(e))
    except TypeError as e:
        return HttpResponseBadRequest(f"Erro interno: {e!s}")


# update pelo id
@csrf_exempt
def update_product(request, product_id):
    if request.method not in ["PATCH", "PUT"]:
        return HttpResponseNotAllowed(["PATCH", "PUT"])

    try:
        data = json.loads(request.body)

        product = product_controller.update_product(product_id, **data)

        return JsonResponse(
            {
                "id": product.pk,
                "name": product.name,
                "category": product.category,
                "description": product.description,
                "image_url": product.image_url,
                "brand": product.brand,
            },
            status=200,
        )

    except ValueError as e:
        return HttpResponseBadRequest(str(e))
    except Product.DoesNotExist:
        return HttpResponseNotFound("Produto não encontrado.")
    except TypeError as e:
        return HttpResponseBadRequest(f"Erro interno: {e!s}")


# exclusão pelo id
@csrf_exempt
def delete_product(request, product_id):
    try:
        message = product_controller.delete_product(product_id)

        return JsonResponse({"message": message}, status=200)

    except ValueError as e:
        return HttpResponseBadRequest(str(e))
    except Product.DoesNotExist:
        return HttpResponseNotFound("Produto não encontrado.")
    except TypeError as e:
        return HttpResponseBadRequest(f"Erro interno: {e!s}")


@csrf_exempt
@require_POST
def create_product_store(request):
    try:
        data = json.loads(request.body)
        product_id = data.get("product_id")
        store_id = data.get("store_id")
        url_product = data.get("url_product")
        available = data.get("available")

        # chama o controller
        ps = product_controller.create_product_store(
            product_id=product_id,
            store_id=store_id,
            url_product=url_product,
            available=available,
        )

        return JsonResponse(
            {
                "id": ps.pk,
                "product": ps.product.id,
                "store": ps.store.id,
                "url_product": ps.url_product,
                "available": ps.available,
            },
            status=201,
        )

    except json.JSONDecodeError:
        return HttpResponseBadRequest("JSON inválido")
    except ValueError as e:
        return HttpResponseBadRequest(str(e))
    except ProductStore.DoesNotExist:
        return HttpResponseNotFound("ProductStore não encontrado")
    except TypeError as e:
        return HttpResponseBadRequest(f"Erro interno: {e}")


# listar todos os ProductStores
@require_GET
def list_product_stores(request):
    try:
        lst = product_controller.get_all_product_stores()
        if not lst:
            return HttpResponseNotFound("Nenhum ProductStore cadastrado")
        return JsonResponse({"product_stores": lst}, safe=False, status=200)

    except ValueError as e:
        return HttpResponseBadRequest(str(e))
    except TypeError as e:
        return HttpResponseBadRequest(f"Erro interno: {e}")


# buscar ProductStore por ID
@require_GET
def get_product_store_by_id(request, product_store_id):
    try:
        data = product_controller.get_product_store_by_id(product_store_id)
        return JsonResponse(data, status=200)

    except product_controller.ProductStore.DoesNotExist:
        return HttpResponseNotFound("ProductStore não encontrado")
    except TypeError as e:
        return HttpResponseBadRequest(f"Erro interno: {e}")
    except ValueError as e:
        return HttpResponseBadRequest(str(e))


# update pelo ID
@csrf_exempt
def update_product_store(request, product_store_id):
    if request.method not in ["PATCH", "PUT"]:
        return HttpResponseNotAllowed(["PATCH", "PUT"])

    try:
        data = json.loads(request.body)
        ps = product_controller.update_product_store(product_store_id, **data)
        return JsonResponse(
            {
                "id": ps.pk,
                "product": ps.product.id,
                "store": ps.store.id,
                "url_product": ps.url_product,
                "available": ps.available,
            },
            status=200,
        )

    except json.JSONDecodeError:
        return HttpResponseBadRequest("JSON inválido")
    except ValueError as e:
        return HttpResponseBadRequest(str(e))
    except ProductStore.DoesNotExist:
        return HttpResponseNotFound("ProductStore não encontrado")


# exclusão pelo ID
@csrf_exempt
def delete_product_store(request, product_store_id):
    if request.method != "DELETE":
        return HttpResponseNotAllowed(["DELETE"])

    try:
        msg = product_controller.delete_product_store(product_store_id)
        return JsonResponse({"message": msg}, status=200)

    except ProductStore.DoesNotExist:
        return HttpResponseNotFound("ProductStore não encontrado")
    except ValueError as e:
        return HttpResponseBadRequest(str(e))

@csrf_exempt
@require_POST
def search_view(request):
    try:
        # Lê o corpo da requisição
        data = json.loads(request.body)

        # Espera receber um array chamado 'searches'
        searches = data.get("searches")
        if not searches:
            return HttpResponseBadRequest("Campo 'searches' é obrigatório.")

        # Chama o controller
        results = product_controller.generic_search(searches)

        # Retorna JSON
        return JsonResponse(results, safe=False)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
