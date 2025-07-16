import hashlib
import re
from decimal import Decimal

from api.entities.favorite import Favorite
from api.entities.price import Price
from api.entities.product import Computer
from api.entities.product import Cpu
from api.entities.product import Gpu
from api.entities.product import Keyboard
from api.entities.product import Monitor
from api.entities.product import Motherboard
from api.entities.product import Mouse
from api.entities.product import Product
from api.entities.product import ProductCategory
from api.entities.product import ProductStore
from api.entities.product import Ram
from api.entities.product import Storage
from api.entities.product import Store
from api.enums.category_specs import CATEGORY_SPECS
from django.apps import apps
from django.contrib.postgres.search import SearchQuery
from django.contrib.postgres.search import SearchRank
from django.contrib.postgres.search import SearchVector
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection
from django.db import transaction
from django.db.models import Case
from django.db.models import Exists
from django.db.models import F
from django.db.models import FloatField
from django.db.models import Max
from django.db.models import OuterRef
from django.db.models import Q
from django.db.models import Subquery
from django.db.models import Value
from django.db.models import When


def create_store(name):
    if Store.objects.filter(name=name).exists():
        msg = "Esta loja já foi cadastrada."
        raise ValueError(msg) from None

    match name:
        case "Kabum":
            store = Store.objects.create(
                name=name,
                url_base="https://www.kabum.com.br",
                is_sponsor=False,
            )
        case "Terabyte":
            store = Store.objects.create(
                name=name,
                url_base="https://www.terabyteshop.com.br",
                is_sponsor=False,
            )
        case "Amazon":
            store = Store.objects.create(
                name=name,
                url_base="https://www.amazon.com/?language=pt_BR",
                is_sponsor=False,
            )

    return store


def get_stores():
    stores = Store.objects.all()

    if not stores:
        msg = "Não há lojas cadastradas"
        raise ValueError(msg)

    lst = []
    for store in stores:
        store_data = {
            "name": store.name,
            "url_base": store.url_base,
            "is_sponsor": store.is_sponsor,
        }

        lst.append(store_data)

    return lst


def update_store(name, url=None, is_sponsor=None):
    store = Store.objects.get(name=name)

    if url:
        store.url_base = url
    if is_sponsor:
        store.is_sponsor = is_sponsor

    store.save()

    return store


def delete_store(name):
    stores = Store.objects.filter(name=name)
    count, _ = stores.delete()
    return f"{count} loja(s) com nome '{name}' foram deletadas com sucesso."


def create_product(  # noqa: C901, PLR0912, PLR0913, PLR0915
    name,
    category,
    description,
    image_url,
    brand,
    store,
    url,
    available,
    rating,
    value,
    **spec_fields,
):
    # Verifica se a categoria existe
    if category not in [choice[0] for choice in ProductCategory.choices]:
        msg = "Categoria inválida."
        raise ValueError(msg)

    # Extrai só os campos específicos daquela categoria
    allowed = CATEGORY_SPECS.get(category, [])
    payload = {key: spec_fields.get(key) for key in allowed}

    # Verifica os campos obrigatórios comuns
    if not all([name, image_url, brand, store, url]):
        msg = "Todos os campos obrigatórios devem ser informados."
        raise ValueError(msg)

    # Cria o hash SHA-256 de nome + url
    base = f"{name}{url}"
    digest = hashlib.sha256(base.encode("utf-8")).hexdigest()

    with transaction.atomic():
        product, created = Product.objects.get_or_create(
            hash=digest,
            defaults={
                "name": name,
                "category": category,
                "description": description,
                "image_url": image_url,
                "brand": brand,
            },
        )

        if created:
            match category:
                case "computer":
                    # exemplo de como usar o payload em vez de spec_fields direto
                    Computer.objects.create(prod=product, **payload)
                case "gpu":
                    Gpu.objects.create(prod=product, **payload)
                case "ram":
                    Ram.objects.create(prod=product, **payload)
                case "cpu":
                    Cpu.objects.create(prod=product, **payload)
                case "mouse":
                    Mouse.objects.create(prod=product, **payload)
                case "monitor":
                    Monitor.objects.create(prod=product, **payload)
                case "keyboard":
                    Keyboard.objects.create(prod=product, **payload)
                case "motherboard":
                    Motherboard.objects.create(prod=product, **payload)
                case "storage":
                    storage_data = {
                        "capacity_gb": spec_fields.get("capacity_gb"),
                        "storage_type": spec_fields.get("storage_type"),
                        "interface": spec_fields.get("interface"),
                        "form_factor": spec_fields.get("form_factor"),
                        "read_speed": spec_fields.get("read_speed"),
                        "write_speed": spec_fields.get("write_speed"),
                    }
                    Storage.objects.create(prod=product, **storage_data)
                case _:
                    # nunca deve chegar aqui, pois já validamos acima
                    msg = f"Categoria não suportada: {category}"
                    raise ValueError(msg)

        # Verifica se a loja existe
        try:
            store = Store.objects.get(name=store)
        except ObjectDoesNotExist as err:
            msg = f"Loja '{store}' não encontrada."
            raise ValueError(msg) from err

        product_store, ps_created = ProductStore.objects.get_or_create(
            product=product,
            url_product=url,
            defaults={
                "store": store,
                "available": available,
                "rating": rating,
            },
        )

        # Se o produto já existe na loja, atualiza o campo 'available' e 'rating'  # noqa: E501
        if not ps_created:
            changed = False

            if product_store.available != available:
                product_store.available = available
                changed = True

            if product_store.rating != rating:
                product_store.rating = rating
                changed = True

            if changed:
                product_store.save(update_fields=["available", "rating"])

        new_value = Decimal(str(value))
        last_price = (
            Price.objects.filter(product_store=product_store)
            .order_by("-collection_date", "-id")
            .first()
        )

        # Se não houver preço anterior ou o novo valor for diferente, cria um novo registro de preço  # noqa: E501
        if not last_price or last_price.value != new_value:
            Price.objects.create(
                product_store=product_store,
                value=new_value,
                collection_date=spec_fields.get("collection_date"),
            )

    return product


