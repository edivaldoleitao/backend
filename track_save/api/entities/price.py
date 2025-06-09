from django.db import models

from api.entities.product import ProductStore

class Price(models.Model):
    product_store = models.ForeignKey(ProductStore, on_delete=models.CASCADE)
    value = models.DecimalField(max_digits=8, decimal_places=2)
    collection_date = models.DateField()

    class Meta:
        app_label = 'api' 

    def __str__(self):
        return f"{self.product_store.product.name} - {self.value}"
