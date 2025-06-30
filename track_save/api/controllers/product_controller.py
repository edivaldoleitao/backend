from api.entities.product import (Product, Store, ProductStore, ProductCategory, Gpu,
                                  Keyboard, Cpu, Mouse, Monitor, Ram, Computer)
from api.entities.price import Price
from api.entities.product import ProductCategory
from django.db import transaction
from django.db.models import Q, OuterRef, Subquery, Max, BooleanField, Exists
from django.db.models.functions import Coalesce


def create_store(name):
    if Store.objects.filter(name=name).exists():
        raise ValueError("Esta loja já foi cadastrada.")
    
    match name:
        case "Kabum":
            store = Store.objects.create(
                    name = name,
                    url_base = "https://www.kabum.com.br",
                    is_sponsor = False
                    )
        case "Terabyte":
            store = Store.objects.create(
                    name = name,
                    url_base = "https://www.terabyteshop.com.br",
                    is_sponsor = False
                    )
        case "Amazon":
            store = Store.objects.create(
                    name = name,
                    url_base = "https://www.amazon.com/?language=pt_BR",
                    is_sponsor = False
                    )
            
    return store

def get_stores():
    stores = Store.objects.all()
    
    if not stores:
        raise ValueError(f"Não há lojas cadastradas")
        
    lst = []
    for store in stores:
        
        store_data = {
        "name": store.name,
        "url_base": store.url_base,
        "is_sponsor": store.is_sponsor
        }
        
        lst.append(store_data)
        
    return lst
        
            
def update_store(name, url=None, is_sponsor=None):
    
    store = Store.objects.get(name=name)
    
    if url:
        store.url_base = url
    if is_sponsor:
        store.is_sponsor = is_sponsor
    
    return store

def delete_store(name):
    
    stores = Store.objects.filter(name=name)
    count, _ = stores.delete()
    return f"{count} loja(s) com nome '{name}' foram deletadas com sucesso."
    

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
                brand=brand
            )

            if not product:
                raise ValueError("Erro ao criar o produto.")

        except Exception as e:
            raise ValueError(f"Erro ao criar produto: {str(e)}")

        try:
            match category:
                case "computer":
                    if "is_notebook" not in spec_fields:
                        raise ValueError("Campo 'is_notebook' é obrigatório para a categoria 'computer'.")
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
                        output=spec_fields.get("output")
                    )
                case "gpu":
                    Gpu.objects.create(
                        prod=product,
                        model=spec_fields.get("model"),
                        vram=spec_fields.get("vram"),
                        chipset=spec_fields.get("chipset"),
                        max_resolution=spec_fields.get("max_resolution"),
                        output=spec_fields.get("output"),
                        tech_support=spec_fields.get("tech_support")
                    )
                case "keyboard":
                    Keyboard.objects.create(
                        prod=product,
                        model=spec_fields.get("model"),
                        key_type=spec_fields.get("key_type"),
                        layout=spec_fields.get("layout"),
                        connectivity=spec_fields.get("connectivity"),
                        dimension=spec_fields.get("dimension")
                    )
                case "cpu":
                    Cpu.objects.create(
                        prod=product,
                        model=spec_fields.get("model"),
                        integrated_video=spec_fields.get("integrated_video"),
                        socket=spec_fields.get("socket"),
                        core_number=spec_fields.get("core_number"),
                        thread_number=spec_fields.get("thread_number"),
                        frequency=spec_fields.get("frequency"),
                        mem_speed=spec_fields.get("mem_speed")
                    )
                case "mouse":
                    Mouse.objects.create(
                        prod=product,
                        model=spec_fields.get("model"),
                        brand=spec_fields.get("brand"),
                        dpi=spec_fields.get("dpi"),
                        connectivity=spec_fields.get("connectivity"),
                        color=spec_fields.get("color")
                    )
                case "monitor":
                    Monitor.objects.create(
                        prod=product,
                        model=spec_fields.get("model"),
                        inches=spec_fields.get("inches"),
                        panel_type=spec_fields.get("panel_type"),
                        proportion=spec_fields.get("proportion"),
                        resolution=spec_fields.get("resolution"),
                        refresh_rate=spec_fields.get("refresh_rate"),
                        color_support=spec_fields.get("color_support"),
                        output=spec_fields.get("output")
                    )
                case "ram":
                    Ram.objects.create(
                        prod=product,
                        brand=spec_fields.get("brand"),
                        model=spec_fields.get("model"),
                        capacity=spec_fields.get("capacity"),
                        ddr=spec_fields.get("ddr"),
                        speed=spec_fields.get("speed")
                    )
                case _:
                    raise ValueError(f"Categorias não suportadas: {category}")

        except Exception as e:
            raise ValueError(f"Erro ao criar produto na categoria específica: {str(e)}")
        
        # cria em ProductStore
        store = Store.objects.get(name=spec_fields.get("store"))
        
        try:
            product_store = ProductStore.objects.create(
                product = product,
                store = store,
                url_product = spec_fields.get("url"),
                available = spec_fields.get("available")
            )
            
        except Exception as e:
            raise ValueError(f"Erro ao inserir em ProductStore: {str(e)}")
        
        # cria em Price
        try:
            Price.objects.create(
                product_store = product_store,
                value = spec_fields.get("value"),
                collection_date = spec_fields.get("collection_date"),
            )
            
        except Exception as e:
            raise ValueError(f"Erro ao inserir em Price: {str(e)}")

    return product


