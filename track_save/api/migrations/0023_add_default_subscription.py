from django.db import migrations

def criar_assinaturas(apps, schema_editor):
    Subscription = apps.get_model("api", "Subscription")

    Subscription.objects.get_or_create(
        type="basic",
        defaults={
            "title": "Basic",
            "description": "A versão gratuita do Track&Save, com recursos limitados.",
            "favorite_quantity": 5,
            "alert_quantity": 1,
            "interactions_quantity": 5,
            "price_htr_quantity": 1,
            "value": 0.0,
        }
    )

    Subscription.objects.get_or_create(
        type="standard",
        defaults={
            "title": "Standard",
            "description": "Versão padrão para usuários que adoram procurar ofertas e interagir mais com o TrackBot.",
            "favorite_quantity": 50,
            "alert_quantity": 10,
            "interactions_quantity": 50,
            "price_htr_quantity": 10,
            "value": 7.90,
        }
    )

    Subscription.objects.get_or_create(
        type="premium",
        defaults={
            "title": "Premium",
            "description": "Versão premium para usuários que querem aproveitar ao máximo o Track&Save.",
            "favorite_quantity": 1000000,
            "alert_quantity": 1000000,
            "interactions_quantity": 1000000,
            "price_htr_quantity": 1000000,
            "value": 14.90,
        }
    )


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0022_subscription_subscriptionuser'),
    ]

    operations = [
        migrations.RunPython(criar_assinaturas),
    ]
