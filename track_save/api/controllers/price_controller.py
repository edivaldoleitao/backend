from api.entities.price import Price
from api.entities.product import ProductStore


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


def get_all_prices_with_product():
    """
    Retorna uma lista de produtos com preços, loja e info do produto.
    """
    data = []

    prices = Price.objects.select_related(
        "product_store__product", "product_store__store"
    ).all()

    for price in prices:
        product = price.product_store.product
        store = price.product_store.store

        data.append(
            {
                "product_id": product.id,
                "name": product.name,
                "category": product.category,
                "brand": product.brand,
                "image_url": product.image_url,
                "store": {
                    "id": store.id,
                    "name": store.name,
                    "logo_url": store.logo_url if hasattr(store, "logo_url") else "",
                },
                "price": str(price.value),
                "collection_date": price.collection_date.isoformat(),
            }
        )

    return data


def search_products_with_price_by_name(query: str):
    """
    Retorna uma lista de produtos com preço cujo nome contém a `query` (case-insensitive).
    """
    all_products = get_all_prices_with_product()
    return [p for p in all_products if query.lower() in p["name"].lower()]