def get_specific_details(product):
    try:
        match product.category:
            case "computer":
                p = Computer.objects.get(prod=product)
                return {
                    "is_notebook": p.is_notebook,
                    "motherboard": p.motherboard,
                    "cpu": p.cpu,
                    "ram": p.ram,
                    "storage": p.storage,
                    "gpu": p.gpu,
                    "inches": p.inches,
                    "panel_type": p.panel_type,
                    "resolution": p.resolution,
                    "refresh_rate": p.refresh_rate,
                    "color_support": p.color_support,
                    "output": p.output
                }
            case "gpu":
                p = Gpu.objects.get(prod=product)
                return {
                    "model": p.model,
                    "vram": p.vram,
                    "chipset": p.chipset,
                    "max_resolution": p.max_resolution,
                    "output": p.output,
                    "tech_support": p.tech_support
                }
            case "keyboard":
                p = Keyboard.objects.get(prod=product)
                return {
                    "model": p.model,
                    "key_type": p.key_type,
                    "layout": p.layout,
                    "connectivity": p.connectivity,
                    "dimension": p.dimension
                }
            case "cpu":
                p = Cpu.objects.get(prod=product)
                return {
                    "model": p.model,
                    "integrated_video": p.integrated_video,
                    "socket": p.socket,
                    "core_number": p.core_number,
                    "thread_number": p.thread_number,
                    "frequency": p.frequency,
                    "mem_speed": p.mem_speed
                }
            case "mouse":
                p = Mouse.objects.get(prod=product)
                return {
                    "model": p.model,
                    "brand": p.brand,
                    "dpi": p.dpi,
                    "connectivity": p.connectivity,
                    "color": p.color
                }
            case "monitor":
                p = Monitor.objects.get(prod=product)
                return {
                    "model": p.model,
                    "inches": p.inches,
                    "panel_type": p.panel_type,
                    "proportion": p.proportion,
                    "resolution": p.resolution,
                    "refresh_rate": p.refresh_rate,
                    "color_support": p.color_support,
                    "output": p.output
                }
            case "ram":
                p = Ram.objects.get(prod=product)
                return {
                    "brand": p.brand,
                    "model": p.model,
                    "capacity": p.capacity,
                    "ddr": p.ddr,
                    "speed": p.speed
                }
            case _:
                return {}
    except:
        return {}

