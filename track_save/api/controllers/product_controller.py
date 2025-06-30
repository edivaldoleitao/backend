from django.core.exceptions import ValidationError
from django.db import transaction

from api.entities.product import Computer
from api.entities.product import Cpu
from api.entities.product import Gpu
from api.entities.product import Keyboard
from api.entities.product import Monitor
from api.entities.product import Mouse
from api.entities.product import Product
from api.entities.product import ProductCategory
from api.entities.product import ProductStore
from api.entities.product import Ram
from api.entities.product import Store
from api.entities.user import Product


# no fim do código tem um exemplo do uso dessa função
def create_product(name, category, description, image_url, brand, **spec_fields):
    if not all([name, category, description, image_url, brand]):
        raise ValueError("Todos os campos são obrigatórios.")

    if Product.objects.filter(name=name).exists():
        raise ValueError("Este produto já foi cadastrado.")

    if category not in [choice[0] for choice in ProductCategory.choices]:
        raise ValueError("Categoria inválida.")

    with transaction.atomic():
        try:
            product = Product.objects.create(
                name=name,
                category=category,
                description=description,
                image_url=image_url,
                brand=brand,
            )

            if not product:
                raise ValueError("Erro ao criar o produto.")

        except Exception as e:
            raise ValueError(f"Erro ao criar produto: {str(e)}")

        try:
            match category:
                case "computer":
                    if "is_notebook" not in spec_fields:
                        raise ValueError(
                            "Campo 'is_notebook' é obrigatório para a categoria 'computer'."
                        )
                    Computer.objects.create(
                        prod=product,
                        is_notebook=spec_fields.get("is_notebook"),
                        motherboard=spec_fields.get("motherboard"),
                        cpu=spec_fields.get("cpu"),
                        ram=spec_fields.get("ram"),
                        storage=spec_fields.get("storage"),
                        gpu=spec_fields.get("gpu"),
                        inches=spec_fields.get("inches"),
                        panel_type=spec_fields.get("panel_type"),
                        resolution=spec_fields.get("resolution"),
                        refresh_rate=spec_fields.get("refresh_rate"),
                        color_support=spec_fields.get("color_support"),
                        output=spec_fields.get("output"),
                    )
                case "gpu":
                    Gpu.objects.create(
                        prod_id=product.id,
                        model=spec_fields.get("model"),
                        vram=spec_fields.get("vram"),
                        chipset=spec_fields.get("chipset"),
                        max_resolution=spec_fields.get("max_resolution"),
                        output=spec_fields.get("output"),
                        tech_support=spec_fields.get("tech_support"),
                    )
                case "keyboard":
                    Keyboard.objects.create(
                        prod_id=product.id,
                        model=spec_fields.get("model"),
                        key_type=spec_fields.get("key_type"),
                        layout=spec_fields.get("layout"),
                        connectivity=spec_fields.get("connectivity"),
                        dimension=spec_fields.get("dimension"),
                    )
                case "cpu":
                    Cpu.objects.create(
                        prod_id=product.id,
                        model=spec_fields.get("model"),
                        integrated_video=spec_fields.get("integrated_video"),
                        socket=spec_fields.get("socket"),
                        core_number=spec_fields.get("core_number"),
                        thread_number=spec_fields.get("thread_number"),
                        frequency=spec_fields.get("frequency"),
                        mem_speed=spec_fields.get("mem_speed"),
                    )
                case "mouse":
                    Mouse.objects.create(
                        prod_id=product.id,
                        model=spec_fields.get("model"),
                        brand=spec_fields.get("brand"),
                        dpi=spec_fields.get("dpi"),
                        connectivity=spec_fields.get("connectivity"),
                        color=spec_fields.get("color"),
                    )
                case "monitor":
                    Monitor.objects.create(
                        prod_id=product.id,
                        model=spec_fields.get("model"),
                        inches=spec_fields.get("inches"),
                        panel_type=spec_fields.get("panel_type"),
                        proportion=spec_fields.get("proportion"),
                        resolution=spec_fields.get("resolution"),
                        refresh_rate=spec_fields.get("refresh_rate"),
                        color_support=spec_fields.get("color_support"),
                        output=spec_fields.get("output"),
                    )
                case "ram":
                    Ram.objects.create(
                        prod_id=product.id,
                        brand=spec_fields.get("brand"),
                        model=spec_fields.get("model"),
                        capacity=spec_fields.get("capacity"),
                        ddr=spec_fields.get("ddr"),
                        speed=spec_fields.get("speed"),
                    )
                case _:
                    raise ValueError(f"Categorias não suportadas: {category}")

        except Exception as e:
            raise ValueError(f"Erro ao criar produto na categoria específica: {str(e)}")

    return product


