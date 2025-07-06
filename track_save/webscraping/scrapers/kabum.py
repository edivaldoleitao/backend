import json
import re
from datetime import date
from datetime import datetime
from pathlib import Path

import requests
from playwright.sync_api import Locator
from playwright.sync_api import Page

from track_save.webscraping.enums import Categories

from .scraper import Scraper

BASE = Path(__file__).parent
API_URL = "http://localhost:8001/api/products/create/"
HTTP_STATUS_CREATED = 201


class KabumScraper(Scraper):
    def __init__(
        self,
        category: Categories,
        limit: int = 100,
        local_results: bool = False,  # noqa: FBT001
    ):
        self.category = category
        self.limit = limit
        self.local_results = local_results

    def run(self) -> list[dict]:
        print("🤖 Iniciando a coleta de dados da Kabum...")
        print(f"> Categoria: {self.category.name}, Limite: {self.limit}")
        results = []
        playwright, browser, page = self.init_browser()

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

            priceSection = page.locator("#blocoValores")
            descriptionSection = page.locator("#description")
            techInfoSection = page.locator("#technicalInfoSection")
            reviewsSection = page.locator("#reviewsSection")
            self.wait_elements(
                page,
                [descriptionSection, techInfoSection, reviewsSection],
            )

            common_data = self.get_common_data(
                page,
                priceSection,
                descriptionSection,
                techInfoSection,
                reviewsSection,
            )
            specific_info = self.get_specific_data(techInfoSection)

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

        browser.close()

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
            name_loc = page.locator("#container-purchase h1")

        name = name_loc.inner_text().strip()
        category = self.category.name.lower()
        price = self.get_price(priceSection)
        url = page.url
        img_url = page.locator("#carouselDetails img").first.get_attribute("src")
        brand = self.get_brand(techInfoSection)
        description = self.get_description(descriptionSection)
        rating = float(reviewsSection.locator("span").first.inner_text().strip())
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

    def get_specific_data(self, section: Locator) -> dict:  # noqa: PLR0911
        if self.category == Categories.MOTHERBOARD:
            return {
                "socket": "AM4/AM5/LGA1200",
                "model": self.get_model(section),
                "chipset": "AMD/NVIDIA",
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
                "vram": self.get_vram(section),
                "chipset": "AMD/NVIDIA",
                "max_resolution": "1920x1080",
                "output": "HDMI, DisplayPort",
                "tech_support": "DirectX 12, OpenGL 4.6",
            }

        if self.category == Categories.CPU:
            return {
                "model": self.get_model(section),
                "integrated_video": "Vega 8/12",
                "socket": "AM4/AM5/LGA1200",
                "core_number": "6/8/12",
                "thread_number": "12/16/24",
                "frequency": "3.0GHz",
                "mem_speed": "3200MHz",
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
        price_locator = section.locator("b.regularPrice")
        if not self.element_visible(price_locator):
            price_locator = section.locator("h4.finalPrice")

        price_raw = price_locator.first.inner_text()
        price_clean = re.sub(r"[^\d\.,]", "", price_raw)
        return (
            price_clean.replace(".", "").replace(",", ".") if price_clean else "Unknown"
        )

    def get_brand(self, section: Locator) -> str:
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
            return ""

        brand = re.search(r"Marca:\s*(.+)$", brand_name, flags=re.IGNORECASE)
        return brand.group(1) if brand else ""

    def get_description(self, section: Locator) -> str:
        """
        Retorna a descrição completa: título + parágrafo
        Suporta tanto o padrão <h3> + <p> quanto segunda <h2> + <p>.
        """
        skip_texts = {"Compre agora no KaBuM!"}

        heading = None
        h3s = section.locator("h3")
        for i in range(h3s.count()):
            h = h3s.nth(i)
            text = h.inner_text().strip()
            if text and text not in skip_texts:
                heading = h
                break

        if not heading:
            h2s = section.locator("h2")
            if h2s.count() > 1:
                heading = h2s.nth(1)
            else:
                return "No description available"

        title = heading.inner_text().strip()
        para_locator = heading.locator(
            "xpath=following-sibling::p[normalize-space()][1]",
        )
        try:
            paragraph = para_locator.first.inner_text(timeout=500).strip()
        except AttributeError:
            paragraph = ""

        return f"{title}\n\n{paragraph}"

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

    def get_vram(self, section: Locator) -> str:  # noqa: C901, PLR0911, PLR0912
        """
        Retorna VRAM no formato "8GB GDDR6", cobrindo ambos os layouts só com <p>:
          - vários <p> com "- Chave: Valor"
          - <p><span><strong>Memória</strong></span></p>
            <p><span>- GDDR6 16 GB</span></p>
          - <p>- Memória: 16 GB GDDR6</p>
        """

        # 1º método: procura por "Capacidade" ou "Tamanho" em <p> com "- Chave: Valor"
        # ex: <p>- Capacidade: 8 GB</p> ou <p>- Tamanho máximo da memória: 8 GB</p>
        vram = ""

        specs = {}
        paras = section.locator("p")
        for i in range(paras.count()):
            try:
                text = paras.nth(i).inner_text().strip()
                # limpa traço e espaços
                text = text.lstrip("- ").strip()
                if ":" not in text:
                    continue
                key, val = [s.strip() for s in text.split(":", 1)]
                specs[key] = val
            except AttributeError:
                vram = ""

        vram_size = (
            specs.get("Capacidade")
            or specs.get("Tamanho máximo da memória", "")
            or specs.get("Tamanho da memória", "")
        )
        if vram_size:
            vram_size = re.sub(r"\s+", "", vram_size)  # "8 GB" -> "8GB"

        vram_type = specs.get("Tipo") or specs.get("Tipo de memória", "")

        if vram_size or vram_type:
            return (
                f"{vram_size or ''}"
                f"{(' ' + vram_type) if vram_size and vram_type else vram_type or ''}"
            ).strip()

        # 2º método: procura por "Memória" em <p> com <strong>
        # ex: <p><strong>Memória</strong></p> <p>- GDDR6 16 GB</p>
        headings = section.locator("p:has(strong)").all()
        for p in headings:
            strong_txt = p.locator("strong").inner_text().strip().rstrip(":").lower()
            if (
                "memória" not in strong_txt
                or "relógio" in strong_txt
                or "velocidade" in strong_txt
            ):
                continue

            try:
                sib = p.locator(
                    "xpath=following-sibling::p[normalize-space()][1]",
                ).first
                vram_raw = sib.inner_text(timeout=500).strip()  # ex: "- 16 GB GDDR6"
                return vram_raw.lstrip("- ").strip()  # → "16 GB GDDR6"
            except AttributeError:
                vram = ""

        # 3º método: procura por "Memória" em <span> com "Memória:"
        # ex: <p><span>- Memória: 12 GB GDDR7</span></p>
        candidates = [
            "span:has-text('Memória')",
            "p:has-text('Memória')",
        ]

        for sel in candidates:
            locs = section.locator(sel)
            for i in range(locs.count()):
                try:
                    vram_raw = locs.nth(i).inner_text(timeout=500).strip()
                except AttributeError:
                    vram = ""
                # só prossegue se começar realmente com "- Memória:"
                vram_clean = vram_raw.lstrip(
                    "- ",
                ).strip()  # ex: "- Memória: 8 GB GDDR6"
                if re.match(r"^Memória:", vram_clean, flags=re.IGNORECASE):
                    vram = re.match(
                        r"Memória:\s*(.+)$",
                        vram_clean,
                        flags=re.IGNORECASE,
                    )
                    if vram:
                        return vram.group(1).strip()
                elif re.match(r"^Tamanho da Memória:", vram_clean, flags=re.IGNORECASE):
                    vram = re.match(
                        r"Tamanho da Memória:\s*(.+)$",
                        vram_clean,
                        flags=re.IGNORECASE,
                    )
                    if vram:
                        return vram.group(1).strip()
                elif re.match(
                    r"^Tamanho da memória/barramento:",
                    vram_clean,
                    flags=re.IGNORECASE,
                ):
                    vram = re.match(
                        r"Tamanho da memória/barramento:\s*(.+)$",
                        vram_clean,
                        flags=re.IGNORECASE,
                    )
                    if vram:
                        return vram.group(1).strip()
                elif re.match(r"^Tamanho da memória", vram_clean, flags=re.IGNORECASE):
                    vram = re.match(
                        r"Tamanho da memória\s*(.+)$",
                        vram_clean,
                        flags=re.IGNORECASE,
                    )
                    if vram:
                        return vram.group(1).strip()
                else:
                    continue

        return vram or ""


if __name__ == "__main__":
    # exemplo de uso
    scraper = KabumScraper(category=Categories.GPU, limit=5, local_results=True)
    resultados = scraper.run()
