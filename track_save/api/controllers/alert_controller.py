import os

from api.entities.alert import Alert
from api.entities.price import Price
from api.entities.product import Product
from api.entities.product import ProductStore
from api.entities.user import User
from django.core.mail import send_mail
from django.db.models import F
from django.db.models import Sum
from django.template.loader import render_to_string


def create_alert(
    user_id: int, product_id: int, desired_price: str, expires_at, created_at
) -> Alert:
    if not all([user_id, product_id, desired_price, expires_at, created_at]):
        raise ValueError(
            "user_id, product_id, desired_price, expires_at e created_at são obrigatórios."
        )

    user = User.objects.get(id=user_id)
    product = Product.objects.get(id=product_id)

    alert = Alert.objects.create(
        user=user,
        product=product,
        desired_price=desired_price,
        is_active=True,
        expires_at=expires_at,
        created_at=created_at,
    )
    send_alert_triggered_email(alert)
    return alert


def get_all_alerts() -> list[dict]:
    out = []
    qs = Alert.objects.select_related("user", "product").all()
    for a in qs:
        out.append(
            {
                "id": a.id,
                "user": a.user.id,
                "product": a.product.id,
                "desired_price": str(a.desired_price),
                "is_active": a.is_active,
                "expires_at": a.expires_at.isoformat(),
                "created_at": a.created_at.isoformat(),
            }
        )
    return out


def get_alert_by_user(user_id: int, product_id: int) -> dict:
    """
    Checa se esse alerta existe, caso positivo ele retorna juntamente o indice
    """
    a = Alert.objects.filter(user=user_id, product=product_id).last()
    if a:
        return {
            "isAlert": True,
            "alert": {
                "id": a.id,
                "user": a.user.id,
                "product": a.product.id,
                "desired_price": str(a.desired_price),
                "is_active": a.is_active,
                "expires_at": a.expires_at.isoformat(),
                "created_at": a.created_at.isoformat(),
            },
        }

    return {
        "isAlert": False,
    }


def get_alert_by_only_user_id(user_id: int) -> dict:
    alerts = (
        Alert.objects.select_related("product", "user")
        .filter(user=user_id)
        .order_by("-created_at")
    )

    alert_list = []

    for alert in alerts:
        try:
            product_store = ProductStore.objects.filter(product=alert.product).first()
            latest_price = None
            url_product = None
            if product_store:
                latest_price = (
                    Price.objects.filter(product_store=product_store)
                    .order_by("-collection_date")
                    .first()
                )
                url_product = product_store.url_product

            current_price = str(latest_price.value) if latest_price else None

        except Exception as e:
            print(f"Erro ao buscar preço: {e}")
            current_price = None

        alert_list.append(
            {
                "id": alert.id,
                "user": alert.user.id,
                "product": {
                    "id": alert.product.id,
                    "name": alert.product.name,
                    "image": alert.product.image_url,
                    "current_price": current_price,
                    "url_product": url_product,
                },
                "desired_price": str(alert.desired_price),
                "is_active": alert.is_active,
                "expires_at": alert.expires_at.isoformat(),
                "created_at": alert.created_at.isoformat(),
            }
        )

    return {
        "isAlert": bool(alert_list),
        "alerts": alert_list,
    }


def get_alert_stats(user_id):
    alerts = Alert.objects.filter(user_id=user_id)

    active_count = alerts.filter(is_active=True).count()
    goals_hit = (
        alerts.filter(
            is_active=True, product__productstore__price__value__lte=F("desired_price")
        )
        .distinct()
        .count()
    )

    total_saving = (
        alerts.filter(
            product__productstore__price__value__lte=F("desired_price")
        ).aggregate(
            total=Sum(F("desired_price") - F("product__productstore__price__value"))
        )["total"]
        or 0
    )

    last_updated = Price.objects.latest("collection_date").collection_date

    return {
        "active_alerts": active_count,
        "goals_hit": goals_hit,
        "total_saving": str(total_saving),
        "last_updated": last_updated.isoformat(),
    }


