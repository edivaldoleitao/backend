from django.contrib.postgres.fields import ArrayField
from django.contrib.auth.models import AbstractUser
from django.db import models

from api.entities.product import Product

class UserCategory(models.TextChoices):
    GAMER = 'gamer', 'Gamer'
    HOME_OFFICE = 'home_office', 'Home Office'
    ESTUDO = 'estudo', 'Estudo'

class User(AbstractUser):
    name = models.CharField(max_length=255, blank=True, null=True)
    
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    created_at = models.DateField(auto_now_add=True)
    is_verified = models.BooleanField()
    categories = ArrayField(
        models.CharField(max_length=20, choices=UserCategory.choices),
        blank=True,
        default=list
    ) # no poostgres a coluna 'categories' vai armazenar uma lista de strings

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

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
