import json
from django.http import JsonResponse
from django.http import HttpResponseNotAllowed
from django.http import HttpResponseNotFound
from django.http import HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from api.controllers import subscription_controller


@require_http_methods(["GET"])
def list_subscriptions(request):
    subs = subscription_controller.get_subscriptions()
    data = [
        {
            "id": s.id,
            "type": s.type,
            "favorite_quantity": s.favorite_quantity,
            "alert_quantity": s.alert_quantity,
            "interactions_quantity": s.interactions_quantity,
            "price_htr_quantity": s.price_htr_quantity,
            "value": s.value,
        }
        for s in subs
    ]
    return JsonResponse(data, safe=False)


@require_http_methods(["GET"])
def list_subscription_users(request):
    users = subscription_controller.get_all_subscription_user()
    data = [
        {
            "id": su.id, 
            "user_id": su.user.id,
            "email": su.user.email,
            "subscription": su.subscription.type,
            "is_active": su.is_active
        }
        for su in users
    ]
    return JsonResponse(data, safe=False)



@csrf_exempt
def update_subscription(request, subscription_id):
    if request.method not in ["PUT", "PATCH"]:
        return HttpResponseNotAllowed(["PUT", "PATCH"])

    try:
        data = json.loads(request.body)
        updated = subscription_controller.update_subscription(subscription_id, data)
        return JsonResponse({
            "message": "Plano atualizado com sucesso.",
            "subscription_type": updated.type,
            "value": updated.value
        })
    except ValueError as e:
        return HttpResponseNotFound(str(e))
    except Exception as e:
        return HttpResponseBadRequest(str(e))


@csrf_exempt
@require_http_methods(["DELETE"])
def delete_subscription(request, subscription_id):
    try:
        subscription_controller.delete_subscription(subscription_id)
        return JsonResponse({"message": "Plano excluído com sucesso."})
    except ValueError as e:
        return HttpResponseNotFound(str(e))
    except Exception as e:
        return HttpResponseBadRequest(str(e))


@csrf_exempt
@require_http_methods(["GET"])
def get_user_subscription(request, user_id):
    subscription = subscription_controller.get_subscription_user(user_id)
    if not subscription:
        return HttpResponseNotFound("Assinatura não encontrada ou inativa.")

    return JsonResponse({
        "user": subscription.user.id,
        "subscription_type": subscription.subscription.type,
        "is_active": subscription.is_active
    })


@csrf_exempt
@require_http_methods(["POST"])
def create_user_subscription(request):
    try:
        data = json.loads(request.body)
        user_id = data.get("user_id")
        plan = data.get("subscription_type")

        subscription = subscription_controller.create_subscription_user(user_id, plan)

        return JsonResponse({
            "message": "Assinatura criada com sucesso",
            "subscription_type": subscription.subscription.type
        }, status=201)
    except Exception as e:
        return HttpResponseBadRequest(str(e))


@csrf_exempt
def update_user_subscription(request, user_id):
    if request.method not in ["PUT", "PATCH"]:
        return HttpResponseNotAllowed(["PUT", "PATCH"])

    try:
        data = json.loads(request.body)
        new_type = data.get("subscription_type")
        updated = subscription_controller.update_subscription_user(user_id, new_type)

        return JsonResponse({
            "message": "Assinatura atualizada com sucesso",
            "subscription_type": updated.subscription.type
        })
    except Exception as e:
        return HttpResponseBadRequest(str(e))


@csrf_exempt
def cancel_user_subscription(request, user_id):
    if request.method not in ["PUT", "PATCH"]:
        return HttpResponseNotAllowed(["PUT", "PATCH"])

    try:
        subscription_controller.cancel_subscription_user(user_id)
        return JsonResponse({"message": "Assinatura cancelada com sucesso"})
    except Exception as e:
        return HttpResponseBadRequest(str(e))

@csrf_exempt
def delete_subscription_user(request, subscription_id):
    if request.method != "DELETE":
        return HttpResponseNotAllowed(["DELETE"])

    try:
        subscription_controller.delete_subscription_user(subscription_id)
        return JsonResponse({"message": "Assinatura deletada com sucesso"})
    except Exception as e:
        return HttpResponseBadRequest(str(e))