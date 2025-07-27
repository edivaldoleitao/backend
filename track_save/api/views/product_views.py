import json

from api.controllers import price_controller
from api.controllers import product_controller
from api.entities.product import Product
from api.entities.product import ProductCategory
from api.entities.product import ProductStore
from api.entities.product import Store
from django.http import HttpResponseBadRequest
from django.http import HttpResponseNotAllowed
from django.http import HttpResponseNotFound
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from django.views.decorators.http import require_POST

import track_save.webscrapping_amazon.scraper.armazena_tera_amazon as amazon_tera


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
    except Exception as e:
        return HttpResponseBadRequest(f"Erro interno: {str(e)}")
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
        msg = product_controller.delete_store(name=name)
        return msg

    except Store.DoesNotExist:
        return HttpResponseNotFound("Store não encontrada")
    except Exception as e:
        return HttpResponseBadRequest(f"Erro interno: {str(e)}")
    else:
        return msg


@csrf_exempt
@require_POST
def create_product(request):
    try:
        data = json.loads(request.body)

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
    except Exception as e:
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


@require_GET
def get_product_details(request, ps_id):
    try:
        product_store = product_controller.get_product_store_by_id(ps_id)
        price_history = price_controller.get_price_by_ps(ps_id)
        price = price_history[-1]
        product = product_controller.get_product_by_id(product_store["product"])
        other_stores = product_controller.get_recent_price_stores(product["id"])

        return JsonResponse(
            {
                "price": price,
                "product_store": product_store,
                "product": product,
                "price_history": price_history,
                "other_stores": other_stores,
            },
            safe=False,
            status=200,
        )

    except price_controller.Price.DoesNotExist:
        return HttpResponseNotFound("Produto não encontrado")
    except product_controller.Product.DoesNotExist:
        return HttpResponseNotFound("Produto não encontrado")
    except product_controller.ProductStore.DoesNotExist:
        return HttpResponseNotFound("ProductStore não encontrado")
    except Exception as e:
        return HttpResponseBadRequest(f"Erro interno: {e}")


@require_GET
def get_product_id(request, product_id):
    try:
        product = product_controller.get_product_by_id(product_id)
        return JsonResponse(product, status=200)
    except product_controller.Product.DoesNotExist:
        return HttpResponseNotFound("Produto não encontrado")


@require_GET
def get_product_name(request, product_name):
    try:
        products = product_controller.get_product_by_name(product_name)
        return JsonResponse({"products": products}, safe=False, status=200)
    except product_controller.Product.DoesNotExist:
        return HttpResponseNotFound("Produto não encontrado")


@require_GET
def get_product_category(request, product_category):
    try:
        products = product_controller.get_product_by_category(product_category)
        if not products:
            return HttpResponseNotFound("Nenhum produto encontrado nesta categoria")
        return JsonResponse({"products": products}, safe=False, status=200)
    except ValueError as e:
        return HttpResponseBadRequest(str(e))
    except Exception as e:
        return HttpResponseBadRequest(f"Erro interno: {e!s}")


@require_GET
def get_products(request):
    try:
        products = product_controller.get_all_products()
        if not products:
            return HttpResponseNotFound("Nenhum produto cadastrado")
        return JsonResponse({"products": products}, safe=False, status=200)
    except ValueError as e:
        return HttpResponseBadRequest(str(e))
    except TypeError as e:
        return HttpResponseBadRequest(f"Erro interno: {e!s}")


