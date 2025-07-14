import re

from playwright.sync_api import Locator


def get_key_type(section: Locator, product_name: str) -> str:  # noqa: C901
    """
    Retorna o tipo de tecla. Se for mecânico, tenta identificar o switch.
    Possui fallbacks para buscar no texto e no nome do produto.
    Ex: "Mecânico, Switch: Gateron G Pro 3.0 Brown", "Mecânico", "Membrana".
    """
    section_text = section.inner_text()
    key_type = ""
    switch_info = ""

    # 1. Extração direta
    direct_match = re.search(r"Tipo de Tecla:\s*(\w+)", section_text, re.IGNORECASE)
    if direct_match:
        key_type = direct_match.group(1).strip()

    if re.search(r"\bMecânico\b", section_text, re.IGNORECASE):
        key_type = "Mecânico"

    # 2. Fallback: procurar por palavras-chave no texto da seção
    if not key_type:
        known_types = ["Mecânico", "Membrana", "Óptico"]
        for t in known_types:
            if re.search(rf"\b{t}\b", section_text, re.IGNORECASE):
                key_type = t
                break

    # 3. Fallback: procurar por palavras-chave no nome do produto
    if not key_type:
        known_types = ["Mecânico", "Membrana", "Óptico"]
        for t in known_types:
            if re.search(rf"\b{t}\b", product_name, re.IGNORECASE):
                key_type = t
                break

    # Tenta encontrar a informação do switch independentemente
    switch_match = re.search(r"Switch:\s*([^\n\r<]+)", section_text, re.IGNORECASE)
    if switch_match:
        # Se tem switch, garante que o tipo da tecla seja "Mecânico"
        key_type = "Mecânico"
        switch_info = switch_match.group(1).strip()

    if key_type and switch_info:
        return f"{key_type}, Switch: {switch_info}"

    return key_type


def get_layout(section: Locator) -> str:
    """
    Retorna o layout, extraindo o padrão principal (ex: ABNT2, ANSI).
    Possui fallback para buscar padrões conhecidos no texto.
    """
    section_text = section.inner_text()

    # 1. Extração direta
    layout_match = re.search(r"Layout:\s*([^\s,]+)", section_text, re.IGNORECASE)
    if layout_match:
        return layout_match.group(1).strip()

    # 2. Fallback: procurar por padrões conhecidos no texto
    known_layouts_pattern = r"\b(ABNT2|ABNT|ANSI|US)\b"
    fallback_match = re.search(known_layouts_pattern, section_text, re.IGNORECASE)
    if fallback_match:
        return fallback_match.group(1).upper()

    return ""


def get_connectivity(section: Locator) -> str:
    """
    Retorna a conectividade, ex: "USB", "USB-C", "Wireless", "Bluetooth", "Cabeado" etc.
    """
    loc = section.locator("text=/Conectividade:|Connectivity:/i")
    if loc.count():
        txt = loc.first.inner_text().strip()
        cleaned = re.sub(r"^[-\s]*", "", txt)
        m = re.search(
            r"(?:Conectividade|Connectivity):\s*(.+)$",
            cleaned,
            flags=re.IGNORECASE,
        )
        if m:
            return m.group(1).strip()

    # fallback: pega todos os matches no texto e junta com " / "
    all_text = section.inner_text()
    found = re.findall(
        r"\bUSB(?:-C)?\b|\bWireless\b|\bBluetooth\b|\bCabeado\b",
        all_text,
        flags=re.IGNORECASE,
    )
    # normaliza e deduplica mantendo a ordem
    seen = set()
    out = []
    for x in found:
        norm = x.upper().replace("CABEADO", "Cabeado")  # só um exemplo de normalização
        if norm not in seen:
            seen.add(norm)
            out.append(norm)
    return " / ".join(out)


def get_dimension(section: Locator) -> str:
    """
    Retorna a dimensão, priorizando a junção de Comprimento, Largura e Altura.
    Ex: "153 mm x 360,5 mm x 34,3 mm" ou "292 x 102 x 39 mm".
    """
    section_text = section.inner_text()

    # 1. Padrão prioritário: busca por Comprimento, Largura e Altura separados
    comprimento_match = re.search(
        r"Comprimento:\s*([^\n\r<]+)",
        section_text,
        re.IGNORECASE,
    )
    largura_match = re.search(r"Largura:\s*([^\n\r<]+)", section_text, re.IGNORECASE)
    altura_match = re.search(r"Altura:\s*([^\n\r<]+)", section_text, re.IGNORECASE)

    if comprimento_match and largura_match and altura_match:
        comprimento = comprimento_match.group(1).strip()
        largura = largura_match.group(1).strip()
        altura = altura_match.group(1).strip()
        return f"{comprimento} x {largura} x {altura}"

    # 2. Fallback: busca por "Dimensões:" seguido de um valor
    dimension_match = re.search(
        r"Dimensões(?: do Teclado)?:\s*([^\n\r<]+)",
        section_text,
        re.IGNORECASE,
    )
    if dimension_match:
        return dimension_match.group(1).strip()

    # 3. Fallback: busca por um padrão numérico como "123 x 45 x 67 mm"
    dimension_pattern = (
        r"\b(\d{1,4}(?:,\d)?\s*x\s*\d{1,4}(?:,\d)?\s*x\s*\d{1,4}(?:,\d)?\s*mm)\b"
    )
    fallback_match = re.search(dimension_pattern, section_text, re.IGNORECASE)
    if fallback_match:
        return fallback_match.group(1).strip()

    return ""
