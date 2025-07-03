from datetime import date

from api.entities.favorite import Favorite
from api.entities.product import Product
from api.entities.user import User


def create_favorite(user_id: int, product_id: int, created_at: date) -> Favorite:
    """
    Cria um novo Favorite.
    Raises:
      ValueError: se faltar campo ou já existir esse par user+product.
      User.DoesNotExist / Product.DoesNotExist: se IDs inválidos.
    """
    if not all([user_id, product_id, created_at]):
        raise ValueError("Os campos user_id, product_id e created_at são obrigatórios.")

    user = User.objects.get(id=user_id)
    product = Product.objects.get(id=product_id)

    # evita duplicatas
    if Favorite.objects.filter(user=user, product=product).exists():
        raise ValueError("Este produto já está nos favoritos deste usuário.")

    fav = Favorite.objects.create(user=user, product=product, created_at=created_at)
    return fav


def get_all_favorites() -> list[dict]:
    """
    Retorna lista de dicts com todos os favoritos.
    """
    out = []
    qs = Favorite.objects.select_related("user", "product").all()
    for f in qs:
        out.append(
            {
                "id": f.id,
                "user": f.user.id,
                "product": f.product.id,
                "created_at": f.created_at.isoformat(),
            }
        )
    return out


def get_favorite_by_id(fav_id: int) -> dict:
    """
    Retorna dict com os dados de um Favorite.
    Raises Favorite.DoesNotExist se não encontrar.
    """
    f = Favorite.objects.select_related("user", "product").get(id=fav_id)
    return {
        "id": f.id,
        "user": f.user.id,
        "product": f.product.id,
        "created_at": f.created_at.isoformat(),
    }


def update_favorite(fav_id: int, **data) -> Favorite:
    """
    Atualiza um Favorite existente.
    Campos aceitos: user_id, product_id, created_at.
    Raises:
      Favorite.DoesNotExist / User.DoesNotExist / Product.DoesNotExist
    """
    f = Favorite.objects.get(id=fav_id)

    if "user_id" in data:
        f.user = User.objects.get(id=data["user_id"])
    if "product_id" in data:
        f.product = Product.objects.get(id=data["product_id"])
    if "created_at" in data:
        f.created_at = data["created_at"]

    f.save()
    return f


def delete_favorite(fav_id: int) -> str:
    """
    Remove um Favorite.
    Raises Favorite.DoesNotExist se não existir.
    """
    f = Favorite.objects.get(id=fav_id)
    f.delete()
    return "Favorite removido com sucesso."
