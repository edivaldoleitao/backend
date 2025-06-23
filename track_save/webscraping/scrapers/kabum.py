from .scraper import Scraper
from ..enums import Categories
from playwright.sync_api import Page, Locator
import re

class KabumScraper(Scraper):

  def __init__(self, category: Categories):
    self.category = category

  def run(self) -> list[dict]:
    results = []
    playwright, browser, page = self.init_browser()
    page.goto("https://www.kabum.com.br/")

    locInputBusca = page.locator("#inputBusca")
    self.wait_element(locInputBusca)

    query = self.parse_category(self.category, is_query=True)
    locInputBusca.fill(query)
    locInputBusca.press("Enter")

    locBarraFiltro = page.locator("#Filter")
    locFiltroItens = locBarraFiltro.locator("select.sc-dcf1314f-0")
    self.wait_element(locFiltroItens)

    locFiltroItens.select_option(value="100")

    locItens = page.locator("article.productCard")
    self.wait_element(locItens)

    for i in range(locItens.count()):
      card = locItens.nth(i)

      card.click()

      descriptionSection = page.locator("#description")
      techInfoSection    = page.locator("#technicalInfoSection")
      self.wait_elements(page, [descriptionSection, techInfoSection])

      common_data   = self.get_common_data(page, descriptionSection, techInfoSection)
      specific_info = self.get_specific_data(techInfoSection)

      product_data = {
        **common_data,
        "specific_info": specific_info
      }

      results.append(product_data)

      page.go_back()

    browser.close()
    return results

  def get_common_data(self, page: Page, descriptionSection: Locator, techInfoSection: Locator) -> dict:
    price_raw   = page.locator("#blocoValores b.regularPrice").first.inner_text()
    price_clean = re.sub(r"[^\d\.,]", "", price_raw)

    brand_name = techInfoSection.locator("span:has-text('Marca')").first.inner_text()
    brand      = re.search(r"Marca:\s*(.+)$", brand_name)

    desc_title     = descriptionSection.locator("h3").first.inner_text()
    desc_paragraph = descriptionSection.locator("h3 + p").first.inner_text().strip()

    name  = descriptionSection.locator("h2").first.inner_text()
    price = price_clean.replace(".", "").replace(",", ".")
    url  = page.url
    img_url = page.locator("#carouselDetails img").first.get_attribute("src")
    brand = brand.group(1) if brand else ""
    description = f"{desc_title}\n\n{desc_paragraph}"

    return {
      "name": name,
      "price": price,
      "url": url,
      "img_url": img_url,
      "brand": brand,
      "description": description
    }

  def get_specific_data(self, section: Locator) -> dict:
    if self.category == Categories.GPU:
      model_name = section.locator("span:has-text('Modelo')").first.inner_text()
      model      = re.search(r"Modelo:\s*(.+)$", model_name)

    #   vram_info = section.locator("span:has-text('Tamanho máximo da memória')").first.inner_text()
    #   vram      = re.search(r"Tamanho máximo da memória:\s*(.+)$", vram_info)

      # COMPLEMENTAR COM OUTRAS INFORMAÇÕES ESPECÍFICAS

      specific_info = {
        "model": model.group(1) if model else "",
        "vram": "8GB GDDR6",
        "chipset": "AMD",
        "max_resolution": "1920x1080",
        "output": "HDMI, DisplayPort",
        "tech_support": "DirectX 12, OpenGL 4.6",
      }

      return specific_info

    else:
      return {}

if __name__ == "__main__":
  # exemplo de uso
  scraper = KabumScraper(category=Categories.GPU)
  resultados = scraper.run()
  print(resultados)
