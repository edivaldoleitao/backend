import json
import re
from datetime import date
from datetime import datetime
from pathlib import Path

import requests
from playwright.sync_api import Locator
from playwright.sync_api import Page
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from track_save.webscraping.enums import Categories

from .scraper import Scraper
from .specific_data import cpu as cpu_specific_data
from .specific_data import gpu as gpu_specific_data

BASE = Path(__file__).parent
API_URL = "http://localhost:8001/api/products/create/"
HTTP_STATUS_CREATED = 201


class KabumScraper(Scraper):
    def __init__(
        self,
        category: Categories,
        limit: int = 100,
        local_results: bool = False,
        save_print: bool = True,
    ):
        self.category = category
        self.limit = limit
        self.local_results = local_results
        self.save_print = save_print

    def run(self, headless) -> list[dict]:  # noqa: C901, PLR0915
        print("🤖 Iniciando a coleta de dados da Kabum...")
        print(f"> Categoria: {self.category.name}, Limite: {self.limit}")
        results = []
        browser, page = self.init_browser(headless=headless)

        url = self.parse_category(self.category, get_url=True)
        page.goto(url)

        locBarraFiltro = page.locator("#Filter")
        locFiltroItens = locBarraFiltro.locator("select.sc-dcf1314f-0")
        self.wait_element(locFiltroItens)

        locFiltroItens.select_option(value="100")

        locItens = page.locator("article.productCard")
        self.wait_element(locItens)
        print(
            f"> Encontrados {locItens.count()} produtos na categoria {self.category.name}.",  # noqa: E501
        )
        for i in range(min(locItens.count(), self.limit)):
            card = locItens.nth(i)

            card.click()

            priceSection = page.locator("span.block.my-12 b")
            descriptionSection = page.locator("#description")
            techInfoSection = page.locator("#technicalInfoSection")
            reviewsSection = page.locator("#reviewsSection")
            self.wait_elements(
                page,
                [priceSection, descriptionSection, techInfoSection, reviewsSection],
            )
            print("> Coletando produto da url:", page.url)

            common_data = self.get_common_data(
                page,
                priceSection,
                descriptionSection,
                techInfoSection,
                reviewsSection,
            )
            specific_info = self.get_specific_data(techInfoSection, common_data["name"])

            product_data = {
                **common_data,
                **specific_info,
                "store": "Kabum",
                "available": True,
            }

            results.append(product_data)
            if self.local_results:
                print(f"Produto {i + 1} capturado: {product_data['name']}")
                # print("URL:", product_data["url"])
                # print("> Product Data:", product_data)
                print("=" * 50 + "\n")

            page.go_back()

        results_dir = BASE / "results"
        results_dir.mkdir(exist_ok=True, parents=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")  # noqa: DTZ005
        base_name = f"{self.category.name.lower()}_{timestamp}"

        if self.local_results:
            print(f"🗂️ Salvando resultados em {results_dir}...")
            if self.save_print:
                screenshot_path = results_dir / f"{base_name}.png"
                page.screenshot(path=str(screenshot_path), full_page=True)

            results_str = json.dumps(results, ensure_ascii=False, indent=4)

            json_path = results_dir / f"{base_name}.json"
            with json_path.open("w", encoding="utf-8") as f:
                f.write(results_str)

        if results:
            print(f"✅ {len(results)} produtos capturados com sucesso!")

            for result in results:
                try:
                    response = requests.post(API_URL, json=result, timeout=10)
                    if response.status_code == HTTP_STATUS_CREATED:
                        print(
                            f"✅ Produto {result['name']} enviado com sucesso para a API!",  # noqa: E501
                        )
                    else:
                        print(
                            f"⚠️ Erro ao enviar dado para a API: {response.status_code} - {response.text}",  # noqa: E501
                        )
                except requests.exceptions.ConnectionError as e:
                    print(f"⚠️ Erro de conexão ao enviar '{result['name']}': {e}")
                except requests.exceptions.Timeout as e:
                    # timeout de 10s expirou
                    print(f"⚠️ Timeout ao enviar '{result['name']}': {e}")
                except requests.exceptions.RequestException as e:
                    # qualquer outro erro de HTTP/Request
                    print(f"⚠️ Erro inesperado ao enviar '{result['name']}': {e}")
        else:
            print("⚠️ Nenhum produto encontrado ou capturado.")

        self.close_browser(browser)
        print("🤖 Coleta finalizada.\n")

        return results

    def get_common_data(
        self,
        page: Page,
        priceSection: Locator,
        descriptionSection: Locator,
        techInfoSection: Locator,
        reviewsSection: Locator,
    ) -> dict:
        name_loc = descriptionSection.locator("h2").first
        if not self.element_visible(name_loc):
            name_loc = page.locator("h1.text-sm").first

        rating_loc = reviewsSection.locator("span").first
        self.wait_element(rating_loc, timeout=2000)

        try:
            txt_rating = rating_loc.inner_text(timeout=2000).strip()
            rating = float(txt_rating) if txt_rating else 0.0
        except (PlaywrightTimeoutError, ValueError):
            # timeout ou texto não-numérico
            rating = 0.0

        name = name_loc.inner_text().strip()
        category = self.category.name.lower()
        price = self.get_price(priceSection)
        url = page.url
        img_url = page.locator(
            "div.swiper-slide.swiper-slide-active img",
        ).first.get_attribute("src")
        brand = self.get_brand(techInfoSection, name)
        description = self.get_description(descriptionSection)
        collection_date = date.today().isoformat()  # noqa: DTZ011

        return {
            "name": name,
            "category": category,
            "value": price,
            "url": url,
            "image_url": img_url,
            "brand": brand,
            "description": description,
            "rating": rating,
            "collection_date": collection_date,
        }

    def get_specific_data(self, section: Locator, name: str) -> dict:  # noqa: PLR0911
        if self.category == Categories.MOTHERBOARD:
            return {
                "socket": "AM4/AM5/LGA1200",
                "model": self.get_model(section),
                "chipset": gpu_specific_data.get_chipset(name=name),
                "form_type": "ATX/ITX",
                "max_ram_capacity": "64GB",
                "ram_type": "DDR4/DDR5",
                "ram_slots": "4",
                "pcie_slots": "2",
                "sata_ports": "6",
                "m2_slot": "1",
            }

        if self.category == Categories.GPU:
            return {
                "model": self.get_model(section),
                "vram": gpu_specific_data.get_vram(section),
                "chipset": gpu_specific_data.get_chipset(name=name),
                "max_resolution": gpu_specific_data.get_max_resolution(section),
                "output": gpu_specific_data.get_output(section),
                "tech_support": gpu_specific_data.get_tech_support(section),
            }

        if self.category == Categories.CPU:
            return {
                "model": self.get_model(section),
                "integrated_video": cpu_specific_data.get_integrated_video(section),
                "socket": cpu_specific_data.get_socket(section),
                "core_number": cpu_specific_data.get_core_number(section),
                "thread_number": cpu_specific_data.get_threads(section),
                "frequency": cpu_specific_data.get_frequency(section, name=name),
                "mem_speed": cpu_specific_data.get_mem_speed(section),
            }

        if self.category == Categories.STORAGE:
            return {
                "capacity_gb": "256/512/1024",
                "storage_type": "SSD/HDD",
                "interface": "SATA/PCIe NVMe",
                "form_factor": '2.5"/M.2',
                "read_speed": "500MB/s",
                "write_speed": "450MB/s",
            }

        if self.category == Categories.KEYBOARD:
            return {
                "model": self.get_model(section),
                "key_type": "Mechanical/Membrane",
                "layout": "ABNT2/ANSI",
                "connectivity": "Wired/Wireless",
                "dimension": "Standard/Compact",
            }

        if self.category == Categories.MOUSE:
            return {
                "model": self.get_model(section),
                "dpi": "8000/16000",
                "connectivity": "Wired/Wireless",
                "color": "Preto/Branco",
            }

        if self.category == Categories.MONITOR:
            return {
                "model": self.get_model(section),
                "inches": '24"/27"',
                "panel_type": "IPS/TN",
                "proportion": "16:9/21:9",
                "resolution": "1920x1080/2560x1440",
                "refresh_rate": "60Hz/144Hz",
                "color_support": "16.7M/1.07B",
                "output": "HDMI/DisplayPort/VGA",
            }

        if self.category == Categories.RAM:
            return {
                "model": self.get_model(section),
                "capacity": "8GB/16GB/32GB",
                "ddr": "DDR4/DDR5",
                "speed": "2400MHz/3200MHz",
            }

        if self.category == Categories.COMPUTER:
            return {
                "is_notebook": False,
                "motherboard": "B550/B550M",
                "cpu": "AMD Ryzen 5/Intel Core i5",
                "ram": "16GB DDR4",
                "storage": "512GB SSD/1TB HDD",
                "gpu": "AMD Radeon RX 6600/NVIDIA GeForce GTX 1660",
                "inches": '24"/27"',
                "panel_type": "IPS/TN",
                "resolution": "1920x1080/2560x1440",
                "refresh_rate": "60Hz/144Hz",
                "color_support": "16.7M/1.07B",
                "output": "HDMI/DisplayPort/VGA",
            }

        return {}

    def get_price(self, section: Locator) -> str:
        if not self.wait_element(section, timeout=2000):
            return "0.00"

        price_locator = section
        price_raw = price_locator.first.inner_text()
        price_clean = re.sub(r"[^\d\.,]", "", price_raw)
        return price_clean.replace(".", "").replace(",", ".") if price_clean else "0.00"

    def get_brand(self, section: Locator, name: str) -> str:
        candidates = [
            "span:has-text('Marca')",
            "p:has-text('Marca')",
        ]

        brand_name = ""
        for sel in candidates:
            loc = section.locator(sel)
            if loc.count() > 0:
                try:
                    brand_name = loc.first.inner_text().strip()
                    if brand_name:
                        break
                except AttributeError:
                    brand_name = ""

        if not brand_name:
            brands = [
                "Corsair",
                "ASUS",
                "Gigabyte",
                "MSI",
                "Samsung",
                "Kingston",
                "Rise Mode",
                "Logitech",
                "Dell",
                "HP",
                "Redragon",
                "HyperX",
                "Acer",
                "Lenovo",
                "Neologic",
                "3green",
                "2eletro",
                "Skill",
            ]
            for brand in brands:
                if brand.lower() in name.lower():
                    return brand

        if not brand_name:
            return "Generic"

        brand = re.search(r"Marca:\s*(.+)$", brand_name, flags=re.IGNORECASE)
        return brand.group(1) if brand else "Generic"

    def get_description(self, section: Locator) -> str:  # noqa: C901
        """
        Retorna a descrição completa: título + parágrafo.
        """
        skip_texts = {"Compre agora no KaBuM!"}

        # 1) tenta achar <h3>
        heading = None
        for i in range(section.locator("h3").count()):
            h = section.locator("h3").nth(i)
            txt = h.inner_text().strip()
            if txt and txt not in skip_texts:
                heading = h
                break

        # 2) se não achou, tenta segunda <h2>
        if not heading:
            h2s = section.locator("h2")
            if h2s.count() > 1:
                heading = h2s.nth(1)
            else:
                return ""  # <-- não quebra, retorna vazio

        title = heading.inner_text().strip()

        # 3) tenta pegar o parágrafo seguinte, mas captura timeout
        para = heading.locator("xpath=following-sibling::p[normalize-space()][1]").first
        try:
            paragraph = para.inner_text(timeout=500).strip()
        except (AttributeError, PlaywrightTimeoutError):
            paragraph = ""

        # Se tiver apenas um parágrafo, captura também
        paras = section.locator("p")
        if not paragraph and paras.count() > 0:
            try:
                paragraph = paras.first.inner_text(timeout=500).strip()
            except (AttributeError, PlaywrightTimeoutError):
                paragraph = ""

        # 4) monta o retorno (se title existir, mesmo sem parágrafo você tem algo)
        if title and paragraph:
            return f"{title}\n\n{paragraph}"
        if title:
            return title
        if paragraph:
            return paragraph
        return ""

    def get_model(self, section: Locator) -> str:
        candidates = [
            "span:has-text('Modelo')",
            "p:has-text('Modelo')",
        ]

        model_name = ""
        for sel in candidates:
            loc = section.locator(sel)
            if loc.count() > 0:
                try:
                    model_name = loc.first.inner_text().strip()
                    if model_name:
                        break
                except AttributeError:
                    continue

        if not model_name:
            return ""

        model = re.search(r"Modelo:\s*(.+)$", model_name, flags=re.IGNORECASE)
        return model.group(1) if model else ""


if __name__ == "__main__":
    # Teste de coleta para todas as categorias
    # for category in Categories:
    #     scraper = KabumScraper(
    #         category=category,
    #         limit=10,
    #         local_results=True,
    #         save_print=False,
    #     )
    #     scraper.run(headless=True)

    # Teste específico para GPU
    scraper = KabumScraper(
        category=Categories.CPU,
        limit=10,
        local_results=True,
        save_print=True,
    )
    scraper.run(headless=True)