"""
exemplo de uso
http://localhost:8001/api/products/search/?name=nvidia rtx 3080&brand=NVIDIA
http://localhost:8001/api/products/search/?brand=NVIDIA&category=gpu&price_min=2000&price_max=3000&store=Kabum
"""
def search_products(filters: dict):
    try:
        base_query = Q()

        if 'id' in filters:
            base_query &= Q(id=filters['id'])
        if 'name' in filters:
            base_query &= Q(name__icontains=filters['name'])
        if 'category' in filters:
            base_query &= Q(category__iexact=filters['category'])
        if 'brand' in filters:
            base_query &= Q(brand__icontains=filters['brand'])
        if 'store' in filters:
            base_query &= Q(productstore__store__name__icontains=filters['store'])

        # último preço coletado
        latest_price_subquery = Price.objects.filter(
            product_store__product=OuterRef('pk')
        ).order_by('-collection_date').values('value')[:1]

        # rating máximo entre as lojas
        rating_subquery = ProductStore.objects.filter(
            product=OuterRef('pk')
        ).order_by('-rating').values('rating')[:1]

        # se o produto pertence a alguma loja patrocinada
        sponsor_subquery = Store.objects.filter(
            productstore__product=OuterRef('pk'),
            is_sponsor=True
        )

        # produtos patrocinados
        sponsored_products = Product.objects.annotate(
            latest_price=Subquery(latest_price_subquery),
            rating=Subquery(rating_subquery),
            is_sponsored=Exists(sponsor_subquery)
        ).filter(base_query, is_sponsored=True)

        if 'price_min' in filters:
            sponsored_products = sponsored_products.filter(latest_price__gte=filters['price_min'])
        if 'price_max' in filters:
            sponsored_products = sponsored_products.filter(latest_price__lte=filters['price_max'])
        if 'rating_min' in filters:
            sponsored_products = sponsored_products.filter(rating__gte=filters['rating_min'])

        sponsored_products = sponsored_products.order_by('-rating')[:3]

        # produtos não patrocinados
        non_sponsored_products = Product.objects.annotate(
            latest_price=Subquery(latest_price_subquery),
            rating=Subquery(rating_subquery),
            is_sponsored=Exists(sponsor_subquery)
        ).filter(base_query, is_sponsored=False)

        if 'price_min' in filters:
            non_sponsored_products = non_sponsored_products.filter(latest_price__gte=filters['price_min'])
        if 'price_max' in filters:
            non_sponsored_products = non_sponsored_products.filter(latest_price__lte=filters['price_max'])
        if 'rating_min' in filters:
            non_sponsored_products = non_sponsored_products.filter(rating__gte=filters['rating_min'])

        non_sponsored_products = non_sponsored_products.order_by('-rating')

        # concatenar resultados
        final_products = list(sponsored_products) + list(non_sponsored_products)

        if not final_products:
            raise ValueError("Nenhum produto encontrado com os filtros fornecidos.")

        product_data_list = []
        for product in final_products:
            # tenta buscar a entrada de preço mais recente com loja associada
            latest_price_entry = Price.objects.filter(
                product_store__product=product
            ).order_by('-collection_date').select_related('product_store__store').first()

            if latest_price_entry:
                ps = latest_price_entry.product_store
                store_name = ps.store.name
                available = ps.available
                collection_date = latest_price_entry.collection_date
            else:
                store_name = None
                available = None

            product_data = {
                "id": product.id,
                "name": product.name,
                "category": product.category,
                "description": product.description,
                "image_url": product.image_url,
                "brand": product.brand,
                "rating": product.rating,
                "latest_price": product.latest_price,
                "is_sponsored": product.is_sponsored,
                "store": store_name,
                "available": available,
                "collection_date": collection_date,
                "specific_details": get_specific_details(product)
            }
            product_data_list.append(product_data)


        return product_data_list if len(product_data_list) > 1 else product_data_list[0]

    except Exception as e:
        raise ValueError(f"Erro ao buscar produto(s): {str(e)}")


