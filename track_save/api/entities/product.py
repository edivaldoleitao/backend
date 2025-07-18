import hashlib

from django.db import models


class ProductCategory(models.TextChoices):
    COMPUTER = "computer", "Computer"
    KEYBOARD = "keyboard", "Keyboard"
    MOUSE = "mouse", "Mouse"
    MONITOR = "monitor", "Monitor"
    MOTHERBOARD = "motherboard", "Motherboard"
    RAM = "ram", "Ram"
    GPU = "gpu", "Gpu"
    CPU = "cpu", "Cpu"
    STORAGE = "storage", "Storage"


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
        choices=ProductCategory.choices,
    )
    description = models.TextField(blank=True, default="")
    image_url = models.TextField()
    brand = models.CharField(max_length=100, default="Generic Brand")
    # identificador para evitar repetição de produtos, é feito um hash com o nome e a url do produto  # noqa: E501
    hash = models.CharField(
        max_length=64,
        editable=False,
        unique=True,
        blank=True,
        null=True,
    )

    class Meta:
        app_label = "api"

    def __str__(self):
        return self.name

    def ensure_hash(self, url: str):
        """
        Gera e salva o hash se ainda não existir.
        Deve ser chamado sempre que você criar um ProductStore novo
        com uma nova URL para garantir que o produto recebe seu hash.
        """
        if not self.hash:
            base = f"{self.name}{url}"
            digest = hashlib.sha256(base.encode("utf-8")).hexdigest()
            self.hash = digest
            # só salva o campo hash para não clobber os outros
            self.save(update_fields=["hash"])


class ProductStore(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    rating = models.FloatField(default=0.0)  # avaliação média do produto
    url_product = models.TextField()
    available = models.BooleanField()

    class Meta:
        app_label = "api"

    def __str__(self):
        return f"{self.product.name} - {self.store.name}"

    def save(self, *args, **kwargs):
        # Garante que o hash do produto é gerado com a URL do produto
        self.product.ensure_hash(self.url_product)

        # Salva o produto
        super().save(*args, **kwargs)


# TABELAS ESPECÍFICAS


class Motherboard(models.Model):
    prod = models.OneToOneField(Product, on_delete=models.CASCADE)
    model = models.CharField(max_length=255, default="Generic Model")
    socket = models.CharField(max_length=50)
    chipset = models.CharField(max_length=100)
    form_type = models.CharField(max_length=50, blank=True, default="")  # atx, itx
    max_ram_capacity = models.CharField(max_length=255, blank=True, default="")
    ram_type = models.CharField(max_length=10, blank=True, default="")
    ram_slots = models.CharField(max_length=255, blank=True, default="")
    pcie_slots = models.CharField(max_length=255, blank=True, default="")
    sata_ports = models.CharField(max_length=255, blank=True, default="")
    m2_slot = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        app_label = "api"
        
        indexes = [
        models.Index(fields=["socket", "form_type", "ram_type"]),
        ]

    def __str__(self):
        return f"Motherboard for {self.prod.name}"


class Gpu(models.Model):
    prod = models.OneToOneField(Product, on_delete=models.CASCADE)
    model = models.CharField(max_length=255)
    vram = models.CharField(max_length=255)
    chipset = models.CharField(max_length=255)
    max_resolution = models.CharField(max_length=255, blank=True, default="")
    output = models.CharField(max_length=255, blank=True, default="")  # HDMI, VGA etc
    tech_support = models.TextField(blank=True, default="")  # DLSS, Ray Tracing etc

    class Meta:
        app_label = "api"
        
        indexes = [
        models.Index(fields=["vram"]),
        ]

    def __str__(self):
        return f"Gpu for {self.prod.name}"


class Keyboard(models.Model):
    prod = models.OneToOneField(Product, on_delete=models.CASCADE)
    model = models.CharField(max_length=255)
    key_type = models.CharField(max_length=255, blank=True, default="")
    layout = models.CharField(max_length=255, blank=True, default="")
    connectivity = models.CharField(max_length=255, blank=True, default="")
    dimension = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        app_label = "api"
        
        indexes = [
        models.Index(fields=["key_type"]),
        ]

    def __str__(self):
        return f"Keyboard for {self.prod.name}"


class Cpu(models.Model):
    prod = models.OneToOneField(Product, on_delete=models.CASCADE)
    model = models.CharField(max_length=255)
    integrated_video = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )  # se tiver, qual é
    socket = models.CharField(max_length=255, blank=True, default="")
    core_number = models.CharField(max_length=255, blank=True, default="")
    thread_number = models.CharField(max_length=255, blank=True, default="")
    frequency = models.CharField(max_length=255, blank=True, default="")  # freq. da cpu
    mem_speed = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )  # freq. máx de memória suportada

    class Meta:
        app_label = "api"
        
        indexes = [
        models.Index(fields=["core_number", "frequency"]),
        ]

    def __str__(self):
        return f"CPU for {self.prod.name}"


