from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import ArrayField
from django.db import models


class UserCategory(models.TextChoices):
    GAMER = "gamer", "Gamer"
    HOME_OFFICE = "home_office", "Home Office"
    ESTUDO = "estudo", "Estudo"


class User(AbstractUser):
    username = None  # pra não usar esse campo
    name = models.CharField(max_length=255, blank=True, default="")

    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    created_at = models.DateField(auto_now_add=True)
    is_verified = models.BooleanField()
    categories = ArrayField(
        models.CharField(max_length=20, choices=UserCategory.choices),
        blank=True,
        default=list,
    )  # no poostgres a coluna 'categories' vai armazenar uma lista de strings

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    class Meta:
        app_label = "api"

    def __str__(self):
        return self.email


class UserSpecification(models.Model):
    user_id = models.OneToOneField(User, on_delete=models.CASCADE)
    cpu = models.CharField(max_length=100)
    ram = models.CharField(max_length=100)
    motherboard = models.CharField(max_length=100)
    cooler = models.CharField(max_length=100, blank=True, default="")
    gpu = models.CharField(max_length=100, blank=True, default="")
    storage = models.CharField(max_length=100)
    psu = models.CharField(max_length=100, blank=True, default="")  # fonte

    class Meta:
        app_label = "api"

    def __str__(self):
        return str(self.user_id)
