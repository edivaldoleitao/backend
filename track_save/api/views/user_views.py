from django.shortcuts import render
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.views.decorators.http import require_GET
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseNotAllowed, HttpResponseNotFound
from django.contrib.auth.hashers import make_password
from api.entities.user import User, UserCategory
from django.views.decorators.csrf import csrf_exempt
import json

# pro front pegar as categorias
@require_GET
def get_categories(request):
    categories = [
        {"value": choice.value, "label": choice.label}
        for choice in UserCategory
    ]
    return JsonResponse(categories, safe=False)

@csrf_exempt # desativa o csrf_token pra TESTES
def create_user(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'], 'Método não permitido!')
        
    try:
        data = json.loads(request.body)
        
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        categories = data.get('categories')
        
        ##### VALIDAÇÕES #####
    
        try:
            validate_email(email)
        except ValidationError:
            return HttpResponseBadRequest('Formato de email inválido!')
        
        # validação para email já cadastrado
        if User.objects.filter(email=email).exists():
            return HttpResponseBadRequest('Este email já foi cadastrado.')

        # validação de preenchimento de campos
        if not all([name, email, password, categories]):
            return HttpResponseBadRequest('Todos os campos são obrigatórios.')
        
        # valida se é uma lista (evitar erro de tipo na gravação do dado no banco)
        if not isinstance(categories, list):
            return HttpResponseBadRequest('categories tem que ser uma lista.')

        # cria o usuário
        user = User.objects.create(
            name=name,
            email=email,
            password=make_password(password), # criptografa a senha
            is_verified=False,
            categories=categories
        )
        
        return JsonResponse({
            'id': user.id,
            'email': user.email,
            'name': user.name,
            'created_at': user.created_at,
            'is_verified': user.is_verified,
            'categories': user.categories
        }, status=201) # status de criado com sucesso
        
    except json.JSONDecodeError:
        return HttpResponseBadRequest('JSON inválido')
    except Exception as e:
        return HttpResponseBadRequest(f'Erro: {str(e)}')
    
# GET pelo ID
def get_user_id(request, user_id):
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'], 'Método não permitido!')

    try:
        user = User.objects.get(id=user_id)

        return JsonResponse({
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'created_at': user.created_at,
            'is_verified': user.is_verified,
            'categories': user.categories,
        })

    except User.DoesNotExist:
        return HttpResponseNotFound('Usuário não encontrado.')

# GET de TODOS os users
def get_all_users(request):
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'], 'Método não permitido!')

    users = User.objects.all()

    users_data = []
    for user in users:
        users_data.append({
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'created_at': user.created_at,
            'is_verified': user.is_verified,
            'categories': user.categories,
        })

    return JsonResponse(users_data, safe=False)
    
def update_user(request):
    if request.method not in ['PUT', 'PATCH']:
        return HttpResponseNotAllowed(['PUT', 'PATCH'], 'Método não permitido!')

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponseBadRequest('JSON inválido.')

    user_id = data.get('id')

    if not user_id:
        return JsonResponse({
            'status': 'error',
            'message': 'O id precisa vir no body da requisição.'
        }, status=400)

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return HttpResponseNotFound('Usuário não encontrado.')

    name = data.get('name')
    email = data.get('email')
    categories = data.get('categories')

    if name is not None:
        user.name = name

    if email is not None:
        user.email = email

    if categories is not None:
        if not isinstance(categories, list):
            return HttpResponseBadRequest('categories deve ser uma lista.')

        invalid_categories = [c for c in categories if c not in UserCategory.values]
        if invalid_categories:
            return HttpResponseBadRequest(f'Categorias inválidas: {invalid_categories}')

        user.categories = categories

    user.save()

    return JsonResponse({
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'created_at': user.created_at,
        'is_verified': user.is_verified,
        'categories': user.categories,
    })
    
# este método apenas valida a igualdade das senhas digitadas e faz o update no banco,
# ainda falta confirmar como será o fluxo para envio do email de confirmação de redefinição
# da senha
@csrf_exempt
def update_password(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método não permitido'}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'JSON inválido'}, status=400)

    email = data.get('email')
    nova_senha = data.get('nova_senha')
    confirmar_senha = data.get('confirmar_senha')

    if not email or not nova_senha or not confirmar_senha:
        return JsonResponse({'status': 'error', 'message': 'Preencha todos os campos'}, status=400)

    if nova_senha != confirmar_senha:
        return JsonResponse({'status': 'error', 'message': 'As senhas precisam ser iguais'}, status=400)

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Usuário não encontrado'}, status=404)

    user.password = make_password(nova_senha)
    user.save()

    return JsonResponse({'status': 'success', 'message': 'Senha redefinida com sucesso'})

@csrf_exempt
def delete_user(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método não permitido'}, status=405)

    try:
        data = json.loads(request.body)
        email = data.get('email')

        if not email:
            return JsonResponse({
                'status': 'error',
                'message': 'O email precisa ser enviado no body da requisição.'
            }, status=400)

        try:
            user = User.objects.get(email=email)
            user.delete()

            return JsonResponse({
                'status': 'success',
                'message': f'Usuário deletado com sucesso!'
            })

        except User.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': f'Usuário não encontrado.'
            }, status=404)

    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'JSON inválido. Envie um JSON no formato {"email": "seu@email.com"}'
        }, status=400)
   