# pra pegar produto pelo id
def get_product_by_id(product_id):
    try:
        product = Product.objects.get(id=product_id)

        product_data = {
            "name": product.name,
            "category": product.category,
            "description": product.description,
            "image_url": product.image_url,
            "brand": product.brand,
        }

        match product.category:
            case "computer":
                computer = Computer.objects.get(prod=product)
                product_data["specific_details"] = {
                    "is_notebook": computer.is_notebook,
                    "motherboard": computer.motherboard,
                    "cpu": computer.cpu,
                    "ram": computer.ram,
                    "storage": computer.storage,
                    "gpu": computer.gpu,
                    "inches": computer.inches,
                    "panel_type": computer.panel_type,
                    "resolution": computer.resolution,
                    "refresh_rate": computer.refresh_rate,
                    "color_support": computer.color_support,
                    "output": computer.output,
                }
            case "gpu":
                gpu = Gpu.objects.get(prod=product)
                product_data["specific_details"] = {
                    "model": gpu.model,
                    "vram": gpu.vram,
                    "chipset": gpu.chipset,
                    "max_resolution": gpu.max_resolution,
                    "output": gpu.output,
                    "tech_support": gpu.tech_support,
                }
            case "keyboard":
                keyboard = Keyboard.objects.get(prod=product)
                product_data["specific_details"] = {
                    "model": keyboard.model,
                    "key_type": keyboard.key_type,
                    "layout": keyboard.layout,
                    "connectivity": keyboard.connectivity,
                    "dimension": keyboard.dimension,
                }
            case "cpu":
                cpu = Cpu.objects.get(prod=product)
                product_data["specific_details"] = {
                    "model": cpu.model,
                    "integrated_video": cpu.integrated_video,
                    "socket": cpu.socket,
                    "core_number": cpu.core_number,
                    "thread_number": cpu.thread_number,
                    "frequency": cpu.frequency,
                    "mem_speed": cpu.mem_speed,
                }
            case "mouse":
                mouse = Mouse.objects.get(prod=product)
                product_data["specific_details"] = {
                    "model": mouse.model,
                    "brand": mouse.brand,
                    "dpi": mouse.dpi,
                    "connectivity": mouse.connectivity,
                    "color": mouse.color,
                }
            case "monitor":
                monitor = Monitor.objects.get(prod=product)
                product_data["specific_details"] = {
                    "model": monitor.model,
                    "inches": monitor.inches,
                    "panel_type": monitor.panel_type,
                    "proportion": monitor.proportion,
                    "resolution": monitor.resolution,
                    "refresh_rate": monitor.refresh_rate,
                    "color_support": monitor.color_support,
                    "output": monitor.output,
                }
            case "ram":
                ram = Ram.objects.get(prod=product)
                product_data["specific_details"] = {
                    "brand": ram.brand,
                    "model": ram.model,
                    "capacity": ram.capacity,
                    "ddr": ram.ddr,
                    "speed": ram.speed,
                }
            case _:
                product_data["category_error"] = "Categoria não existe"

        return product_data

    except Product.DoesNotExist:
        raise ValueError("Produto não encontrado.")
    except Exception as e:
        raise ValueError(f"Erro ao obter produto: {str(e)}")


