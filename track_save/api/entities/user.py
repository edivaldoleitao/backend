from django.contrib.auth.models import AbstractUser
from django.db import models

from api.entities.product import Product

class User(AbstractUser):
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    created_at = models.DateField()
    is_verified = models.BooleanField()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        app_label = 'api'

    def __str__(self):
        return self.email

class UserHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    created_at = models.DateField()

    class Meta:
        app_label = 'api' 

    def __str__(self):
        return f"{self.user.email} viewed {self.product.name}"