def get_alert_by_id(alert_id: int) -> dict:
    a = Alert.objects.select_related("user", "product").get(id=alert_id)
    return {
        "id": a.id,
        "user": a.user.id,
        "product": a.product.id,
        "desired_price": str(a.desired_price),
        "is_active": a.is_active,
        "expires_at": a.expires_at.isoformat(),
        "created_at": a.created_at.isoformat(),
    }


def update_alert(alert_id: int, **data) -> Alert:
    """
    Campos possíveis em data:
      user_id, product_id, desired_price, is_active, expires_at, created_at
    """
    a = Alert.objects.get(id=alert_id)

    if "user_id" in data:
        a.user = User.objects.get(id=data["user_id"])
    if "product_id" in data:
        a.product = Product.objects.get(id=data["product_id"])
    if "desired_price" in data:
        a.desired_price = data["desired_price"]
    if "is_active" in data:
        a.is_active = data["is_active"]
    if "expires_at" in data:
        a.expires_at = data["expires_at"]
    if "created_at" in data:
        a.created_at = data["created_at"]

    a.save()
    send_alert_triggered_email(a)
    return a


def delete_alert(alert_id: int) -> str:
    a = Alert.objects.get(id=alert_id)
    a.delete()
    return "Alert removido com sucesso."


def send_alert_triggered_email(alert):
    user = alert.user
    product = alert.product
    # Busca ProductStore e preço atual
    product_store = ProductStore.objects.filter(product=product).first()
    url_product = product_store.url_product if product_store else None
    latest_price = None
    if product_store:
        latest_price = (
            Price.objects.filter(product_store=product_store)
            .order_by("-collection_date")
            .first()
        )
    current_price = str(latest_price.value) if latest_price else None

    # Só envia email se o preço atual for menor ou igual ao desejado
    if latest_price is None or float(latest_price.value) > float(alert.desired_price):
        return  # Não envia email

    context = {
        "user_name": user.name or user.email,
        "product_name": product.name,
        "product_image": product.image_url,
        "desired_price": str(alert.desired_price),
        "current_price": current_price,
        "url_product": url_product,
        "expires_at": alert.expires_at.isoformat(),
    }
    html_message = render_to_string("emails/alert_triggered.html", context)
    send_mail(
        subject=f"Alerta disparado: {product.name} chegou no preço desejado!",
        message=f"O produto {product.name} atingiu o preço desejado.",
        recipient_list=[user.email],
        from_email=os.getenv("DEFAULT_FROM_EMAIL"),
        html_message=html_message,
    )


def send_preference_alert_triggered_email(alert):
    user = alert.user
    product = alert.product
    # Busca ProductStore e preço atual
    product_store = ProductStore.objects.filter(product=product).first()
    url_product = product_store.url_product if product_store else None
    latest_price = None
    if product_store:
        latest_price = (
            Price.objects.filter(product_store=product_store)
            .order_by("-collection_date")
            .first()
        )
    current_price = str(latest_price.value) if latest_price else None

    # Só envia email se o preço atual for menor ou igual ao desejado
    if latest_price is None or float(latest_price.value) > float(alert.desired_price):
        return  # Não envia email

    context = {
        "user_name": user.name or user.email,
        "product_name": product.name,
        "product_image": product.image_url,
        "orcamento": str(alert.desired_price),
        "marca": product.brand,
        "current_price": current_price,
        "url_product": url_product,
    }
    html_message = render_to_string("emails/alert_triggered.html", context)
    send_mail(
        subject=f"Alerta disparado: {product.name} chegou no preço desejado!",
        message=f"O produto {product.name} atingiu o preço desejado.",
        recipient_list=[user.email],
        from_email=os.getenv("DEFAULT_FROM_EMAIL"),
        html_message=html_message,
    )