def get_specific_details(product):  # noqa: PLR0911
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
                    "output": p.output,
                }
            case "gpu":
                p = Gpu.objects.get(prod=product)
                return {
                    "model": p.model,
                    "vram": p.vram,
                    "chipset": p.chipset,
                    "max_resolution": p.max_resolution,
                    "output": p.output,
                    "tech_support": p.tech_support,
                }
            case "keyboard":
                p = Keyboard.objects.get(prod=product)
                return {
                    "model": p.model,
                    "key_type": p.key_type,
                    "layout": p.layout,
                    "connectivity": p.connectivity,
                    "dimension": p.dimension,
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
                    "mem_speed": p.mem_speed,
                }
            case "mouse":
                p = Mouse.objects.get(prod=product)
                return {
                    "model": p.model,
                    "dpi": p.dpi,
                    "connectivity": p.connectivity,
                    "color": p.color,
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
                    "output": p.output,
                }
            case "ram":
                p = Ram.objects.get(prod=product)
                return {
                    "model": p.model,
                    "capacity": p.capacity,
                    "ddr": p.ddr,
                    "speed": p.speed,
                }
            case "storage":
                p = Storage.objects.get(prod=product)
                return {
                    "capacity": p.capacity_gb,
                    "storage_type": p.storage_type,
                    "interface": p.interface,
                    "form_factor": p.form_factor,
                    "read_speed": p.read_speed,
                    "write_speed": p.write_speed,
                }
            case "motherboard":
                p = Motherboard.objects.get(prod=product)
                return {
                    "model": p.model,
                    "socket": p.socket,
                    "chipset": p.chipset,
                    "form_type": p.form_type,
                    "max_ram_capacity": p.max_ram_capacity,
                    "ram_type": p.ram_type,
                    "ram_slots": p.ram_slots,
                    "pcie_slots": p.pcie_slots,
                    "sata_ports": p.sata_ports,
                    "m2_slot": p.m2_slot,
                }
            case _:
                return {}
    except (
        Computer.DoesNotExist,
        Gpu.DoesNotExist,
        Keyboard.DoesNotExist,
        Cpu.DoesNotExist,
        Mouse.DoesNotExist,
        Monitor.DoesNotExist,
        Ram.DoesNotExist,
        Storage.DoesNotExist,
        Motherboard.DoesNotExist,
    ):
        return {}