# pra pegar produto pelo nome
def get_product_by_name(product_name):
    try:
        product = Product.objects.get(name=product_name)

        product_data = {
            "name": product.name,
            "category": product.category,
            "description": product.description,
            "image_url": product.image_url,
            "brand": product.brand,
        }

        match product.category:
            case "computer":
                computer = Computer.objects.get(prod=product)
                product_data["specific_details"] = {
                    "is_notebook": computer.is_notebook,
                    "motherboard": computer.motherboard,
                    "cpu": computer.cpu,
                    "ram": computer.ram,
                    "storage": computer.storage,
                    "gpu": computer.gpu,
                    "inches": computer.inches,
                    "panel_type": computer.panel_type,
                    "resolution": computer.resolution,
                    "refresh_rate": computer.refresh_rate,
                    "color_support": computer.color_support,
                    "output": computer.output,
                }
            case "gpu":
                gpu = Gpu.objects.get(prod=product)
                product_data["specific_details"] = {
                    "model": gpu.model,
                    "vram": gpu.vram,
                    "chipset": gpu.chipset,
                    "max_resolution": gpu.max_resolution,
                    "output": gpu.output,
                    "tech_support": gpu.tech_support,
                }
            case "keyboard":
                keyboard = Keyboard.objects.get(prod=product)
                product_data["specific_details"] = {
                    "model": keyboard.model,
                    "key_type": keyboard.key_type,
                    "layout": keyboard.layout,
                    "connectivity": keyboard.connectivity,
                    "dimension": keyboard.dimension,
                }
            case "cpu":
                cpu = Cpu.objects.get(prod=product)
                product_data["specific_details"] = {
                    "model": cpu.model,
                    "integrated_video": cpu.integrated_video,
                    "socket": cpu.socket,
                    "core_number": cpu.core_number,
                    "thread_number": cpu.thread_number,
                    "frequency": cpu.frequency,
                    "mem_speed": cpu.mem_speed,
                }
            case "mouse":
                mouse = Mouse.objects.get(prod=product)
                product_data["specific_details"] = {
                    "model": mouse.model,
                    "brand": mouse.brand,
                    "dpi": mouse.dpi,
                    "connectivity": mouse.connectivity,
                    "color": mouse.color,
                }
            case "monitor":
                monitor = Monitor.objects.get(prod=product)
                product_data["specific_details"] = {
                    "model": monitor.model,
                    "inches": monitor.inches,
                    "panel_type": monitor.panel_type,
                    "proportion": monitor.proportion,
                    "resolution": monitor.resolution,
                    "refresh_rate": monitor.refresh_rate,
                    "color_support": monitor.color_support,
                    "output": monitor.output,
                }
            case "ram":
                ram = Ram.objects.get(prod=product)
                product_data["specific_details"] = {
                    "brand": ram.brand,
                    "model": ram.model,
                    "capacity": ram.capacity,
                    "ddr": ram.ddr,
                    "speed": ram.speed,
                }
            case _:
                product_data["name_error"] = "Produto com este nome não existe"

        return product_data

    except Product.DoesNotExist:
        raise ValueError("Produto não encontrado.")
    except Exception as e:
        raise ValueError(f"Erro ao obter produto: {str(e)}")


