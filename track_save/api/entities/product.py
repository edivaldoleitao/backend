from django.db import models


class Store(models.Model):
    name = models.CharField(max_length=255)
    url_base = models.TextField()

    class Meta:
        app_label = "api"

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=255)
    specification = models.TextField()
    image_url = models.TextField()
    category = models.IntegerField()

    class Meta:
        app_label = "api"

    def __str__(self):
        return self.name


class ProductStore(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    url_product = models.TextField()
    available = models.BooleanField()

    class Meta:
        app_label = "api"

    def __str__(self):
        return f"{self.product.name} - {self.store.name}"
