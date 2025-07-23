from api.entities.favorite import Favorite
from api.entities.price import Price
from api.entities.product import ProductStore
from api.controllers.alert_controller import send_alert_triggered_email
from api.entities.alert import Alert


def create_price(product_store_id, value, collection_date):
    """
    Cria um novo registro de Price.
    Raises:
      ValueError: se faltar algum campo obrigatório.
      ProductStore.DoesNotExist: se o product_store_id não existir.
    """
    if not all([product_store_id, value, collection_date]):
        raise ValueError(
            "Os campos product_store_id, value e collection_date são obrigatórios."
        )

    ps = ProductStore.objects.get(id=product_store_id)
    price = Price.objects.create(
        product_store=ps, value=value, collection_date=collection_date
    )

    # Envia email de alerta para todos os alertas ativos desse produto
    alerts = Alert.objects.filter(product=ps.product, is_active=True)
    for alert in alerts:
        send_alert_triggered_email(alert)

    return price


def get_all_prices():
    """
    Retorna uma lista de dicts com todos os Prices.
    """
    lst = []
    for p in Price.objects.select_related("product_store").all():
        lst.append(
            {
                "product_store": p.product_store.id,
                "value": str(p.value),
                "collection_date": p.collection_date.isoformat(),
            }
        )
    return lst


def get_price_by_id(price_id):
    """
    Retorna um dict com os dados do Price solicitado.
    Raises:
      Price.DoesNotExist: se não encontrar.
    """
    p = Price.objects.get(id=price_id)
    return {
        "product_store": p.product_store.id,
        "value": str(p.value),
        "collection_date": p.collection_date.isoformat(),
    }


def get_price_by_ps(ps_id):
    """
    Retorna uma lista dos prices que possuem o mesmo product store
    """
    lst = [
        {
            "product_store": p.product_store.id,
            "value": str(p.value),
            "collection_date": p.collection_date.isoformat(),
        }
        for p in Price.objects.filter(product_store=ps_id).order_by("collection_date")
    ]
    return lst


def update_price(price_id, **data):
    """
    Atualiza um Price existente.
    Campos aceitos em data: product_store_id, value, collection_date.
    Raises:
      Price.DoesNotExist: se não encontrar.
      ProductStore.DoesNotExist: se product_store_id inválido.
    """
    p = Price.objects.get(id=price_id)

    if "product_store_id" in data:
        p.product_store = ProductStore.objects.get(id=data["product_store_id"])
    if "value" in data:
        p.value = data["value"]
    if "collection_date" in data:
        p.collection_date = data["collection_date"]

    p.save()
    return p


def delete_price(price_id):
    """
    Exclui o Price indicado.
    Raises:
      Price.DoesNotExist: se não encontrar.
    Returns:
      mensagem de confirmação.
    """
    p = Price.objects.get(id=price_id)
    p.delete()
    return "Price excluído com sucesso."


def get_all_prices_with_product(
    limit=None,
    offset=None,
    name=None,
    category=None,
    user_id=None,
    seller=None,
    rating=None,
    price_min=None,
    price_max=None,
    brand=None,
):
    data = []

    prices_query = Price.objects.select_related(
        "product_store__product", "product_store__store"
    )

    if name:
        prices_query = prices_query.filter(product_store__product__name__icontains=name)

    if category:
        prices_query = prices_query.filter(
            product_store__product__category__iexact=category
        )

    if seller:
        prices_query = prices_query.filter(product_store__store__name__icontains=seller)

    if rating:
        try:
            prices_query = prices_query.filter(product_store__rating__gte=float(rating))
        except ValueError:
            pass

    if price_min:
        try:
            prices_query = prices_query.filter(value__gte=float(price_min))
        except ValueError:
            pass

    if price_max:
        try:
            prices_query = prices_query.filter(value__lte=float(price_max))
        except ValueError:
            pass

    if brand:
        prices_query = prices_query.filter(
            product_store__product__brand__icontains=brand
        )
    total = prices_query.count()

    if offset:
        try:
            prices_query = prices_query[int(offset) :]
        except ValueError:
            pass

    if limit:
        try:
            prices_query = prices_query[: int(limit)]
        except ValueError:
            pass

    favorites = Favorite.objects.filter(user_id=user_id).only("id", "product_id")
    favorites_by_product = {int(fav.product_id): fav.id for fav in favorites}

    for price in prices_query:
        product = price.product_store.product
        store = price.product_store.store

        data.append(
            {
                "product_id": product.id,
                "name": product.name,
                "category": product.category,
                "brand": product.brand,
                "model": getattr(product, "model", None),
                "image_url": product.image_url,
                "rating": price.product_store.rating,
                "reviewCount": getattr(price.product_store, "review_count", 0),
                "favorite_id": favorites_by_product.get(product.id)
                if user_id
                else None,
                "store": {
                    "id": store.id,
                    "name": store.name,
                    "logo_url": getattr(store, "logo_url", ""),
                },
                "price": str(price.value),
                "price_id": price.id,
                "collection_date": price.collection_date.isoformat(),
            }
        )

    return {"products": data, "total": total}


def search_products_with_price_by_name(query: str):
    """
    Retorna uma lista de produtos com preço cujo nome contém a `query` (case-insensitive).
    """
    all_products = get_all_prices_with_product()
    return [p for p in all_products if query.lower() in p["name"].lower()]
