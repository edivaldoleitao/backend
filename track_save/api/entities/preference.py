from api.entities.product import Product
from api.entities.user import User
from django.contrib.postgres.fields import ArrayField
from django.db import models


class Preference(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    marca = ArrayField(
        models.CharField(max_length=20),
        blank=True,
        default=list,
    )
    orcamento = models.DecimalField(max_digits=8, decimal_places=2)
    build = models.ManyToManyField(Product, blank=True)

    class Meta:
        app_label = "api"

    def __str__(self):
        return f"Preferencias - {self.user.email}"
