import json
from datetime import datetime

from django.http import (
    JsonResponse,
    HttpResponseBadRequest,
    HttpResponseNotAllowed,
    HttpResponseNotFound,
)
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from api.controllers.alert_controller import (
    create_alert,
    get_all_alerts,
    get_alert_by_id,
    update_alert,
    delete_alert,
)
from api.entities.alert import Alert
from api.entities.user import User
from api.entities.product import Product


# POST /api/alerts/create/
@csrf_exempt
@require_POST
def create_alert_view(request):
    try:
        data = json.loads(request.body)

        # converte datas de string para date
        try:
            expires = datetime.strptime(data.get("expires_at"), "%Y-%m-%d").date()
            created = datetime.strptime(data.get("created_at"), "%Y-%m-%d").date()
        except (TypeError, ValueError):
            return HttpResponseBadRequest("expires_at e created_at devem ser YYYY-MM-DD")

        alert = create_alert(
            user_id       = data.get("user_id"),
            product_id    = data.get("product_id"),
            desired_price = data.get("desired_price"),
            expires_at    = expires,
            created_at    = created,
        )

        return JsonResponse({
            "id":            alert.id,
            "user":          alert.user.id,
            "product":       alert.product.id,
            "desired_price": str(alert.desired_price),
            "is_active":     alert.is_active,
            "expires_at":    alert.expires_at.isoformat(),
            "created_at":    alert.created_at.isoformat(),
        }, status=201)

    except json.JSONDecodeError:
        return HttpResponseBadRequest("JSON inválido")
    except User.DoesNotExist:
        return HttpResponseNotFound("Usuário não encontrado")
    except Product.DoesNotExist:
        return HttpResponseNotFound("Produto não encontrado")
    except ValueError as e:
        return HttpResponseBadRequest(str(e))
    except Exception as e:
        return HttpResponseBadRequest(f"Erro interno: {e}")


# GET /api/alerts/
@csrf_exempt
@require_GET
def list_alerts_view(request):
    try:
        lst = get_all_alerts()
        if not lst:
            return HttpResponseNotFound("Nenhum alert cadastrado")
        return JsonResponse({"alerts": lst}, safe=False, status=200)
    except Exception as e:
        return HttpResponseBadRequest(f"Erro interno: {e}")


# GET /api/alerts/<id>/
@csrf_exempt
@require_GET
def get_alert_view(request, alert_id):
    try:
        data = get_alert_by_id(alert_id)
        return JsonResponse(data, status=200)
    except Alert.DoesNotExist:
        return HttpResponseNotFound("Alert não encontrado")
    except Exception as e:
        return HttpResponseBadRequest(f"Erro interno: {e}")


# PUT /api/alerts/update/<id>/
@csrf_exempt
def update_alert_view(request, alert_id):
    if request.method not in ["POST", "PUT"]:
        return HttpResponseNotAllowed(["POST", "PUT"])
    try:
        data = json.loads(request.body)

        # converte dates se existirem
        if "expires_at" in data:
            try:
                data["expires_at"] = datetime.strptime(
                    data["expires_at"], "%Y-%m-%d"
                ).date()
            except (TypeError, ValueError):
                return HttpResponseBadRequest("expires_at deve ser YYYY-MM-DD")
        if "created_at" in data:
            try:
                data["created_at"] = datetime.strptime(
                    data["created_at"], "%Y-%m-%d"
                ).date()
            except (TypeError, ValueError):
                return HttpResponseBadRequest("created_at deve ser YYYY-MM-DD")

        a = update_alert(alert_id, **data)
        return JsonResponse({
            "id":            a.id,
            "user":          a.user.id,
            "product":       a.product.id,
            "desired_price": str(a.desired_price),
            "is_active":     a.is_active,
            "expires_at":    a.expires_at.isoformat(),
            "created_at":    a.created_at.isoformat(),
        }, status=200)

    except json.JSONDecodeError:
        return HttpResponseBadRequest("JSON inválido")
    except Alert.DoesNotExist:
        return HttpResponseNotFound("Alert não encontrado")
    except ValueError as e:
        return HttpResponseBadRequest(str(e))
    except Exception as e:
        return HttpResponseBadRequest(f"Erro interno: {e}")


# DELETE /api/alerts/delete/<id>/
@csrf_exempt
def delete_alert_view(request, alert_id):
    if request.method != "DELETE":
        return HttpResponseNotAllowed(["DELETE"])
    try:
        msg = delete_alert(alert_id)
        return JsonResponse({"message": msg}, status=200)
    except Alert.DoesNotExist:
        return HttpResponseNotFound("Alert não encontrado")
    except Exception as e:
        return HttpResponseBadRequest(f"Erro interno: {e}")
