from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseNotAllowed, HttpResponseNotFound
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from api.controllers import user_controller
import json


@require_GET
def get_categories(request):
    categories = user_controller.get_categories()
    return JsonResponse(categories, safe=False)


@csrf_exempt
def create_user(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    try:
        data = json.loads(request.body)
        user = user_controller.create_user(
            name=data.get('name'),
            email=data.get('email'),
            password=data.get('password'),
            categories=data.get('categories')
        )

        return JsonResponse({
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'created_at': user.created_at,
            'is_verified': user.is_verified,
            'categories': user.categories,
        }, status=201)

    except json.JSONDecodeError:
        return HttpResponseBadRequest('JSON inválido')
    except Exception as e:
        return HttpResponseBadRequest(str(e))


def get_user_id(request, user_id):
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])

    try:
        user = user_controller.get_user_by_id(user_id)

        return JsonResponse({
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'created_at': user.created_at,
            'is_verified': user.is_verified,
            'categories': user.categories,
        })

    except user_controller.User.DoesNotExist:
        return HttpResponseNotFound('Usuário não encontrado')


def get_all_users(request):
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])

    users = user_controller.get_all_users()

    users_data = [{
        'id': u.id,
        'name': u.name,
        'email': u.email,
        'created_at': u.created_at,
        'is_verified': u.is_verified,
        'categories': u.categories,
    } for u in users]

    return JsonResponse(users_data, safe=False)


@csrf_exempt
def update_user(request, user_id):
    if request.method not in ['PUT', 'PATCH']:
        return HttpResponseNotAllowed(['PUT', 'PATCH'])

    try:
        data = json.loads(request.body)
        user = user_controller.update_user(
            user_id,
            name=data.get('name'),
            email=data.get('email'),
            categories=data.get('categories')
        )

        return JsonResponse({
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'created_at': user.created_at,
            'is_verified': user.is_verified,
            'categories': user.categories,
        })

    except json.JSONDecodeError:
        return HttpResponseBadRequest('JSON inválido')
    except user_controller.User.DoesNotExist:
        return HttpResponseNotFound('Usuário não encontrado')
    except Exception as e:
        return HttpResponseBadRequest(str(e))


@csrf_exempt
def update_password(request, user_id):
    if request.method not in ['PUT', 'PATCH']:
        return HttpResponseNotAllowed(['PUT', 'PATCH'])

    try:
        data = json.loads(request.body)

        user = user_controller.update_password(
            user_id,
            nova_senha=data.get('nova_senha'),
            confirmar_senha=data.get('confirmar_senha')
        )

        return JsonResponse({'status': 'success', 'message': 'Senha redefinida com sucesso'})

    except json.JSONDecodeError:
        return HttpResponseBadRequest('JSON inválido')
    except user_controller.User.DoesNotExist:
        return HttpResponseNotFound('Usuário não encontrado')
    except Exception as e:
        return HttpResponseBadRequest(str(e))


@csrf_exempt
def recover_password(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    try:
        data = json.loads(request.body)
        response = user_controller.recover_password(
            email=data.get('email')
        )
        return JsonResponse({'status': 'success', 'message': response['message']})

    except json.JSONDecodeError:
        return HttpResponseBadRequest('JSON inválido')
    except user_controller.User.DoesNotExist:
        return HttpResponseNotFound('Email não encontrado')
    except Exception as e:
        return HttpResponseBadRequest(str(e))


@csrf_exempt
def delete_user(request, user_id):
    if request.method != 'DELETE':
        return HttpResponseNotAllowed(['DELETE'])

    try:
        user_controller.delete_user(user_id)
        return JsonResponse({'status': 'success', 'message': 'Usuário deletado com sucesso'})

    except user_controller.User.DoesNotExist:
        return HttpResponseNotFound('Usuário não encontrado')