def fallback_simples_por_sql(search_text: str, permitir_relaxamento: bool = True):
    """
    Busca produtos por similaridade textual + filtros extraídos implicitamente (categoria, marca, tipo, preço).
    Agora com categorias, marcas e tipos extraídos dinamicamente do banco.
    """

    texto = search_text.lower()
    palavras = re.findall(r"\w+", texto)
    if not palavras:
        return []

    # ====== Dados válidos extraídos dinamicamente ======
    CATEGORIAS_VALIDAS = set(
        Product.objects.values_list("category", flat=True).distinct()
    )
    MARCAS_VALIDAS = set(Product.objects.values_list("brand", flat=True).distinct())
    TIPOS_VALIDOS = set(
        Product.objects.values_list("description", flat=True)
        .exclude(description__isnull=True)
        .exclude(description__exact="")
        .distinct()
    )

    # Normaliza para string simples (ex: "teclado mecânico" → ["teclado", "mecânico"])
    tipos_tokenizados = set()
    for desc in TIPOS_VALIDOS:
        tipos_tokenizados.update(re.findall(r"\w+", desc.lower()))
    TIPOS_VALIDOS = tipos_tokenizados

    # ====== Extração de intenção ======
    categoria = next((c for c in CATEGORIAS_VALIDAS if c and c.lower() in texto), None)
    marca = next((m for m in MARCAS_VALIDAS if m and m.lower() in texto), None)
    tipos = [t for t in TIPOS_VALIDOS if t in texto]

    preco_limite = None
    match_preco = re.search(
        r"(?:até|por|menos de|abaixo de)?\s*(?:r\$)?\s*(\d{1,3}(?:[.,]?\d{3})*(?:[.,]\d{2})?|\d+)",
        texto,
    )
    if match_preco:
        preco_raw = match_preco.group(1).replace(".", "").replace(",", ".")
        try:
            preco_limite = float(preco_raw)
        except:
            preco_limite = None

    # ====== Função interna para montar e executar SQL ======
    def executar_busca(
        com_preco=True, com_categoria=True, com_marca=True, com_tipos=True
    ):
        like_clauses = [
            f"unaccent(p.name || ' ' || p.description) ILIKE unaccent(%s)"
            for _ in palavras
        ]
        sql_or = " OR ".join(like_clauses)

        sql = f"""
            SELECT DISTINCT p.id
            FROM api_product p
            JOIN api_productstore ps ON ps.product_id = p.id
            JOIN (
                SELECT product_store_id, MAX(collection_date) AS max_date
                FROM api_price
                GROUP BY product_store_id
            ) latest ON latest.product_store_id = ps.id
            JOIN api_price pr ON pr.product_store_id = ps.id AND pr.collection_date = latest.max_date
            WHERE ({sql_or})
        """

        values = [f"%{palavra}%" for palavra in palavras]

        if com_categoria and categoria:
            sql += " AND unaccent(lower(p.category)) = unaccent(%s)"
            values.append(categoria.lower())

        if com_marca and marca:
            sql += " AND unaccent(lower(p.brand)) ILIKE unaccent(%s)"
            values.append(f"%{marca.lower()}%")

        if com_tipos and tipos:
            for tipo in tipos:
                sql += " AND unaccent(lower(p.description)) ILIKE unaccent(%s)"
                values.append(f"%{tipo}%")

        if com_preco and preco_limite:
            sql += " AND pr.value <= %s"
            values.append(preco_limite)

        with connection.cursor() as cursor:
            cursor.execute(sql, values)
            return [row[0] for row in cursor.fetchall()]

    # ====== Tentativas com relaxamento progressivo ======
    tentativas = (
        [
            dict(com_preco=True, com_categoria=True, com_marca=True, com_tipos=True),
            dict(com_preco=True, com_categoria=False, com_marca=True, com_tipos=True),
            dict(com_preco=True, com_categoria=False, com_marca=False, com_tipos=True),
            dict(
                com_preco=False, com_categoria=False, com_marca=False, com_tipos=False
            ),
        ]
        if permitir_relaxamento
        else [dict(com_preco=True, com_categoria=True, com_marca=True, com_tipos=True)]
    )

    for tentativa in tentativas:
        ids = executar_busca(**tentativa)
        if ids:
            return [{"pk": pid, "rank": 0.05} for pid in ids]

    return []


"""
exemplo de uso
http://localhost:8001/api/products/search/?name=nvidia rtx 3080&brand=NVIDIA
http://localhost:8001/api/products/search/?brand=NVIDIA&category=gpu&price_min=2000&price_max=3000&store=Kabum
"""