# pra pegar produto pela categoria
def get_product_by_category(product_category):
    try:
        products = Product.objects.filter(category=product_category)

        if not products.exists():
            raise ValueError(f"Não há produtos na categoria: {product_category}")

        product_data_list = []

        for product in products:
            product_data = {
                "name": product.name,
                "category": product.category,
                "description": product.description,
                "image_url": product.image_url,
                "brand": product.brand,
            }

            match product.category:
                case "computer":
                    computer = Computer.objects.get(prod=product)
                    product_data["specific_details"] = {
                        "is_notebook": computer.is_notebook,
                        "motherboard": computer.motherboard,
                        "cpu": computer.cpu,
                        "ram": computer.ram,
                        "storage": computer.storage,
                        "gpu": computer.gpu,
                        "inches": computer.inches,
                        "panel_type": computer.panel_type,
                        "resolution": computer.resolution,
                        "refresh_rate": computer.refresh_rate,
                        "color_support": computer.color_support,
                        "output": computer.output,
                    }
                case "gpu":
                    gpu = Gpu.objects.get(prod_id=product)
                    product_data["specific_details"] = {
                        "model": gpu.model,
                        "vram": gpu.vram,
                        "chipset": gpu.chipset,
                        "max_resolution": gpu.max_resolution,
                        "output": gpu.output,
                        "tech_support": gpu.tech_support,
                    }
                case "keyboard":
                    keyboard = Keyboard.objects.get(prod_id=product)
                    product_data["specific_details"] = {
                        "model": keyboard.model,
                        "key_type": keyboard.key_type,
                        "layout": keyboard.layout,
                        "connectivity": keyboard.connectivity,
                        "dimension": keyboard.dimension,
                    }
                case "cpu":
                    cpu = Cpu.objects.get(prod_id=product)
                    product_data["specific_details"] = {
                        "model": cpu.model,
                        "integrated_video": cpu.integrated_video,
                        "socket": cpu.socket,
                        "core_number": cpu.core_number,
                        "thread_number": cpu.thread_number,
                        "frequency": cpu.frequency,
                        "mem_speed": cpu.mem_speed,
                    }
                case "mouse":
                    mouse = Mouse.objects.get(prod_id=product)
                    product_data["specific_details"] = {
                        "model": mouse.model,
                        "brand": mouse.brand,
                        "dpi": mouse.dpi,
                        "connectivity": mouse.connectivity,
                        "color": mouse.color,
                    }
                case "monitor":
                    monitor = Monitor.objects.get(prod_id=product)
                    product_data["specific_details"] = {
                        "model": monitor.model,
                        "inches": monitor.inches,
                        "panel_type": monitor.panel_type,
                        "proportion": monitor.proportion,
                        "resolution": monitor.resolution,
                        "refresh_rate": monitor.refresh_rate,
                        "color_support": monitor.color_support,
                        "output": monitor.output,
                    }
                case "ram":
                    ram = Ram.objects.get(prod_id=product)
                    product_data["specific_details"] = {
                        "brand": ram.brand,
                        "model": ram.model,
                        "capacity": ram.capacity,
                        "ddr": ram.ddr,
                        "speed": ram.speed,
                    }
                case _:
                    product_data["category_error"] = "Categoria não existe"

            product_data_list.append(product_data)

        return product_data_list

    except Exception as e:
        raise ValueError(f"Erro ao obter produtos: {str(e)}")


def get_all_products():
    try:
        products = Product.objects.all()

        if not products:
            raise ValueError(f"Não há produtos cadastrados")

        product_data_list = []

        for product in products:
            product_data = {
                "name": product.name,
                "category": product.category,
                "description": product.description,
                "image_url": product.image_url,
                "brand": product.brand,
            }

            try:
                match product.category:
                    case "computer":
                        computer = Computer.objects.get(prod=product)
                        product_data["specific_details"] = {
                            "is_notebook": computer.is_notebook,
                            "motherboard": computer.motherboard,
                            "cpu": computer.cpu,
                            "ram": computer.ram,
                            "storage": computer.storage,
                            "gpu": computer.gpu,
                            "inches": computer.inches,
                            "panel_type": computer.panel_type,
                            "resolution": computer.resolution,
                            "refresh_rate": computer.refresh_rate,
                            "color_support": computer.color_support,
                            "output": computer.output,
                        }
                    case "gpu":
                        gpu = Gpu.objects.get(prod_id=product)
                        product_data["specific_details"] = {
                            "model": gpu.model,
                            "vram": gpu.vram,
                            "chipset": gpu.chipset,
                            "max_resolution": gpu.max_resolution,
                            "output": gpu.output,
                            "tech_support": gpu.tech_support,
                        }
                    case "keyboard":
                        keyboard = Keyboard.objects.get(prod_id=product)
                        product_data["specific_details"] = {
                            "model": keyboard.model,
                            "key_type": keyboard.key_type,
                            "layout": keyboard.layout,
                            "connectivity": keyboard.connectivity,
                            "dimension": keyboard.dimension,
                        }
                    case "cpu":
                        cpu = Cpu.objects.get(prod_id=product)
                        product_data["specific_details"] = {
                            "model": cpu.model,
                            "integrated_video": cpu.integrated_video,
                            "socket": cpu.socket,
                            "core_number": cpu.core_number,
                            "thread_number": cpu.thread_number,
                            "frequency": cpu.frequency,
                            "mem_speed": cpu.mem_speed,
                        }
                    case "mouse":
                        mouse = Mouse.objects.get(prod_id=product)
                        product_data["specific_details"] = {
                            "model": mouse.model,
                            "brand": mouse.brand,
                            "dpi": mouse.dpi,
                            "connectivity": mouse.connectivity,
                            "color": mouse.color,
                        }
                    case "monitor":
                        monitor = Monitor.objects.get(prod_id=product)
                        product_data["specific_details"] = {
                            "model": monitor.model,
                            "inches": monitor.inches,
                            "panel_type": monitor.panel_type,
                            "proportion": monitor.proportion,
                            "resolution": monitor.resolution,
                            "refresh_rate": monitor.refresh_rate,
                            "color_support": monitor.color_support,
                            "output": monitor.output,
                        }
                    case "ram":
                        ram = Ram.objects.get(prod_id=product)
                        product_data["specific_details"] = {
                            "brand": ram.brand,
                            "model": ram.model,
                            "capacity": ram.capacity,
                            "ddr": ram.ddr,
                            "speed": ram.speed,
                        }
                    case _:
                        product_data["category_error"] = "Categoria não existe"

            except Exception as e:
                f"Erro ao carregar detalhes: {str(e)}"

            product_data_list.append(product_data)

        return product_data_list

    except Exception as e:
        raise ValueError(f"Erro ao obter produtos: {str(e)}")


