from django.http import HttpResponseBadRequest
from django.http import HttpResponseNotAllowed
from django.http import HttpResponseNotFound
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from django.views.decorators.http import require_POST

from api.entities.product import Product
from api.controllers import product_controller
import json

# criar produto
@csrf_exempt
@require_POST
def create_product(request):

    try:
        data = json.loads(request.body)
        
        # separa os atributos específicos
        spec_fields = {key: value for key, value in data.items() if key 
                       not in ['name', 'category', 'description', 'image_url', 'brand']}
        
        product = product_controller.create_product(
            name = data.get('name').lower(),
            category = data.get('category').lower(),
            description = data.get("description"),
            image_url = data.get("image_url"),
            brand = data.get("brand"),
            **spec_fields
        )
        
        return JsonResponse(
            {
                "id": product.id,
                "name": product.name,
                "category": product.category,
                "description": product.description,
                "image_url": product.image_url,
                "brand": product.brand
            },
            status=201
        )
        
    except json.JSONDecodeError:
        return HttpResponseBadRequest("JSON inválido")
    except Exception as e:
        return HttpResponseBadRequest(str(e))
    
# buscar produto pelo id
@require_GET
def get_product_id(request, product_id):
    
    try:
        product = product_controller.get_product_by_id(product_id)

        return JsonResponse(
            product,
            status=200
        )

    except product_controller.Product.DoesNotExist:
        return HttpResponseNotFound("Produto não encontrado")

# buscar produto pelo nome
@require_GET
def get_product_name(request, product_name):
    
    try:
        product = product_controller.get_product_by_name(product_name)

        return JsonResponse(
            product,
            status=200
        )

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
    except Exception as e:
        return HttpResponseBadRequest(f"Erro interno: {str(e)}")

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
    except Exception as e:
        return HttpResponseBadRequest(f"Erro interno: {str(e)}")
    
# update pelo id
@csrf_exempt
def update_product(request, product_id):
    if request.method not in ["POST", "PUT"]:
        return HttpResponseNotAllowed(["POST", "PUT"])
    
    try:
        data = json.loads(request.body)
        
        product = product_controller.update_product(product_id, **data)
        
        return JsonResponse({
            "id": product.id,
            "name": product.name,
            "category": product.category,
            "description": product.description,
            "image_url": product.image_url,
            "brand": product.brand
        }, status=200)
    
    except ValueError as e:
        return HttpResponseBadRequest(str(e))
    except Product.DoesNotExist:
        return HttpResponseNotFound("Produto não encontrado.")
    except Exception as e:
        return HttpResponseBadRequest(f"Erro interno: {str(e)}")

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
    except Exception as e:
        return HttpResponseBadRequest(f"Erro interno: {str(e)}")