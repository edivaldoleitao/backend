import re
import unicodedata

from playwright.sync_api import Locator


def get_vram(section: Locator) -> str:  # noqa: C901, PLR0911, PLR0912
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


def get_chipset(name: str) -> str:
    """
    Retorna o chipset da GPU, que pode ser AMD ou NVIDIA.
    """
    # Exemplo de texto: "Chipset: NVIDIA GeForce RTX 3060"
    if "NVIDIA" in name or "GeForce" in name or "RTX" in name or "GTX" in name:
        return "NVIDIA"
    if "AMD" in name or "Radeon" in name or "RX" in name or "Vega" in name:
        return "AMD"
    return "Desconhecido"


def normalize_key(s: str) -> str:
    # tira acentos, coloca em lowercase e remove espaços extras
    nf = unicodedata.normalize("NFKD", s)
    no_accents = "".join(c for c in nf if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", no_accents).strip().lower()


def get_max_resolution(section: Locator) -> str:
    """
    Retorna a resolução máxima no formato "7680 x 4320".
    Procura em parágrafos "Chave: Valor" e, se falhar, faz regex genérico.
    """
    specs = {}
    paras = section.locator("p")
    for i in range(paras.count()):
        text = paras.nth(i).inner_text().strip()
        text = text.lstrip("- ").strip()
        if ":" not in text:
            continue
        key, val = [part.strip() for part in text.split(":", 1)]
        specs[normalize_key(key)] = val

    # aliases de chave que queremos capturar
    aliases = [
        "resolucao maxima digital",
        "resolucao digital maxima",
        "resolucao maxima",
        "resolucao",
    ]

    for alias in aliases:
        val = specs.get(alias, "").strip()
        if val:
            # só retorna se realmente tiver algo depois dos dois-pontos
            return re.sub(r"\s*x\s*", " x ", val).strip()

    # fallback: busca qualquer "1234 x 5678" no texto completo
    full = section.inner_text()
    m = re.search(r"(\d{3,4})\s*[x×]\s*(\d{3,4})", full)
    if m:
        return f"{m.group(1)} x {m.group(2)}"

    return ""


def get_output(section: Locator) -> str:
    """
    Retorna todas as saídas de vídeo da GPU,
    ex: "HDMI, DisplayPort, DVI".
    """
    text = section.inner_text().lower()
    candidates = ["HDMI", "DisplayPort", "VGA", "DVI"]
    found = [c for c in candidates if c.lower() in text]
    return ", ".join(found)


def get_tech_support(section: Locator) -> str:
    """
    Retorna todos os suportes técnicos detectados na GPU,
    ex: "DLSS, Ray Tracing, FreeSync".
    """
    text = section.inner_text().lower()
    SUPPORT_MAP = {
        "dlss": "DLSS",
        "ray tracing": "Ray Tracing",
        "vulkan": "Vulkan",
        "freesync": "FreeSync",
        "g-sync": "G-Sync",
        "opencl": "OpenCL",
        "opengl": "OpenGL",
        "directx": "DirectX",
    }
    found = [pretty for key, pretty in SUPPORT_MAP.items() if key in text]
    return ", ".join(found)
