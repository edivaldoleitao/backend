from .scrapers.kabum import KabumScraper

# Lista de scrapers disponíveis
SCRAPERS = {
    "kabum": KabumScraper,
}


def get_scraper(store: str, **kwargs):
    """
    Retorna uma instância do scraper requisitado.
    kwargs serão passados para o construtor.
    """
    try:
        cls = SCRAPERS[store]
    except KeyError as err:
        msg = f"Scraper '{store}' não encontrado"
        raise ValueError(msg) from err
    return cls(**kwargs)