# pra pegar produto pelo id
def get_product_by_id(product_id):
    try:
        product = Product.objects.get(id=product_id)

        product_data = {
            "id": product.id,
            "name": product.name,
            "category": product.category,
            "description": product.description,
            "image_url": product.image_url,
            "brand": product.brand
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
                    "output": computer.output
                }
            case "gpu":
                gpu = Gpu.objects.get(prod=product)
                product_data["specific_details"] = {
                    "model": gpu.model,
                    "vram": gpu.vram,
                    "chipset": gpu.chipset,
                    "max_resolution": gpu.max_resolution,
                    "output": gpu.output,
                    "tech_support": gpu.tech_support
                }
            case "keyboard":
                keyboard = Keyboard.objects.get(prod=product)
                product_data["specific_details"] = {
                    "model": keyboard.model,
                    "key_type": keyboard.key_type,
                    "layout": keyboard.layout,
                    "connectivity": keyboard.connectivity,
                    "dimension": keyboard.dimension
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
                    "mem_speed": cpu.mem_speed
                }
            case "mouse":
                mouse = Mouse.objects.get(prod=product)
                product_data["specific_details"] = {
                    "model": mouse.model,
                    "brand": mouse.brand,
                    "dpi": mouse.dpi,
                    "connectivity": mouse.connectivity,
                    "color": mouse.color
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
                    "output": monitor.output
                }
            case "ram":
                ram = Ram.objects.get(prod=product)
                product_data["specific_details"] = {
                    "brand": ram.brand,
                    "model": ram.model,
                    "capacity": ram.capacity,
                    "ddr": ram.ddr,
                    "speed": ram.speed
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
            "id": product.id,
            "name": product.name,
            "category": product.category,
            "description": product.description,
            "image_url": product.image_url,
            "brand": product.brand
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
                    "output": computer.output
                }
            case "gpu":
                gpu = Gpu.objects.get(prod=product)
                product_data["specific_details"] = {
                    "model": gpu.model,
                    "vram": gpu.vram,
                    "chipset": gpu.chipset,
                    "max_resolution": gpu.max_resolution,
                    "output": gpu.output,
                    "tech_support": gpu.tech_support
                }
            case "keyboard":
                keyboard = Keyboard.objects.get(prod=product)
                product_data["specific_details"] = {
                    "model": keyboard.model,
                    "key_type": keyboard.key_type,
                    "layout": keyboard.layout,
                    "connectivity": keyboard.connectivity,
                    "dimension": keyboard.dimension
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
                    "mem_speed": cpu.mem_speed
                }
            case "mouse":
                mouse = Mouse.objects.get(prod=product)
                product_data["specific_details"] = {
                    "model": mouse.model,
                    "brand": mouse.brand,
                    "dpi": mouse.dpi,
                    "connectivity": mouse.connectivity,
                    "color": mouse.color
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
                    "output": monitor.output
                }
            case "ram":
                ram = Ram.objects.get(prod=product)
                product_data["specific_details"] = {
                    "brand": ram.brand,
                    "model": ram.model,
                    "capacity": ram.capacity,
                    "ddr": ram.ddr,
                    "speed": ram.speed
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
                "id": product.id,
                "name": product.name,
                "category": product.category,
                "description": product.description,
                "image_url": product.image_url,
                "brand": product.brand
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
                        "output": computer.output
                    }
                case "gpu":
                    gpu = Gpu.objects.get(prod_id=product)
                    product_data["specific_details"] = {
                        "model": gpu.model,
                        "vram": gpu.vram,
                        "chipset": gpu.chipset,
                        "max_resolution": gpu.max_resolution,
                        "output": gpu.output,
                        "tech_support": gpu.tech_support
                    }
                case "keyboard":
                    keyboard = Keyboard.objects.get(prod_id=product)
                    product_data["specific_details"] = {
                        "model": keyboard.model,
                        "key_type": keyboard.key_type,
                        "layout": keyboard.layout,
                        "connectivity": keyboard.connectivity,
                        "dimension": keyboard.dimension
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
                        "mem_speed": cpu.mem_speed
                    }
                case "mouse":
                    mouse = Mouse.objects.get(prod_id=product)
                    product_data["specific_details"] = {
                        "model": mouse.model,
                        "brand": mouse.brand,
                        "dpi": mouse.dpi,
                        "connectivity": mouse.connectivity,
                        "color": mouse.color
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
                        "output": monitor.output
                    }
                case "ram":
                    ram = Ram.objects.get(prod_id=product)
                    product_data["specific_details"] = {
                        "brand": ram.brand,
                        "model": ram.model,
                        "capacity": ram.capacity,
                        "ddr": ram.ddr,
                        "speed": ram.speed
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
                "id": product.id,
                "name": product.name,
                "category": product.category,
                "description": product.description,
                "image_url": product.image_url,
                "brand": product.brand
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
                            "output": computer.output
                        }
                    case "gpu":
                        gpu = Gpu.objects.get(prod_id=product)
                        product_data["specific_details"] = {
                            "model": gpu.model,
                            "vram": gpu.vram,
                            "chipset": gpu.chipset,
                            "max_resolution": gpu.max_resolution,
                            "output": gpu.output,
                            "tech_support": gpu.tech_support
                        }
                    case "keyboard":
                        keyboard = Keyboard.objects.get(prod_id=product)
                        product_data["specific_details"] = {
                            "model": keyboard.model,
                            "key_type": keyboard.key_type,
                            "layout": keyboard.layout,
                            "connectivity": keyboard.connectivity,
                            "dimension": keyboard.dimension
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
                            "mem_speed": cpu.mem_speed
                        }
                    case "mouse":
                        mouse = Mouse.objects.get(prod_id=product)
                        product_data["specific_details"] = {
                            "model": mouse.model,
                            "brand": mouse.brand,
                            "dpi": mouse.dpi,
                            "connectivity": mouse.connectivity,
                            "color": mouse.color
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
                            "output": monitor.output
                        }
                    case "ram":
                        ram = Ram.objects.get(prod_id=product)
                        product_data["specific_details"] = {
                            "brand": ram.brand,
                            "model": ram.model,
                            "capacity": ram.capacity,
                            "ddr": ram.ddr,
                            "speed": ram.speed
                        }
                    case _:
                        product_data["category_error"] = "Categoria não existe"

            except Exception as e:
                f"Erro ao carregar detalhes: {str(e)}"

            product_data_list.append(product_data)

        return product_data_list

    except Exception as e:
        raise ValueError(f"Erro ao obter produtos: {str(e)}")


def update_product(product_id, name=None, category=None, description=None,
                   image_url=None, brand=None, **spec_fields):

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
                    computer.is_notebook = spec_fields.get("is_notebook", computer.is_notebook)
                    computer.motherboard = spec_fields.get("motherboard", computer.motherboard)
                    computer.cpu = spec_fields.get("cpu", computer.cpu)
                    computer.ram = spec_fields.get("ram", computer.ram)
                    computer.storage = spec_fields.get("storage", computer.storage)
                    computer.gpu = spec_fields.get("gpu", computer.gpu)
                    computer.inches = spec_fields.get("inches", computer.inches)
                    computer.panel_type = spec_fields.get("panel_type", computer.panel_type)
                    computer.resolution = spec_fields.get("resolution", computer.resolution)
                    computer.refresh_rate = spec_fields.get("refresh_rate", computer.refresh_rate)
                    computer.color_support = spec_fields.get("color_support", computer.color_support)
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

