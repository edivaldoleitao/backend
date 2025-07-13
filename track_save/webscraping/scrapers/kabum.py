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
from .specific_data import keyboard as keyboard_specific_data
from .specific_data import mouse as mouse_specific_data
from .specific_data import ram as ram_specific_data

BASE = Path(__file__).parent
API_URL = "http://localhost:8001/api/products/create/"
HTTP_STATUS_CREATED = 201


class KabumScraper(Scraper):
    def __init__(
        self,
        category: Categories,
        limit: int = 100,
        page_limit: int = 3,
        local_results: bool = False,
        save_print: bool = True,
    ):
        self.category = category
        self.limit = limit
        self.page_limit = page_limit
        self.local_results = local_results
        self.save_print = save_print

    def run(self, headless) -> list[dict]:  # noqa: C901, PLR0912, PLR0915
        print("🤖 Iniciando a coleta de dados da Kabum...")
        print(f"> Categoria: {self.category.name}, Limite: {self.limit}")
        results = []
        browser, page = self.init_browser(headless=headless)

        try:
            url = self.parse_category(self.category, get_url=True)
            page.goto(url, timeout=60000)

            locBarraFiltro = page.locator("#Filter")
            locFiltroItens = locBarraFiltro.locator("select.sc-dcf1314f-0")
            self.wait_element(locFiltroItens)

            locFiltroItens.select_option(value="100")
            page.wait_for_load_state("domcontentloaded")

            page_num = 1
            while len(results) < self.limit and page_num <= self.page_limit:
                locItens = page.locator("article.productCard")
                self.wait_element(locItens)
                item_count_on_page = locItens.count()

                if item_count_on_page == 0:
                    print("> Nenhum produto encontrado nesta página. Encerrando.")
                    break

                print(
                    f"> Encontrados {locItens.count()} produtos na categoria {self.category.name}.",  # noqa: E501
                )

                for i in range(item_count_on_page):
                    if len(results) >= self.limit:
                        print(
                            "\n> Limite total de produtos atingido. Encerrando coleta de itens.",  # noqa: E501
                        )
                        break

                    card = locItens.nth(i)
                    card.click()

                    priceSection = page.locator("span.block.my-12 b")
                    descriptionSection = page.locator("#description")
                    techInfoSection = page.locator("#technicalInfoSection")
                    reviewsSection = page.locator("#reviewsSection")
                    self.wait_elements(
                        page,
                        [
                            priceSection,
                            descriptionSection,
                            techInfoSection,
                            reviewsSection,
                        ],
                    )
                    print("> Coletando produto da url:", page.url)

                    common_data = self.get_common_data(
                        page,
                        priceSection,
                        descriptionSection,
                        techInfoSection,
                        reviewsSection,
                    )
                    specific_info = self.get_specific_data(
                        techInfoSection,
                        common_data["name"],
                    )

                    product_data = {
                        **common_data,
                        **specific_info,
                        "store": "Kabum",
                        "available": True,
                    }

                    results.append(product_data)
                    if self.local_results:
                        print(f"Produto {i + 1} capturado: {product_data['name']}")
                        print("=" * 50 + "\n")

                    page.go_back()
                    page.wait_for_load_state("domcontentloaded")

                # --- Fim do loop de itens da página ---

                # Verifica se o limite de produtos foi atingido
                if len(results) >= self.limit:
                    break

                ITEMS_PER_PAGE = 100
                if item_count_on_page < ITEMS_PER_PAGE:
                    print(
                        f"\n> Página final detectada (contém {item_count_on_page} itens, menos que {ITEMS_PER_PAGE}). Coleta concluída.",  # noqa: E501
                    )
                    break

                # Lógica para ir para a próxima página
                locProximaPagina = page.locator("#listingPagination li.next")
                is_disabled = "disabled" in (
                    locProximaPagina.get_attribute("class") or ""
                )

                if locProximaPagina.is_visible() and not is_disabled:
                    print("> Indo para a próxima página...")
                    locProximaPagina.click()
                    page.wait_for_load_state("domcontentloaded")
                    page_num += 1
                else:
                    print(
                        "\n> Botão 'Próxima Página' não encontrado ou desabilitado. Fim da coleta.",  # noqa: E501
                    )
                    break

            # --- Fim do loop de paginação ---

            # Seção para salvar os resultados e enviar para a API
            if results:
                print(f"\n✅ {len(results)} produtos capturados com sucesso!")
                self.save_and_send_results(results)
            else:
                print("\n⚠️ Nenhum produto encontrado ou capturado.")

        except PlaywrightTimeoutError as e:
            print(f"❌ Timeout do Playwright durante a execução: {e}")
            page.screenshot(path="error_screenshot.png")
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro de requisição HTTP durante a execução: {e}")
            page.screenshot(path="error_screenshot.png")
        finally:
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
                "key_type": keyboard_specific_data.get_key_type(section, name),
                "layout": keyboard_specific_data.get_layout(section),
                "connectivity": keyboard_specific_data.get_connectivity(section),
                "dimension": keyboard_specific_data.get_dimension(section),
            }

        if self.category == Categories.MOUSE:
            return {
                "model": self.get_model(section),
                "dpi": mouse_specific_data.get_dpi(section),
                "connectivity": mouse_specific_data.get_connectivity(section),
                "color": mouse_specific_data.get_color(section),
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
                "capacity": ram_specific_data.get_capacity(section),
                "ddr": ram_specific_data.get_ddr(section),
                "speed": ram_specific_data.get_speed(section),
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

    def save_and_send_results(self, results: list[dict]):
        """
        Salva os resultados localmente e os envia para a API.
        """
        results_dir = BASE / "results"
        results_dir.mkdir(exist_ok=True, parents=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")  # noqa: DTZ005
        base_name = f"{self.category.name.lower()}_{timestamp}"

        if self.local_results:
            print(f"🗂️ Salvando resultados em {results_dir}...")
            results_str = json.dumps(results, ensure_ascii=False, indent=4)
            json_path = results_dir / f"{base_name}.json"
            with json_path.open("w", encoding="utf-8") as f:
                f.write(results_str)
            print(f"  Resultados salvos em {json_path}")

        # Enviar para a API
        for result in results:
            try:
                response = requests.post(API_URL, json=result, timeout=10)
                if response.status_code == HTTP_STATUS_CREATED:
                    print(
                        f"🚀 Produto '{result['name']}' enviado com sucesso para a API!",
                    )
                else:
                    print(
                        f"⚠️ Erro ao enviar para a API: {response.status_code} - {response.text}",
                    )
            except requests.exceptions.RequestException as e:
                print(f"⚠️ Erro de conexão ao enviar '{result['name']}': {e}")


if __name__ == "__main__":
    # Teste de coleta para todas as categorias
    for category in Categories:
        scraper = KabumScraper(
            category=category,
            limit=500,
            local_results=True,
            page_limit=7,
            save_print=False,
        )
        scraper.run(headless=True)

    # # Teste específico para uma categoria
    # scraper = KabumScraper(
    #     category=Categories.RAM,
    #     limit=10,
    #     page_limit=1,
    #     local_results=True,
    #     save_print=True,
    # )
    # scraper.run(headless=True)