def update_product(
    product_id,
    name=None,
    category=None,
    description=None,
    image_url=None,
    brand=None,
    **spec_fields,
):
    try:
        with transaction.atomic():
            product = Product.objects.get(id=product_id)

            if name:
                product.name = name
            if category:
                product.category = category
            if description:
                product.description = description
            if image_url:
                product.image_url = image_url
            if brand:
                product.brand = brand

            product.save()

            match product.category:
                case "computer":
                    computer = Computer.objects.get(prod=product)
                    computer.is_notebook = spec_fields.get(
                        "is_notebook", computer.is_notebook
                    )
                    computer.motherboard = spec_fields.get(
                        "motherboard", computer.motherboard
                    )
                    computer.cpu = spec_fields.get("cpu", computer.cpu)
                    computer.ram = spec_fields.get("ram", computer.ram)
                    computer.storage = spec_fields.get("storage", computer.storage)
                    computer.gpu = spec_fields.get("gpu", computer.gpu)
                    computer.inches = spec_fields.get("inches", computer.inches)
                    computer.panel_type = spec_fields.get(
                        "panel_type", computer.panel_type
                    )
                    computer.resolution = spec_fields.get(
                        "resolution", computer.resolution
                    )
                    computer.refresh_rate = spec_fields.get(
                        "refresh_rate", computer.refresh_rate
                    )
                    computer.color_support = spec_fields.get(
                        "color_support", computer.color_support
                    )
                    computer.output = spec_fields.get("output", computer.output)
                    computer.save()
                case "gpu":
                    gpu = Gpu.objects.get(prod=product)
                    gpu.model = spec_fields.get("model", gpu.model)
                    gpu.vram = spec_fields.get("vram", gpu.vram)
                    gpu.save()
                case "keyboard":
                    keyboard = Keyboard.objects.get(prod=product)
                    keyboard.model = spec_fields.get("model", keyboard.model)
                    keyboard.save()
                case "cpu":
                    cpu = Cpu.objects.get(prod=product)
                    cpu.model = spec_fields.get("model", cpu.model)
                    cpu.save()
                case "mouse":
                    mouse = Mouse.objects.get(prod=product)
                    mouse.model = spec_fields.get("model", mouse.model)
                    mouse.save()
                case "monitor":
                    monitor = Monitor.objects.get(prod=product)
                    monitor.model = spec_fields.get("model", monitor.model)
                    monitor.save()
                case "ram":
                    ram = Ram.objects.get(prod=product)
                    ram.model = spec_fields.get("model", ram.model)
                    ram.save()
                case _:
                    raise ValueError(f"Categoria desconhecida: {product.category}")

            return product

    except Product.DoesNotExist:
        raise ValueError("Produto não encontrado.")
    except Exception as e:
        raise ValueError(f"Erro ao atualizar produto: {str(e)}")


