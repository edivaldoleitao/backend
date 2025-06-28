
from django.db import models

class ProductCategory(models.TextChoices):
    COMPUTER = 'computer', 'Computer'
    KEYBOARD = 'keyboard', 'Keyboard'
    MOUSE = 'mouse', 'Mouse'
    MONITOR = 'monitor', 'Monitor'
    MOTHERBOARD = 'motherboard', 'Motherboard'
    RAM = 'ram', 'Ram'
    GPU = 'gpu', 'Gpu'


class Store(models.Model):
    name = models.CharField(max_length=255)
    url_base = models.TextField()
    is_sponsor = models.BooleanField()

    class Meta:
        app_label = "api"

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=255)
    category = models.CharField(
        max_length=20,
        choices=ProductCategory.choices
    )
    description = models.TextField()
    image_url = models.TextField()
    brand = models.CharField(max_length=100, default="Generic Brand")


    class Meta:
        app_label = "api"

    def __str__(self):
        return self.name


class ProductStore(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    rating = models.FloatField() # avaliação média do produto
    url_product = models.TextField()
    available = models.BooleanField()

    class Meta:
        app_label = "api"

    def __str__(self):
        return f"{self.product.name} - {self.store.name}"

# TABELAS ESPECÍFICAS

class Motherboard(models.Model):
    prod = models.OneToOneField(Product, on_delete=models.CASCADE)
    socket = models.CharField(max_length=50)
    chipset = models.CharField(max_length=100)
    form_type = models.CharField(max_length=50) # (atx, itx)
    max_ram_capacity = models.IntegerField()
    ram_type = models.CharField(max_length=10)
    ram_slots = models.IntegerField()
    pcie_slots = models.PositiveIntegerField()
    sata_ports = models.IntegerField()
    m2_slot = models.IntegerField()

    class Meta:
        app_label = "api"

    def __str__(self):
        return f"Motherboard for {self.prod.name}"


class Gpu(models.Model):
    prod = models.OneToOneField(Product, on_delete=models.CASCADE)
    model = models.CharField(max_length=255)
    vram = models.IntegerField()
    chipset = models.CharField(max_length=255)
    max_resolution = models.CharField(max_length=255)
    output = models.CharField(max_length=255) # HDMI, VGA etc
    tech_support = models.TextField() # DLSS, Ray Tracing etc

    class Meta:
        app_label = "api"

    def __str__(self):
        return f"Gpu for {self.prod.name}"


class Keyboard(models.Model):
    prod = models.OneToOneField(Product, on_delete=models.CASCADE)
    model = models.CharField(max_length=255)
    key_type = models.CharField(max_length=255)
    layout = models.CharField(max_length=255)
    connectivity = models.CharField(max_length=255)
    dimension = models.CharField(max_length=255)

    class Meta:
        app_label = "api"

    def __str__(self):
        return f"Keyboard for {self.prod.name}"


class Cpu(models.Model):
    prod = models.OneToOneField(Product, on_delete=models.CASCADE)
    model = models.CharField(max_length=255)
    integrated_video = models.CharField(max_length=255) # se tiver, qual é
    socket = models.CharField(max_length=255)
    core_number = models.IntegerField()
    thread_number = models.IntegerField()
    frequency = models.FloatField() # freq. da cpu
    mem_speed = models.FloatField() # freq. máx de memória suportada

    class Meta:
        app_label = "api"

    def __str__(self):
        return f"CPU for {self.prod.name}"


class Mouse(models.Model):
    prod = models.OneToOneField(Product, on_delete=models.CASCADE)
    model = models.CharField(max_length=255)
    brand = models.CharField(max_length=255)
    dpi = models.IntegerField()
    connectivity = models.CharField(max_length=255)
    color = models.CharField(max_length=255)

    class Meta:
        app_label = "api"

    def __str__(self):
        return f"Mouse for {self.prod.name}"


class Monitor(models.Model):
    prod = models.OneToOneField(Product, on_delete=models.CASCADE)
    model = models.CharField(max_length=255)
    inches = models.FloatField()
    panel_type = models.CharField(max_length=255) # ips, led etc
    proportion = models.CharField(max_length=255)
    resolution = models.CharField(max_length=255)
    refresh_rate = models.CharField(max_length=255)
    color_support = models.CharField(max_length=255)
    output = models.CharField(max_length=255) # HDMI, VGA etc

    class Meta:
        app_label = "api"

    def __str__(self):
        return f"Monitor for {self.prod.name}"


class Ram(models.Model):
    prod = models.OneToOneField(Product, on_delete=models.CASCADE)
    brand = models.CharField(max_length=255)
    model = models.CharField(max_length=255)
    capacity = models.FloatField()
    ddr = models.CharField(max_length=255)
    speed = models.FloatField()

    class Meta:
        app_label = "api"

    def __str__(self):
        return f"RAM for {self.prod.name}"

class Computer(models.Model):
    prod = models.OneToOneField(Product, on_delete=models.CASCADE)
    is_notebook = models.BooleanField()
    motherboard = models.CharField(max_length=100)
    cpu = models.CharField(max_length=100)
    ram =  models.IntegerField()
    storage =  models.IntegerField()
    gpu = models.CharField(max_length=100) # se não tiver dedicada deve ser o vídedo integrado
    # características de tela
    inches = models.FloatField()
    panel_type = models.CharField(max_length=50)
    resolution = models.CharField(max_length=50)
    refresh_rate = models.CharField(max_length=50)
    color_support = models.CharField(max_length=50)
    output = models.CharField(max_length=50) # HDMI, VGA etc

    class Meta:
        app_label = "api"

    def __str__(self):
        return f"{self.product.name} ({'Notebook' if self.is_notebook else 'Desktop'})"
