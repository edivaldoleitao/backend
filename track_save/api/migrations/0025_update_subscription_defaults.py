from django.db import migrations

def preencher_subscription_fields(apps, schema_editor):
    Subscription = apps.get_model("api", "Subscription")

    Subscription.objects.filter(type="basic").update(
        title="Basic",
        description="A versão gratuita do Track&Save, com recursos limitados.",
        value=0.0,
    )
    Subscription.objects.filter(type="standard").update(
        title="Standard",
        description="Versão padrão para usuários que adoram procurar ofertas e interagir mais com o TrackBot.",
        value=7.90,
    )
    Subscription.objects.filter(type="premium").update(
        title="Premium",
        description="Versão premium para usuários que querem aproveitar ao máximo o Track&Save.",
        value=14.90,
    )

class Migration(migrations.Migration):

    dependencies = [
        ('api', '0024_subscription_description_subscription_title'),
    ]

    operations = [
        migrations.RunPython(preencher_subscription_fields),
    ]
