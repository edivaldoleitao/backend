import re

from playwright.sync_api import Locator


def get_capacity(section: Locator) -> str:
    """
    Extrai a capacidade da memória RAM, como "16GB".
    Busca por padrões como "Capacidade: 16GB (1x 16GB)" ou apenas "16GB".
    """
    section_text = section.inner_text()

    # 1. Extração direta, focando no valor principal (ex: 16GB)
    capacity_match = re.search(r"Capacidade:\s*(\d+GB)", section_text, re.IGNORECASE)
    if capacity_match:
        return capacity_match.group(1)

    # 2. Fallback: procura pelo primeiro padrão "XXGB" no texto
    fallback_match = re.search(r"\b(\d+GB)\b", section_text, re.IGNORECASE)
    if fallback_match:
        return fallback_match.group(1)

    return ""


def get_ddr(section: Locator) -> str:
    """
    Extrai o tipo de memória, como "DDR5".
    Busca por padrões como "Tipo de memória: DDR5" ou apenas "DDR5".
    """
    section_text = section.inner_text()

    # 1. Extração direta
    ddr_match = re.search(r"Tipo de memória:\s*(DDR[345])", section_text, re.IGNORECASE)
    if ddr_match:
        return ddr_match.group(1)

    # 2. Fallback: procura pelo padrão DDRx no texto
    fallback_match = re.search(r"\b(DDR[345])\b", section_text, re.IGNORECASE)
    if fallback_match:
        return fallback_match.group(1)

    return ""


def get_speed(section: Locator) -> str:
    """
    Extrai a velocidade da memória, como "4800MHz".
    Busca por "Velocidade: 4800 Mhz" e tem fallback para outros padrões.
    4800MT/s
    DDR5-5200
    """
    section_text = section.inner_text()

    # 1. Extração direta, priorizando a linha "Velocidade:"
    speed_match = re.search(r"Velocidade:\s*(\d+\s*MHz)", section_text, re.IGNORECASE)
    if speed_match:
        # Normaliza o resultado para "XXXXMHz" (sem espaço)
        return speed_match.group(1).replace(" ", "")

    # 2. Fallback: procura por qualquer número de 4+ dígitos seguido de "MHz"
    fallback_match = re.search(r"(\d{4,})\s*MHz", section_text, re.IGNORECASE)
    if fallback_match:
        return f"{fallback_match.group(1)}MHz"

    # 3. Fallback adicional: procura por padrões como "4800MT/s" ou "DDR5-5200"
    mt_match = re.search(r"(\d{4,})\s*MT/s", section_text, re.IGNORECASE)
    if mt_match:
        return f"{mt_match.group(1)}MT/s"

    ddr_match = re.search(r"DDR[345]-(\d{4,})", section_text, re.IGNORECASE)
    if ddr_match:
        return f"{ddr_match.group(1)}MHz"

    return ""