class Mouse(models.Model):
    prod = models.OneToOneField(Product, on_delete=models.CASCADE)
    model = models.CharField(max_length=255)
    dpi = models.CharField(max_length=255, blank=True, default="")
    connectivity = models.CharField(max_length=255, blank=True, default="")
    color = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        app_label = "api"
        
        indexes = [
            models.Index(fields=["connectivity"]),
        ]

    def __str__(self):
        return f"Mouse for {self.prod.name}"


class Monitor(models.Model):
    prod = models.OneToOneField(Product, on_delete=models.CASCADE)
    model = models.CharField(max_length=255)
    inches = models.CharField(max_length=255, blank=True, default="")
    panel_type = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )  # ips, led etc
    proportion = models.CharField(max_length=255, blank=True, default="")
    resolution = models.CharField(max_length=255, blank=True, default="")
    refresh_rate = models.CharField(max_length=255, blank=True, default="60hz")
    color_support = models.CharField(max_length=255, blank=True, default="")
    output = models.CharField(max_length=255)  # HDMI, VGA etc

    class Meta:
        app_label = "api"
        
        indexes = [
            models.Index(fields=["panel_type", "inches", "refresh_rate"]),
        ]

    def __str__(self):
        return f"Monitor for {self.prod.name}"


class Ram(models.Model):
    prod = models.OneToOneField(Product, on_delete=models.CASCADE)
    model = models.CharField(max_length=255)
    capacity = models.CharField(max_length=255)
    ddr = models.CharField(max_length=255, blank=True, default="")
    speed = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        app_label = "api"
        
        indexes = [
            models.Index(fields=["speed", "ddr"]),
        ]

    def __str__(self):
        return f"RAM for {self.prod.name}"


class Computer(models.Model):
    prod = models.OneToOneField(Product, on_delete=models.CASCADE)
    is_notebook = models.BooleanField()
    motherboard = models.CharField(max_length=100)
    cpu = models.CharField(max_length=100)
    ram = models.CharField(max_length=100)
    storage = models.CharField(max_length=100)
    gpu = models.CharField(
        max_length=100,
        blank=True,
        default="",
    )  # se não tiver dedicada deve ser o vídedo integrado
    # características de tela
    inches = models.CharField(max_length=50, blank=True, default="")
    panel_type = models.CharField(max_length=50, blank=True, default="")
    resolution = models.CharField(max_length=50, blank=True, default="")
    refresh_rate = models.CharField(max_length=50, blank=True, default="")
    color_support = models.CharField(max_length=50, blank=True, default="")
    output = models.CharField(max_length=50, blank=True, default="")  # HDMI, VGA etc

    class Meta:
        app_label = "api"
        
        indexes = [
            models.Index(fields=["cpu", "gpu", "ram", "panel_type"]),
        ]

    def __str__(self):
        return f"{self.prod.name} ({'Notebook' if self.is_notebook else 'Desktop'})"


class Storage(models.Model):
    # relacionamento 1-1 com o produto "base"
    prod = models.OneToOneField(
        Product,
        on_delete=models.CASCADE,
        related_name="storage",
    )

    # campos específicos de Storage
    capacity_gb = models.CharField(max_length=255, help_text="Capacidade em GB")
    storage_type = models.CharField(
        max_length=255,
        choices=[("HDD", "HDD"), ("SSD", "SSD"), ("NVMe", "NVMe")],
    )
    interface = models.CharField(
        max_length=255,
        choices=[("SATA", "SATA"), ("PCIe", "PCIe"), ("USB", "USB")],
    )
    form_factor = models.CharField(max_length=255, help_text="Ex: 2.5, 3.5, M.2")
    read_speed = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Velocidade de leitura em MB/s (opcional)",
    )
    write_speed = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Velocidade de gravação em MB/s (opcional)",
    )

    class Meta:
        app_label = "api"
        verbose_name = "Storage"
        verbose_name_plural = "Storages"
        
        indexes = [
        models.Index(fields=["capacity_gb", "storage_type"]),
        ]

    def __str__(self):
        return f"{self.prod.name} - {self.capacity_gb}GB {self.storage_type}"
