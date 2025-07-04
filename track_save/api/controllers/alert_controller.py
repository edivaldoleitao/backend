from api.entities.alert import Alert
from api.entities.user import User
from api.entities.product import Product


def create_alert(user_id: int,
                 product_id: int,
                 desired_price: str,
                 expires_at,
                 created_at) -> Alert:
    if not all([user_id, product_id, desired_price, expires_at, created_at]):
        raise ValueError("user_id, product_id, desired_price, expires_at e created_at são obrigatórios.")

    user = User.objects.get(id=user_id)
    product = Product.objects.get(id=product_id)

    alert = Alert.objects.create(
        user=user,
        product=product,
        desired_price=desired_price,
        is_active=True,
        expires_at=expires_at,
        created_at=created_at
    )
    return alert


def get_all_alerts() -> list[dict]:
    out = []
    qs = Alert.objects.select_related("user", "product").all()
    for a in qs:
        out.append({
            "id":            a.id,
            "user":          a.user.id,
            "product":       a.product.id,
            "desired_price": str(a.desired_price),
            "is_active":     a.is_active,
            "expires_at":    a.expires_at.isoformat(),
            "created_at":    a.created_at.isoformat(),
        })
    return out


def get_alert_by_id(alert_id: int) -> dict:
    a = Alert.objects.select_related("user", "product").get(id=alert_id)
    return {
        "id":            a.id,
        "user":          a.user.id,
        "product":       a.product.id,
        "desired_price": str(a.desired_price),
        "is_active":     a.is_active,
        "expires_at":    a.expires_at.isoformat(),
        "created_at":    a.created_at.isoformat(),
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
    return a


def delete_alert(alert_id: int) -> str:
    a = Alert.objects.get(id=alert_id)
    a.delete()
    return "Alert removido com sucesso."