def search_products(filters: dict):
    try:
        base_query = Q()
        product_ranks = {}

        if "name" in filters:
            search_query = SearchQuery(filters["name"], config="portuguese")
            search_vector = SearchVector("name", "description", config="portuguese")
            search_text = filters["name"]

            # ====== 1. Busca full-text ======
            search_query = SearchQuery(search_text, config="portuguese")
            search_vector = SearchVector("name", "description", config="portuguese")

            fulltext_match = Product.objects.annotate(
                search=search_vector,
                rank=SearchRank(search_vector, search_query),
            ).filter(search=search_query)

            combined_products = list(fulltext_match.values("pk", "rank"))

            # ====== 2. Fallback por SQL puro ======
            if not combined_products:
                combined_products = fallback_simples_por_sql(search_text)

            # ====== 3. Se nada for encontrado ======
            if not combined_products:
                raise ValueError("Nenhum produto encontrado com os filtros fornecidos.")

                if not product_ids:
                    raise ValueError(
                        "Nenhum produto encontrado com os filtros fornecidos."
                    )

                # Simula rank baixo no fallback
                combined_products = [{"pk": pid, "rank": 0.1} for pid in product_ids]

            # Gera os ranks e monta query base
            product_ranks = {item["pk"]: item["rank"] for item in combined_products}
            # Constrói ranks e aplica filtro base
            product_ranks = {item["pk"]: item["rank"] for item in combined_products}
            base_query &= Q(pk__in=product_ranks.keys())

        # ====== FILTROS EXTRAS ======
        if "id" in filters:
            base_query &= Q(id=filters["id"])
        if "category" in filters:
            base_query &= Q(category__iexact=filters["category"])
        if "brand" in filters:
            base_query &= Q(brand__icontains=filters["brand"])
        if "store" in filters:
            base_query &= Q(productstore__store__name__icontains=filters["store"])

        # ====== ANOTAÇÕES ======
        latest_price_subquery = (
            Price.objects.filter(product_store__product=OuterRef("pk"))
            .order_by("-collection_date")
            .values("value")[:1]
        )

        max_rating_subquery = (
            ProductStore.objects.filter(product=OuterRef("pk"))
            .order_by("-rating")
            .values("rating")[:1]
        )

        sponsor_subquery = Store.objects.filter(
            productstore__product=OuterRef("pk"),
            is_sponsor=True,
        )

        # ====== PRODUTOS PATROCINADOS ======
        sponsored_products = Product.objects.annotate(
            latest_price=Subquery(latest_price_subquery),
            rating=Subquery(max_rating_subquery),
            is_sponsored=Exists(sponsor_subquery),
        ).filter(base_query, is_sponsored=True)

        sponsored_products = sponsored_products.annotate(
            search_rank=Case(
                *[When(pk=pk, then=Value(rank)) for pk, rank in product_ranks.items()],
                default=Value(0.0),
                output_field=FloatField(),
            )
        )

        if "price_min" in filters:
            sponsored_products = sponsored_products.filter(
                latest_price__gte=filters["price_min"]
            )
        if "price_max" in filters:
            sponsored_products = sponsored_products.filter(
                latest_price__lte=filters["price_max"]
            )
        if "rating_min" in filters:
            sponsored_products = sponsored_products.filter(
                rating__gte=filters["rating_min"]
            )

        sponsored_products = sponsored_products.order_by("-search_rank", "-rating")[:3]

        # ====== PRODUTOS NÃO PATROCINADOS ======
        non_sponsored_products = Product.objects.annotate(
            latest_price=Subquery(latest_price_subquery),
            rating=Subquery(max_rating_subquery),
            is_sponsored=Exists(sponsor_subquery),
        ).filter(base_query, is_sponsored=False)

        non_sponsored_products = non_sponsored_products.annotate(
            search_rank=Case(
                *[When(pk=pk, then=Value(rank)) for pk, rank in product_ranks.items()],
                default=Value(0.0),
                output_field=FloatField(),
            )
        )

        if "price_min" in filters:
            non_sponsored_products = non_sponsored_products.filter(
                latest_price__gte=filters["price_min"]
            )
        if "price_max" in filters:
            non_sponsored_products = non_sponsored_products.filter(
                latest_price__lte=filters["price_max"]
            )
        if "rating_min" in filters:
            non_sponsored_products = non_sponsored_products.filter(
                rating__gte=filters["rating_min"]
            )

        non_sponsored_products = non_sponsored_products.order_by(
            "-search_rank", "-rating"
        )

        # ====== RESULTADOS ======
        final_products = list(sponsored_products) + list(non_sponsored_products)

        if not final_products:
            raise ValueError("Nenhum produto encontrado com os filtros fornecidos.")

        # MONTA JSON DE RETORNO
        product_data_list = []
        for product in final_products:
            latest_price_entry = (
                Price.objects.filter(product_store__product=product)
                .order_by("-collection_date")
                .select_related("product_store__store")
                .first()
            )

            if latest_price_entry:
                ps = latest_price_entry.product_store
                store_name = ps.store.name
                available = ps.available
                collection_date = latest_price_entry.collection_date
                store_rating = ps.rating
            else:
                store_name = None
                available = None
                collection_date = None
                store_rating = None

            product_data = {
                "id": product.pk,
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
                "store_rating": store_rating,
                "specific_details": get_specific_details(product),
            }
            product_data_list.append(product_data)

        return product_data_list if len(product_data_list) > 1 else product_data_list[0]

    except Exception as e:
        raise ValueError(f"Erro ao buscar produto(s): {e!s}")


