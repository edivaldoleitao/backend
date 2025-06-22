from .scraper import Scraper
from playwright.sync_api import Page, Locator
import re

class KabumScraper(Scraper):

  def __init__(self, category: str):
    self.category = category

  def run(self) -> list[dict]:
    results = []
    playwright, browser, page = self.init_browser()
    page.goto("https://www.kabum.com.br/")

    locInputBusca = page.locator("#inputBusca")
    self.wait_element(locInputBusca)
    locInputBusca.fill(self.category)
    locInputBusca.press("Enter")

    locBarraFiltro = page.locator("#Filter")
    locFiltroItens = locBarraFiltro.locator("select.sc-dcf1314f-0")
    self.wait_element(locFiltroItens)

    locFiltroItens.select_option(value="100")

    locItens = page.locator("article.productCard")
    self.wait_element(locItens)

    # for i in range(locItens.count()):
    for i in range(2):
      card = locItens.nth(i)

      card.click()

      descriptionSection = page.locator("#description")
      techInfoSection    = page.locator("#technicalInfoSection")
      self.wait_elements(page, [descriptionSection, techInfoSection])

      common_data = self.get_common_data(page, descriptionSection, techInfoSection)

      product_data = {
        **common_data,
        "specific_info": {}
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

if __name__ == "__main__":
  # exemplo de uso
  q = "placa de vídeo"
  scraper = KabumScraper(q)
  resultados = scraper.run()
  print(resultados)
