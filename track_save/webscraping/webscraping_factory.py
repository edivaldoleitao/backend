from .scrapers.kabum import KabumScraper

# Lista de scrapers disponíveis
SCRAPERS = {
  "kabum": KabumScraper,
}

def get_scraper(name: str, **kwargs):
    """
    Retorna uma instância do scraper requisitado.
    kwargs serão passados para o construtor.
    """
    try:
      cls = SCRAPERS[name]
    except KeyError:
      raise ValueError(f"Scraper '{name}' não encontrado")
    return cls(**kwargs)