# pra pegar produto pelo id
def get_product_by_id(product_id):  # noqa: C901
    try:
        product = Product.objects.get(id=product_id)

        product_data = {
            "id": product.pk,
            "name": product.name,
            "category": product.category,
            "description": product.description,
            "image_url": product.image_url,
            "brand": product.brand,
            "hash": product.hash,
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
                    "model": ram.model,
                    "capacity": ram.capacity,
                    "ddr": ram.ddr,
                    "speed": ram.speed,
                }
            case "storage":
                storage = Storage.objects.get(prod=product)
                product_data["specific_details"] = {
                    "capacity": storage.capacity_gb,
                    "storage_type": storage.storage_type,
                    "interface": storage.interface,
                    "form_factor": storage.form_factor,
                    "read_speed": storage.read_speed,
                    "write_speed": storage.write_speed,
                }
            case "motherboard":
                motherboard = Motherboard.objects.get(prod_id=product)
                product_data["specific_details"] = {
                    "model": motherboard.model,
                    "socket": motherboard.socket,
                    "chipset": motherboard.chipset,
                    "form_type": motherboard.form_type,
                    "max_ram_capacity": motherboard.max_ram_capacity,
                    "ram_type": motherboard.ram_type,
                    "ram_slots": motherboard.ram_slots,
                    "pcie_slots": motherboard.pcie_slots,
                    "sata_ports": motherboard.sata_ports,
                    "m2_slot": motherboard.m2_slot,
                }
            case _:
                product_data["category_error"] = "Categoria não existe"

        return product_data  # noqa: TRY300

    except Product.DoesNotExist:
        msg = "Produto não encontrado."
        raise ValueError(msg)  # noqa: B904
    except Exception as e:
        msg = f"Erro ao obter produto: {e!s}"
        raise ValueError(msg) from e


# pra pegar produto pelo nome


def get_product_by_name(product_name):  # noqa: C901
    try:
        products = Product.objects.filter(name=product_name)

        if not products.exists():
            msg = f"Não há produtos nomeados como: {product_name}"
            raise ValueError(msg)  # noqa: TRY301

        product_data_list = []

        for product in products:
            product_data = {
                "id": product.pk,
                "name": product.name,
                "category": product.category,
                "description": product.description,
                "image_url": product.image_url,
                "brand": product.brand,
                "hash": product.hash,
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
                        "model": ram.model,
                        "capacity": ram.capacity,
                        "ddr": ram.ddr,
                        "speed": ram.speed,
                    }
                case "storage":
                    storage = Storage.objects.get(prod=product)
                    product_data["specific_details"] = {
                        "capacity": storage.capacity_gb,
                        "storage_type": storage.storage_type,
                        "interface": storage.interface,
                        "form_factor": storage.form_factor,
                        "read_speed": storage.read_speed,
                        "write_speed": storage.write_speed,
                    }
                case "motherboard":
                    motherboard = Motherboard.objects.get(prod_id=product)
                    product_data["specific_details"] = {
                        "model": motherboard.model,
                        "socket": motherboard.socket,
                        "chipset": motherboard.chipset,
                        "form_type": motherboard.form_type,
                        "max_ram_capacity": motherboard.max_ram_capacity,
                        "ram_type": motherboard.ram_type,
                        "ram_slots": motherboard.ram_slots,
                        "pcie_slots": motherboard.pcie_slots,
                        "sata_ports": motherboard.sata_ports,
                        "m2_slot": motherboard.m2_slot,
                    }

            product_data_list.append(product_data)

        return product_data_list  # noqa: TRY300

    except Exception as e:
        msg = f"Erro ao obter produtos: {e!s}"
        raise ValueError(msg) from e


def get_product_by_category(product_category):  # noqa: C901
    try:
        products = Product.objects.filter(category=product_category)

        if not products.exists():
            msg = f"Não há produtos na categoria: {product_category}"
            raise ValueError(msg)  # noqa: TRY301

        product_data_list = []

        for product in products:
            product_data = {
                "id": product.pk,
                "name": product.name,
                "category": product.category,
                "description": product.description,
                "image_url": product.image_url,
                "brand": product.brand,
                "hash": product.hash,
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
                        "model": ram.model,
                        "capacity": ram.capacity,
                        "ddr": ram.ddr,
                        "speed": ram.speed,
                    }
                case "storage":
                    storage = Storage.objects.get(prod=product)
                    product_data["specific_details"] = {
                        "capacity": storage.capacity_gb,
                        "storage_type": storage.storage_type,
                        "interface": storage.interface,
                        "form_factor": storage.form_factor,
                        "read_speed": storage.read_speed,
                        "write_speed": storage.write_speed,
                    }
                case "motherboard":
                    motherboard = Motherboard.objects.get(prod_id=product)
                    product_data["specific_details"] = {
                        "model": motherboard.model,
                        "socket": motherboard.socket,
                        "chipset": motherboard.chipset,
                        "form_type": motherboard.form_type,
                        "max_ram_capacity": motherboard.max_ram_capacity,
                        "ram_type": motherboard.ram_type,
                        "ram_slots": motherboard.ram_slots,
                        "pcie_slots": motherboard.pcie_slots,
                        "sata_ports": motherboard.sata_ports,
                        "m2_slot": motherboard.m2_slot,
                    }
                case _:
                    product_data["category_error"] = "Categoria não existe"

            product_data_list.append(product_data)

        return product_data_list  # noqa: TRY300

    except Exception as e:  # noqa: BLE001
        msg = f"Erro ao obter produtos: {e!s}"
        raise ValueError(msg)  # noqa: B904


