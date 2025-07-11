import json

from django.http import HttpResponseBadRequest
from django.http import HttpResponseNotAllowed
from django.http import HttpResponseNotFound
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from rest_framework import generics
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.controllers import user_controller
from api.serielizers.login_serielizers import EmailLoginSerializer
from api.serielizers.user_data_serializers import CurrentUserSerializer


@require_GET
def get_categories(request):
    categories = user_controller.get_categories()
    return JsonResponse(categories, safe=False)


@csrf_exempt
def create_user(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    try:
        data = json.loads(request.body)
        user = user_controller.create_user(
            name=data.get("name"),
            email=data.get("email"),
            password=data.get("password"),
            categories=data.get("categories"),
        )

        return JsonResponse(
            {
                "name": user.name,
                "email": user.email,
                "created_at": user.created_at,
                "is_verified": user.is_verified,
                "categories": user.categories,
            },
            status=201,
        )

    except json.JSONDecodeError:
        return HttpResponseBadRequest("JSON inválido")
    except Exception as e:
        return HttpResponseBadRequest(str(e))


@require_GET
def get_user_id(request, user_id):
    try:
        user = user_controller.get_user_by_id(user_id)

        return JsonResponse(
            {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "created_at": user.created_at,
                "is_verified": user.is_verified,
                "categories": user.categories,
            }
        )

    except user_controller.User.DoesNotExist:
        return HttpResponseNotFound("Usuário não encontrado")


@require_GET
def get_all_users(request):
    users = user_controller.get_all_users()

    users_data = [
        {
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "created_at": u.created_at,
            "is_verified": u.is_verified,
            "categories": u.categories,
        }
        for u in users
    ]

    return JsonResponse(users_data, safe=False)


@csrf_exempt
def update_user(request, user_id):
    if request.method not in ["PUT", "PATCH"]:
        return HttpResponseNotAllowed(["PUT", "PATCH"])

    try:
        data = json.loads(request.body)
        user = user_controller.update_user(
            user_id,
            name=data.get("name"),
            email=data.get("email"),
            categories=data.get("categories"),
        )

        return JsonResponse(
            {
                "name": user.name,
                "email": user.email,
                "created_at": user.created_at,
                "is_verified": user.is_verified,
                "categories": user.categories,
            }
        )

    except json.JSONDecodeError:
        return HttpResponseBadRequest("JSON inválido")
    except user_controller.User.DoesNotExist:
        return HttpResponseNotFound("Usuário não encontrado")
    except Exception as e:
        return HttpResponseBadRequest(str(e))


@csrf_exempt
def update_password(request, user_id):
    if request.method not in ["PUT", "PATCH"]:
        return HttpResponseNotAllowed(["PUT", "PATCH"])

    try:
        data = json.loads(request.body)

        user_controller.update_password(
            user_id,
            nova_senha=data.get("nova_senha"),
            confirmar_senha=data.get("confirmar_senha"),
        )

        return JsonResponse(
            {"status": "success", "message": "Senha redefinida com sucesso"}
        )

    except json.JSONDecodeError:
        return HttpResponseBadRequest("JSON inválido")
    except user_controller.User.DoesNotExist:
        return HttpResponseNotFound("Usuário não encontrado")
    except Exception as e:
        return HttpResponseBadRequest(str(e))


@csrf_exempt
def recover_password(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    try:
        data = json.loads(request.body)
        response = user_controller.recover_password(email=data.get("email"))
        return JsonResponse({"status": "success", "message": response["message"]})

    except json.JSONDecodeError:
        return HttpResponseBadRequest("JSON inválido")
    except user_controller.User.DoesNotExist:
        return HttpResponseNotFound("Email não encontrado")
    except Exception as e:
        return HttpResponseBadRequest(str(e))


@csrf_exempt
def delete_user(request, user_id):
    if request.method != "DELETE":
        return HttpResponseNotAllowed(["DELETE"])

    try:
        user_controller.delete_user(user_id)
        return JsonResponse(
            {"status": "success", "message": "Usuário deletado com sucesso"}
        )

    except user_controller.User.DoesNotExist:
        return HttpResponseNotFound("Usuário não encontrado")


class EmailLoginView(APIView):
    def post(self, request):
        serializer = EmailLoginSerializer(data=request.data)
        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CurrentUserView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CurrentUserSerializer

    def get_object(self):
        return self.request.user


@csrf_exempt
def confirm_email(request, user_id):
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])

    user_controller.confirm_email(user_id)
    return JsonResponse(
        {"status": "success", "message": "Email do usuário verificado com sucesso"}
    )


### USER SPECIFICATION ###


@csrf_exempt
def create_user_specification(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    try:
        data = json.loads(request.body)
        spec = user_controller.create_user_specification(
            user_id=data.get("user_id"),
            cpu=data.get("cpu"),
            ram=data.get("ram"),
            motherboard=data.get("motherboard"),
            cooler=data.get("cooler"),
            gpu=data.get("gpu"),
            storage=data.get("storage"),
            psu=data.get("psu"),
        )

        return JsonResponse(
            {
                "user_id": spec.user_id.id,
                "cpu": spec.cpu,
                "ram": spec.ram,
                "motherboard": spec.motherboard,
                "cooler": spec.cooler,
                "gpu": spec.gpu,
                "storage": spec.storage,
                "psu": spec.psu,
            },
            status=201,
        )

    except json.JSONDecodeError:
        return HttpResponseBadRequest("JSON inválido")
    except Exception as e:
        return HttpResponseBadRequest(str(e))


@require_GET
def get_user_specification_id(request, user_id):
    try:
        spec = user_controller.get_user_specification_by_user_id(user_id)
        return JsonResponse(
            {
                "user_id": spec.user_id.id,
                "cpu": spec.cpu,
                "ram": spec.ram,
                "motherboard": spec.motherboard,
                "cooler": spec.cooler,
                "gpu": spec.gpu,
                "storage": spec.storage,
                "psu": spec.psu,
            }
        )
    except Exception as e:
        return HttpResponseNotFound(str(e))


@require_GET
def get_all_specifications(request):
    specs = user_controller.get_all_specifications()

    specs_data = [
        {
            "user_id": s.user_id.id,
            "cpu": s.cpu,
            "ram": s.ram,
            "motherboard": s.motherboard,
            "cooler": s.cooler,
            "gpu": s.gpu,
            "storage": s.storage,
            "psu": s.psu,
        }
        for s in specs
    ]

    return JsonResponse(specs_data, safe=False)


@csrf_exempt
def update_user_specification(request, user_id):
    if request.method != "PUT":
        return HttpResponseNotAllowed(["PUT"])

    try:
        data = json.loads(request.body)
        spec = user_controller.update_user_specification(user_id, data)

        return JsonResponse(
            {
                "user_id": spec.user_id.id,
                "cpu": spec.cpu,
                "ram": spec.ram,
                "motherboard": spec.motherboard,
                "cooler": spec.cooler,
                "gpu": spec.gpu,
                "storage": spec.storage,
                "psu": spec.psu,
            }
        )

    except json.JSONDecodeError:
        return HttpResponseBadRequest("JSON inválido")
    except Exception as e:
        return HttpResponseBadRequest(str(e))


@csrf_exempt
def delete_user_specification(request, user_id):
    if request.method != "DELETE":
        return HttpResponseNotAllowed(["DELETE"])

    try:
        user_controller.delete_user_specification(user_id)
        return JsonResponse({"message": "Especificação deletada com sucesso."})

    except Exception as e:
        return HttpResponseBadRequest(str(e))
