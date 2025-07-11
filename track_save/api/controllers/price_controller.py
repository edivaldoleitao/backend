import datetime

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


def list_prices_by_product(product_id, number_of_days):
    data = Price.objects.filter(
        product_store__product_id=product_id,
        collection_date__gte=(
            datetime.date.today() - datetime.timedelta(days=float(number_of_days))
        ),
    ).order_by("collection_date")
    return data.values()
