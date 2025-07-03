
from django.db import models

class ProductCategory(models.TextChoices):
    COMPUTER = 'computer', 'Computer'
    KEYBOARD = 'keyboard', 'Keyboard'
    MOUSE = 'mouse', 'Mouse'
    MONITOR = 'monitor', 'Monitor'
    MOTHERBOARD = 'motherboard', 'Motherboard'
    RAM = 'ram', 'Ram'
    GPU = 'gpu', 'Gpu'
    CPU = 'cpu', 'Cpu'
    STORAGE = 'storage', 'Storage'


class Store(models.Model):
    name = models.CharField(max_length=255)
    url_base = models.TextField()
    is_sponsor = models.BooleanField(default=False)

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
    # identificador para evitar repetição de produtos, composto por nome + url do produto
    hash = models.TextField(editable=False, unique=True, blank=True, null=True)


    class Meta:
        app_label = "api"

    def __str__(self):
        return self.name


class ProductStore(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    rating = models.FloatField(default=0.0) # avaliação média do produto
    url_product = models.TextField()
    available = models.BooleanField()

    class Meta:
        app_label = "api"

    def __str__(self):
        return f"{self.product.name} - {self.store.name}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if not self.product.hash:
            self.product.hash = self.product.name + self.url_product
            self.product.save()


# TABELAS ESPECÍFICAS

class Motherboard(models.Model):
    prod = models.OneToOneField(Product, on_delete=models.CASCADE)
    model = models.CharField(max_length=255, default="Generic Model")
    socket = models.CharField(max_length=50)
    chipset = models.CharField(max_length=100)
    form_type = models.CharField(max_length=50) # atx, itx
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
    
class Storage(models.Model):
    # relacionamento 1-1 com o produto "base"
    prod = models.OneToOneField(Product,on_delete=models.CASCADE,related_name='storage')

    # campos específicos de Storage
    capacity_gb    = models.IntegerField(help_text="Capacidade em GB")
    storage_type   = models.CharField(max_length=20,choices=[('HDD', 'HDD'),('SSD', 'SSD'),('NVMe', 'NVMe')])
    interface      = models.CharField(max_length=20,choices=[('SATA', 'SATA'),('PCIe', 'PCIe'),('USB', 'USB')])
    form_factor    = models.CharField(max_length=20,help_text="Ex: 2.5, 3.5, M.2")
    read_speed     = models.IntegerField(null=True, blank=True,help_text="Velocidade de leitura em MB/s (opcional)")
    write_speed    = models.IntegerField(null=True, blank=True,help_text="Velocidade de gravação em MB/s (opcional)")

    class Meta:
        app_label = "api"
        verbose_name = "Storage"
        verbose_name_plural = "Storages"

    def __str__(self):
        return f"{self.prod.name} – {self.capacity_gb}GB {self.storage_type}"
