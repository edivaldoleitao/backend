from django.db import models

from api.entities.user import User
from api.entities.product import Product


class List(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    created_at = models.DateField()

    class Meta:
        app_label = 'api' 

    def __str__(self):
        return self.name


class ProductList(models.Model):
    list = models.ForeignKey(List, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    desired_price = models.DecimalField(max_digits=8, decimal_places=2)
    receive_alert = models.BooleanField()

    class Meta:
        app_label = 'api' 

    def __str__(self):
        return f"{self.product.name} in list {self.list.name}"


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    created_at = models.DateField()

    class Meta:
        app_label = 'api' 

    def __str__(self):
        return f"{self.product.name} - {self.user.email}"

class FavoriteCategories(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.IntegerField()

    class Meta:
        app_label = 'api' 

    def __str__(self):
        return f"Category {self.category} for {self.user.email}"
