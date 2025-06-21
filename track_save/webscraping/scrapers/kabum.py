from .scraper import Scraper

class KabumScraper(Scraper):

  def __init__(self, query: str):
    self.query = query

  def run(self) -> list[dict]:
    results = []
    playwright, browser, page = self.init_browser()
    page.goto("https://www.kabum.com.br/")

    locInputBusca = page.locator("#inputBusca")
    self.wait_element(locInputBusca)
    locInputBusca.fill(self.query)
    locInputBusca.press("Enter")

    locBarraFiltro = page.locator("#Filter")
    locFiltroItens = locBarraFiltro.locator("select.sc-dcf1314f-0")
    self.wait_element(locFiltroItens)

    locFiltroItens.select_option(value="100")

    locItens = page.locator("article.productCard")
    self.wait_element(locItens)

    #for i in range(locItens.count()):
    for i in range(3):
      locItem = locItens.nth(i)
      locNome   = locItem.locator("span.nameCard")
      locPreco  = locItem.locator("span.priceCard")
      locLink   = locItem.locator("a")
      locImgURL = locItem.locator("img")

      if self.element_visible(locNome) and self.element_visible(locPreco) and self.element_visible(locLink):
        nome = locNome.inner_text().strip()
        preco = locPreco.inner_text().strip()
        link_href = locLink.get_attribute("href") if locLink.count() > 0 else ""
        link = link_href.strip() if link_href else ""
        img_src = locImgURL.get_attribute("src") if locImgURL.count() > 0 else ""
        img_url = img_src.strip() if img_src else ""

        results.append({
        "nome": nome,
        "preco": preco,
        "link": link,
        "img_url": img_url
        })

    browser.close()
    return results

if __name__ == "__main__":
  # exemplo de uso
  q = "placa de vídeo"
  scraper = KabumScraper(q)
  resultados = scraper.run()
  print(resultados)
