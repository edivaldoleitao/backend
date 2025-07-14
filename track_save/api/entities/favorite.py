from api.entities.product import Product
from api.entities.user import User
from django.db import models


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    created_at = models.DateField()

    class Meta:
        app_label = "api"

    def __str__(self):
        return f"{self.product.name} - {self.user.email}"
