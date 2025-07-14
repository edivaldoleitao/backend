from api.entities.product import Product
from api.entities.user import User
from django.db import models


class Alert(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    desired_price = models.DecimalField(max_digits=8, decimal_places=2)
    is_active = models.BooleanField(default=True)
    expires_at = models.DateField()
    created_at = models.DateField()

    class Meta:
        app_label = "api"

    def __str__(self):
        return f"Alert for {self.product.name} - {self.user.email}"