@csrf_exempt
def update_product(request, product_id):
    if request.method not in ["PATCH", "PUT"]:
        return HttpResponseNotAllowed(["PATCH", "PUT"])

    try:
        data = json.loads(request.body)
        product = product_controller.update_product(product_id, **data)
        return JsonResponse(
            {
                "id": product.id,
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


@csrf_exempt
def delete_product(request, product_id):
    try:
        message = product_controller.delete_product(product_id)
        return JsonResponse({"message": message}, status=200)
    except ValueError as e:
        return HttpResponseBadRequest(str(e))
    except Product.DoesNotExist:
        return HttpResponseNotFound("Produto não encontrado.")
    except Exception as e:
        return HttpResponseBadRequest(f"Erro interno: {str(e)}")
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

        ps = product_controller.create_product_store(
            product_id=product_id,
            store_id=store_id,
            url_product=url_product,
            available=available,
        )

        return JsonResponse(
            {
                "id": ps.id,
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


@csrf_exempt
def update_product_store(request, product_store_id):
    if request.method not in ["PATCH", "PUT"]:
        return HttpResponseNotAllowed(["PATCH", "PUT"])

    try:
        data = json.loads(request.body)
        ps = product_controller.update_product_store(product_store_id, **data)
        return JsonResponse(
            {
                "id": ps.id,
                "product": ps.product.id,
                "store": ps.store.id,
                "url_product": ps.url_product,
                "available": ps.available,
                "rating": ps.rating,
            },
            status=200,
        )
    except json.JSONDecodeError:
        return HttpResponseBadRequest("JSON inválido")
    except ValueError as e:
        return HttpResponseBadRequest(str(e))
    except ProductStore.DoesNotExist:
        return HttpResponseNotFound("ProductStore não encontrado")


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
        data = json.loads(request.body)
        searches = data.get("searches")
        if not searches:
            return HttpResponseBadRequest("Campo 'searches' é obrigatório.")
        results = product_controller.generic_search(searches)
        return JsonResponse(results, safe=False)
    except Exception as e:
        return HttpResponseBadRequest(f"Erro interno: {e}")
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_GET
def get_terabyte(request):
    try:
        terabyte = amazon_tera.get_terabyte()
        produtos_criados = []
        erros = []

        for i, produto in enumerate(terabyte):
            spec_fields = produto.get("spec_fields", {})
            category = produto.get("categoria", "").lower()

            try:
                if spec_fields:
                    if category == "mouse":
                        product = product_controller.create_product(
                            name=produto.get("nome"),
                            category=category,
                            description=produto.get("descricao"),
                            image_url=produto.get("imagem"),
                            rating=5,
                            brand=produto.get("tecnica", {}).get("Marca"),
                            **spec_fields,
                        )
                    else:
                        product = product_controller.create_product(
                            name=produto.get("nome"),
                            category=category,
                            description=produto.get("descricao"),
                            image_url=produto.get("imagem"),
                            rating=5,
                            brand=produto.get("tecnica", {}).get("Marca"),
                            **spec_fields,
                        )
                    produtos_criados.append(
                        {
                            "id": product.id,
                            "name": product.name,
                            "category": product.category,
                            "description": product.description,
                            "image_url": product.image_url,
                            "brand": product.brand,
                            "hash": product.hash,
                        }
                    )
                spec_fields.clear()
                category == ""
            except Exception as e:
                erros.append(
                    {
                        "index": i,
                        "produto": produto.get("nome"),
                        "brand": produto.get("tecnica", {}).get("Marca"),
                        "erro": str(e),
                    }
                )
                spec_fields.clear()
                category = ""
                continue

        return JsonResponse(
            {"created": produtos_criados, "errors": erros}, safe=False, status=201
        )

    except Exception as e:
        return HttpResponseBadRequest(f"Erro geral: {str(e)}")


@csrf_exempt
@require_GET
def list_product_stores_by_best_rating(request):
    try:
        category = request.GET.get("category", None)
        limit = request.GET.get("limit", None)
        user_id = request.GET.get("user_id", None)

        products = product_controller.list_product_stores_by_best_rating(
            category=category,
            limit=limit,
            user_id=user_id,
        )

        return JsonResponse(products, safe=False, status=200)

    except ValueError as e:
        return HttpResponseBadRequest(str(e))
    except TypeError as e:
        return HttpResponseBadRequest(f"Erro interno: {e!s}")
    except Exception as e:
        return HttpResponseBadRequest(f"Erro interno: {e!s}")