def get_all_products():  # noqa: C901, PLR0912, PLR0915
    try:
        products = Product.objects.all()

        if not products:
            msg = "Não há produtos cadastrados"
            raise ValueError(msg)  # noqa: TRY301

        product_data_list = []

        for product in products:
            product_data = {
                "id": product.pk,
                "name": product.name,
                "category": product.category,
                "description": product.description,
                "image_url": product.image_url,
                "brand": product.brand,
                "hash": product.hash,
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
                            "model": ram.model,
                            "capacity": ram.capacity,
                            "ddr": ram.ddr,
                            "speed": ram.speed,
                        }
                    case "storage":
                        storage = Storage.objects.get(prod_id=product)
                        product_data["specific_details"] = {
                            "capacity": storage.capacity_gb,
                            "storage_type": storage.storage_type,
                            "interface": storage.interface,
                            "form_factor": storage.form_factor,
                            "read_speed": storage.read_speed,
                            "write_speed": storage.write_speed,
                        }
                    case "motherboard":
                        motherboard = Motherboard.objects.get(prod_id=product)
                        product_data["specific_details"] = {
                            "model": motherboard.model,
                            "socket": motherboard.socket,
                            "chipset": motherboard.chipset,
                            "form_type": motherboard.form_type,
                            "max_ram_capacity": motherboard.max_ram_capacity,
                            "ram_type": motherboard.ram_type,
                            "ram_slots": motherboard.ram_slots,
                            "pcie_slots": motherboard.pcie_slots,
                            "sata_ports": motherboard.sata_ports,
                            "m2_slot": motherboard.m2_slot,
                        }
                    case _:
                        product_data["category_error"] = "Categoria não existe"

            except Exception as e:  # noqa: BLE001
                f"Erro ao carregar detalhes: {e!s}"

            latest_price_entry = (
                Price.objects.filter(
                    product_store__product=product,
                )
                .order_by("-collection_date")
                .select_related("product_store__store")
                .first()
            )

            if latest_price_entry:
                ps = latest_price_entry.product_store
                product_data["store"] = ps.store.name
                product_data["store_url_base"] = ps.store.url_base
                product_data["rating"] = ps.rating
                product_data["available"] = ps.available
                product_data["value"] = float(latest_price_entry.value)
                product_data["collection_date"] = latest_price_entry.collection_date
            else:
                product_data["store"] = None
                product_data["store_url_base"] = None
                product_data["rating"] = None
                product_data["available"] = None
                product_data["value"] = None
                product_data["collection_date"] = None

            product_data_list.append(product_data)

        return product_data_list  # noqa: TRY300

    except Exception as e:  # noqa: BLE001
        msg = f"Erro ao obter produtos: {e!s}"
        raise ValueError(msg)  # noqa: B904


def get_product_stores_by_product(ps_id):
    """
    Retorna uma lista dos prices que possuem o mesmo product store
    """
    lst = [
        {
            "product": ps.product.id,
            "store": Store.objects.get(id=ps.store.id).name,
            "url_product": ps.url_product,
            "available": ps.available,
        }
        for ps in ProductStore.objects.filter(product=ps_id)
    ]
    return lst


def get_recent_price_stores(product_id):
    """
    Retorna o preço mais recente de cada ProductStore para um produto específico.
    """
    latest_prices = (
        Price.objects.filter(product_store__product_id=product_id)
        .order_by("product_store_id", "-collection_date")
        .distinct("product_store_id")
        .select_related("product_store__store")
    )

    return [
        {
            "store_name": price.product_store.store.name,
            "value": str(price.value),
            "ps_id": price.product_store.id,
        }
        for price in latest_prices
    ]


