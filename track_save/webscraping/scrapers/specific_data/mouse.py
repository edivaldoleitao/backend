import re

from playwright.sync_api import Locator


def get_dpi(section: Locator) -> str:
    """
    Retorna o DPI no formato "8000 DPI", "10000 DPI", etc.
    """
    loc = section.locator("text=/DPI:/i")
    if loc.count():
        txt = loc.first.inner_text().strip()
        cleaned = re.sub(r"^[-\s]*", "", txt)
        m = re.search(r"DPI:\s*(\d{1,3}(?:[.,]\d{1,3})?)", cleaned, flags=re.IGNORECASE)
        if m:
            # normaliza vírgula -> ponto e adiciona unidade
            return f"{m.group(1).replace(',', '.')} DPI"

    # fallback: varre todo o texto da seção e captura a primeira ocorrência "NNNN DPI"
    all_text = section.inner_text()
    m2 = re.search(
        r"\b(\d{1,3}(?:[.,]\d{1,3})?)\s*DPI\b",
        all_text,
        flags=re.IGNORECASE,
    )
    if m2:
        return f"{m2.group(1).replace(',', '.')} DPI"

    return ""


def get_connectivity(section: Locator) -> str:
    """
    Retorna a conectividade, ex: "USB", "USB-C", "Wireless", "Bluetooth", "Caboado" etc.
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
        r"\bUSB(?:-C)?\b|\bWireless\b|\bBluetooth\b|\bCaboado\b",
        all_text,
        flags=re.IGNORECASE,
    )
    # normaliza e deduplica mantendo a ordem
    seen = set()
    out = []
    for x in found:
        norm = x.upper().replace("CABOADO", "Caboado")  # só um exemplo de normalização
        if norm not in seen:
            seen.add(norm)
            out.append(norm)
    return " / ".join(out)


def get_color(section: Locator) -> str:
    """
    Retorna a cor, ex: "Preto", "RGB Redragon Chroma Mk.II" etc.
    """
    patterns = [
        r"Cor:",
        r"Color:",
    ]
    for pat in patterns:
        loc = section.locator(f"text=/{pat}/i")
        if not loc.count():
            continue
        txt = loc.first.inner_text().strip()
        cleaned = re.sub(r"^[-\s]*", "", txt)
        m = re.search(rf"{pat}\s*(.+)$", cleaned, flags=re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return ""
