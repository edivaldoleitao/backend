from django.db import models
from api.entities.user import User


class SubscriptionType(models.TextChoices):
    BASIC = "basic", "Basic"
    STANDARD = "standard", "Standard"
    PREMIUM = "premium", "Premium"


class Subscription(models.Model):
    type = models.CharField(max_length=10, choices=SubscriptionType.choices)
    title = models.CharField(max_length=10, default="")
    description = models.CharField(max_length=255, default="")
    favorite_quantity = models.IntegerField(default=5)
    alert_quantity = models.IntegerField(default=1)
    interactions_quantity = models.IntegerField(default=5)
    price_htr_quantity = models.IntegerField(default=1)
    value = models.FloatField(default=0.0)

    class Meta:
        app_label = "api"

    def __str__(self):
        return self.type


class SubscriptionUser(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        app_label = "api"

    def __str__(self):
        return f"{self.user.email} - {self.subscription.type}"