def delete_product(product_id):
    try:
        product = Product.objects.get(id=product_id)

        product.delete()

        return "Produto excluído com sucesso."

    except Product.DoesNotExist:
        raise ValueError("Produto não encontrado.")
    except Exception as e:
        raise ValueError(f"Erro ao excluir produto: {str(e)}")

    """
    data = {
        "name": "Gaming Laptop",
        "category": "computer",  # Categoria como "computer"
        "description": "A high-end gaming laptop with powerful specs.",
        "image_url": "https://example.com/laptop.jpg",
        "brand": "BrandX",
        # atributos específicos
        "is_notebook": True,
        "motherboard": "Model ABC",
        "cpu": "Intel i7",
        "ram": 16,
        "storage": 512,
        "gpu": "NVIDIA GTX 3060",
        "inches": 15.6,
        "panel_type": "IPS",
        "resolution": "1920x1080",
        "refresh_rate": "144Hz",
        "color_support": "16.7M",
        "output": "HDMI"
    }

    product = create_product(
        name=data["name"],
        category=data["category"],
        description=data["description"],
        image_url=data["image_url"],
        brand=data["brand"],
        **data  # Passa os campos específicos de categoria
    )
    """


def create_product_store(product_id, store_id, url_product, available):
    """
    Cria um novo ProductStore.
    Raises:
      ValueError: se faltar algum campo obrigatório.
      Product.DoesNotExist / Store.DoesNotExist: se product_id ou store_id não existirem.
    """
    # validação básica
    if not all([product_id, store_id, url_product]) or available is None:
        raise ValueError(
            "Todos os campos (product_id, store_id, url_product, available) são obrigatórios."
        )

    # busca as entidades relacionadas
    product = Product.objects.get(id=product_id)
    store = Store.objects.get(id=store_id)

    # cria e retorna
    ps = ProductStore.objects.create(
        product=product, store=store, url_product=url_product, available=available
    )
    return ps


def get_all_product_stores():
    """
    Retorna lista de dicts com todos os ProductStore.
    """
    lst = []
    for ps in ProductStore.objects.select_related("product", "store").all():
        lst.append(
            {
                "product": ps.product.id,
                "store": ps.store.id,
                "url_product": ps.url_product,
                "available": ps.available,
            }
        )
    return lst


def get_product_store_by_id(product_store_id):
    """
    Retorna dict com os dados do ProductStore solicitado.
    Raises:
      ProductStore.DoesNotExist se não existir.
    """
    ps = ProductStore.objects.get(id=product_store_id)
    return {
        "product": ps.product.id,
        "store": ps.store.id,
        "url_product": ps.url_product,
        "available": ps.available,
    }


def update_product_store(product_store_id, **data):
    """
    Atualiza campos de um ProductStore existente.
    Campos aceitos em data: product_id, store_id, url_product, available.
    Raises:
      ProductStore.DoesNotExist se não existir.
      Product.DoesNotExist / Store.DoesNotExist se IDs inválidos.
    """
    ps = ProductStore.objects.get(id=product_store_id)

    if "product_id" in data:
        ps.product = Product.objects.get(id=data["product_id"])
    if "store_id" in data:
        ps.store = Store.objects.get(id=data["store_id"])
    if "url_product" in data:
        ps.url_product = data["url_product"]
    if "available" in data:
        ps.available = data["available"]

    ps.save()
    return ps


def delete_product_store(product_store_id):
    """
    Exclui o ProductStore indicado.
    Raises:
      ProductStore.DoesNotExist se não existir.
    Returns mensagem de confirmação.
    """
    ps = ProductStore.objects.get(id=product_store_id)
    ps.delete()
    return "ProductStore excluído com sucesso."
