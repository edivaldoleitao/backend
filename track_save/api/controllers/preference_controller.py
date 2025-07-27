from api.controllers.user_controller import get_user_by_id
from api.entities.preference import Preference
from api.entities.product import Product


def create_preference(id_user, marca, orcamento, build_ids):
    try:
        user = get_user_by_id(id_user)
        preference = Preference.objects.create(
            user=user, marca=marca, orcamento=orcamento
        )
        if build_ids:
            products = Product.objects.filter(id__in=build_ids)
            preference.build.set(products)
        return preference
    except Exception as e:
        print(e)
        return None


def get_preferences():
    return Preference.objects.all()