def update_product(  # noqa: C901, PLR0912, PLR0913, PLR0915
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
                        "is_notebook",
                        computer.is_notebook,
                    )
                    computer.motherboard = spec_fields.get(
                        "motherboard",
                        computer.motherboard,
                    )
                    computer.cpu = spec_fields.get("cpu", computer.cpu)
                    computer.ram = spec_fields.get("ram", computer.ram)
                    computer.storage = spec_fields.get("storage", computer.storage)
                    computer.gpu = spec_fields.get("gpu", computer.gpu)
                    computer.inches = spec_fields.get("inches", computer.inches)
                    computer.panel_type = spec_fields.get(
                        "panel_type",
                        computer.panel_type,
                    )
                    computer.resolution = spec_fields.get(
                        "resolution",
                        computer.resolution,
                    )
                    computer.refresh_rate = spec_fields.get(
                        "refresh_rate",
                        computer.refresh_rate,
                    )
                    computer.color_support = spec_fields.get(
                        "color_support",
                        computer.color_support,
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
                case "storage":
                    storage = Storage.objects.get(prod=product)
                    storage.capacity_gb = int(
                        spec_fields.get("capacity", storage.capacity_gb),
                    )
                    storage.storage_type = spec_fields.get(
                        "storage_type",
                        storage.storage_type,
                    )
                    storage.interface = spec_fields.get("interface", storage.interface)
                    storage.form_factor = spec_fields.get(
                        "form_factor",
                        storage.form_factor,
                    )
                    storage.read_speed = spec_fields.get(
                        "read_speed",
                        storage.read_speed,
                    )
                    storage.write_speed = spec_fields.get(
                        "write_speed",
                        storage.write_speed,
                    )
                    storage.save()
                case "motherboard":
                    motherboard = Motherboard.objects.get(prod=product)
                    motherboard.model = spec_fields.get("model", motherboard.model)
                    motherboard.socket = spec_fields.get("socket", motherboard.socket)
                    motherboard.chipset = spec_fields.get(
                        "chipset", motherboard.chipset
                    )
                    motherboard.form_type = spec_fields.get(
                        "form_type", motherboard.form_type
                    )
                    motherboard.max_ram_capacity = spec_fields.get(
                        "max_ram_capacity", motherboard.max_ram_capacity
                    )
                    motherboard.ram_type = spec_fields.get(
                        "ram_type", motherboard.ram_type
                    )
                    motherboard.ram_slots = spec_fields.get(
                        "ram_slots", motherboard.ram_slots
                    )
                    motherboard.pcie_slots = spec_fields.get(
                        "pcie_slots", motherboard.pcie_slots
                    )
                    motherboard.sata_ports = spec_fields.get(
                        "sata_ports", motherboard.sata_ports
                    )
                    motherboard.m2_slot = spec_fields.get(
                        "m2_slot", motherboard.m2_slot
                    )
                    motherboard.save()
                case _:
                    msg = f"Categoria desconhecida: {product.category}"
                    raise ValueError(msg)  # noqa: TRY301

            return product

    except Product.DoesNotExist:
        msg = "Produto não encontrado."
        raise ValueError(msg)  # noqa: B904
    except Exception as e:  # noqa: BLE001
        msg = f"Erro ao atualizar produto: {e!s}"
        raise ValueError(msg)  # noqa: B904


def delete_product(product_id):
    try:
        product = Product.objects.get(id=product_id)

        product.delete()

    except Product.DoesNotExist:
        msg = "Produto não encontrado."
        raise ValueError(msg) from None
    except Exception as e:
        msg = f"Erro ao excluir produto: {e!s}"
        raise ValueError(msg) from e
    else:
        return "Produto excluído com sucesso."


def create_product_store(product_id, store_id, url_product, available):
    """
    Cria um novo ProductStore.
    Raises:
      ValueError: se faltar algum campo obrigatório.
      Product.DoesNotExist / Store.DoesNotExist: se product_id ou store_id não existirem
    """
    # validação básica
    if not all([product_id, store_id, url_product]) or available is None:
        msg = "Todos os campos (product_id, store_id, url_product, available) são obrigatórios."  # noqa: E501
        raise ValueError(
            msg,
        )

    # busca as entidades relacionadas
    product = Product.objects.get(id=product_id)
    store = Store.objects.get(id=store_id)

    # cria e retorna
    return ProductStore.objects.create(
        product=product,
        store=store,
        url_product=url_product,
        available=available,
    )


def get_all_product_stores():
    """
    Retorna lista de dicts com todos os ProductStore.
    """
    lst = []
    for ps in ProductStore.objects.select_related("product", "store").all():
        lst.append(
            {
                "id": ps.id,
                "product": ps.product.id,
                "store": ps.store.id,
                "url_product": ps.url_product,
                "rating": ps.rating,
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
        "rating": ps.rating,
    }


def update_product_store(product_store_id, **data):
    """
    Atualiza campos de um ProductStore existente.
    Campos aceitos em data: product_id, store_id, url_product, available e rating.
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
    if "rating" in data:
        ps.rating = data["rating"]

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


def generic_search(searches):
    results = []

    for search in searches:
        model_name = search.get("model_name")
        columns = search.get("columns", [])
        search_values = search.get("search_values", [])

        if not model_name or not columns or not search_values:
            continue

        if len(columns) != len(search_values):
            raise ValueError("A quantidade de colunas e valores deve ser igual.")

        Model = apps.get_model("api", model_name)
        if not Model:
            raise ValueError(f"Model {model_name} não encontrado no app 'api'.")

        model_fields = [f.name for f in Model._meta.get_fields()]
        field_types = {f.name: f.get_internal_type() for f in Model._meta.get_fields()}

        query = Q()
        price_limit = None  # ✅ Aqui vamos guardar o valor do filtro de price

        for column, value in zip(columns, search_values, strict=False):
            if column == "price":
                price_limit = float(value)  # ✅ Salva o valor e não filtra no Model
                continue

            if column not in model_fields:
                print(
                    f"⚠️ Ignorando filtro: coluna '{column}' não existe no model '{model_name}'"
                )
                continue

            field_type = field_types.get(column)

            if field_type in ["CharField", "TextField"]:
                query &= Q(**{f"{column}__iexact": value})
            elif field_type in ["IntegerField", "FloatField", "DecimalField"]:
                query &= Q(**{f"{column}": value})
            else:
                print(
                    f"⚠️ Ignorando filtro: tipo '{field_type}' da coluna '{column}' não tratado."
                )
                continue

        technical_results = Model.objects.filter(query)
        product_ids = technical_results.values_list("prod_id", flat=True)

        # Busca produtos
        products = Product.objects.filter(id__in=product_ids)

        # Busca stores disponíveis
        stores = ProductStore.objects.filter(product_id__in=product_ids, available=True)
        store_data = stores.values("id", "product_id", "url_product", "store_id")

        store_ids = [s["store_id"] for s in store_data]
        store_names = Store.objects.filter(id__in=store_ids).values("id", "name")
        store_name_map = {s["id"]: s["name"] for s in store_names}

        price_data = (
            Price.objects.filter(product_store_id__in=[s["id"] for s in store_data])
            .order_by("product_store_id", "-collection_date")
            .values("product_store_id", "value", "collection_date")
        )

        price_map = {}
        for price in price_data:
            ps_id = price["product_store_id"]
            if ps_id not in price_map:
                price_map[ps_id] = float(price["value"])

        for product in products:
            product_stores = [s for s in store_data if s["product_id"] == product.id]
            for store in product_stores:
                store_name = store_name_map.get(store["store_id"], "Unknown Store")
                price = price_map.get(store["id"])

                if price is None:
                    continue

                # ✅ Aqui filtra pelo preço máximo, se tiver
                if price_limit is not None and price > price_limit:
                    continue

                results.append(
                    {
                        "name": product.name,
                        "description": product.description,
                        "image_url": product.image_url,
                        "category": product.category,
                        "brand": product.brand,
                        "price": str(price),
                        "store_name": store_name,
                        "url_product": store["url_product"],
                    },
                )

    return {"results": results}


def list_product_stores_by_best_rating(category=None, limit=None, user_id=None):
    qs = ProductStore.objects.filter(available=True)

    if category:
        qs = qs.filter(product__category=category)

    max_rating_subquery = (
        ProductStore.objects.filter(
            product=OuterRef("product"),
            available=True,
            **({"product__category": category} if category else {}),
        )
        .order_by("-rating")
        .values("rating")[:1]
    )

    qs = (
        qs.annotate(max_rating=Subquery(max_rating_subquery))
        .filter(rating=F("max_rating"))
        .order_by("-rating")
    )

    if limit:
        qs = qs[: int(limit)]

    qs = qs.select_related("product", "store").prefetch_related("price_set")

    favorites_by_product = {}

    if user_id:
        favorites = Favorite.objects.filter(user_id=user_id).only("id", "product_id")
        favorites_by_product = {int(fav.product_id): fav.id for fav in favorites}

    return [
        {
            "id": ps.id,
            "product": ps.product.id,
            "product_name": ps.product.name,
            "image_url": ps.product.image_url,
            "store": ps.store.id,
            "store_name": ps.store.name,
            "rating": ps.rating,
            "url_product": ps.url_product,
            "available": ps.available,
            "price": ps.price_set.first().value if ps.price_set.exists() else None,
            "favorite_id": favorites_by_product.get(int(ps.product.id)),
        }
        for ps in qs
    ]
