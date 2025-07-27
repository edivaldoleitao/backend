import os

from api.controllers.user_controller import get_user_by_id
from api.entities.preference import Preference
from api.entities.price import Price
from api.entities.product import Product
from api.entities.product import ProductStore
from django.core.mail import send_mail
from django.template.loader import render_to_string


def create_preference(id_user, marca, orcamento, build_ids):
    try:
        user = get_user_by_id(id_user)
        preference = Preference.objects.create(
            user=user, marca=marca, orcamento=orcamento
        )
        if build_ids:
            products = Product.objects.filter(id__in=build_ids)
            preference.build.set(products)
        check_and_send_preference_alerts(preference)
        return preference
    except Exception as e:
        print(e)
        return None


def get_preferences():
    return Preference.objects.all()


def update_preference_orcamento(preference_id, novo_orcamento):
    try:
        preference = Preference.objects.get(id=preference_id)
        preference.orcamento = novo_orcamento
        preference.save()
        # Após atualizar, verifica preços e dispara e-mails
        check_and_send_preference_alerts(preference)
        return preference
    except Preference.DoesNotExist:
        print("Preference não encontrado")
        return None


def check_and_send_preference_alerts(preference):
    """Verifica produtos na build e dispara e-mail se algum estiver dentro do orçamento."""
    marcas_preferencia = (
        [m.lower() for m in preference.marca]
        if isinstance(preference.marca, list)
        else [preference.marca.lower()]
    )
    for product in preference.build.all():
        total_orcamento = float(preference.orcamento)
        product_store = ProductStore.objects.filter(product=product).first()
        if not product_store:
            continue

        if product.brand.lower() not in marcas_preferencia:
            continue

        latest_price = (
            Price.objects.filter(product_store=product_store)
            .order_by("-collection_date")
            .first()
        )
        if not latest_price:
            continue

        if float(latest_price.value) <= float(preference.orcamento):
            total_orcamento = total_orcamento - float(latest_price.value)
            if total_orcamento >= 0:
                send_preference_alert_email(
                    preference, product, latest_price, product_store
                )


def send_preference_alert_email(preference, product, latest_price, product_store):
    """Dispara e-mail quando um produto da preferência está dentro do orçamento."""
    user = preference.user
    context = {
        "user_name": user.name or user.email,
        "product_name": product.name,
        "product_image": product.image_url,
        "orcamento": str(preference.orcamento),
        "marca": product.brand,
        "current_price": str(latest_price.value),
        "url_product": product_store.url_product,
    }
    html_message = render_to_string("emails/alert_preference.html", context)
    send_mail(
        subject=f"Produto dentro do orçamento: {product.name}",
        message=f"O produto {product.name} está com o preço {latest_price.value}, dentro do seu orçamento de {preference.orcamento}.",
        recipient_list=[user.email],
        from_email=os.getenv("DEFAULT_FROM_EMAIL"),
        html_message=html_message,
    )
