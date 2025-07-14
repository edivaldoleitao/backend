import re

from playwright.sync_api import Locator


def get_integrated_video(section: Locator) -> str:  # noqa: C901
    """
    Retorna Integrated Video no formato "Intel® UHD Graphics 770"
    """
    integrated_video = ""

    # 1º método: procura por "Gráficos" em <p> com <strong>
    # ex: <p><strong>Gráficos</strong></p> <p>- GDDR6 16 GB</p>
    headings = section.locator("p:has(strong:has-text('Gráficos'))").all()
    for p in headings:
        strong_txt = p.locator("strong").inner_text().strip().rstrip(":").lower()
        if (
            "gráficos" not in strong_txt
            # or "relógio" in strong_txt
            # or "velocidade" in strong_txt
        ):
            continue

        try:
            sib = p.locator(
                "xpath=following-sibling::p[normalize-space()][1]",
            ).first
            integrated_video_raw = sib.inner_text(
                timeout=500,
            ).strip()  # ex: "- 16 GB GDDR6"
            return integrated_video_raw.lstrip("- ").strip()  # → "16 GB GDDR6"
        except AttributeError:
            integrated_video = ""

    # 2º método: procura por "Gráficos do processador" em <span> ou <p>
    # ex: <p>- Gráficos do processador ‡: Intel® UHD Graphics 770</p>
    candidates = [
        "span:has-text('Gráficos do processador')",
        "p:has-text('Gráficos do processador')",
    ]

    for sel in candidates:
        locs = section.locator(sel)
        for i in range(locs.count()):
            try:
                integrated_video_raw = locs.nth(i).inner_text(timeout=500).strip()
            except AttributeError:
                integrated_video = ""
            # só prossegue se começar realmente com "- Gráficos do processador:"
            integrated_video_clean = integrated_video_raw.lstrip(
                "- ",
            ).strip()  # ex: "- Gráficos do processador‡: Intel® UHD Graphics 770"
            if re.match(
                r"^Gráficos do processador:",
                integrated_video_clean,
                flags=re.IGNORECASE,
            ):
                integrated_video = re.match(
                    r"Gráficos do processador:\s*(.+)$",
                    integrated_video_clean,
                    flags=re.IGNORECASE,
                )
                if integrated_video:
                    return integrated_video.group(1).strip()
            elif re.match(
                r"^Gráficos do processador ‡:",
                integrated_video_clean,
                flags=re.IGNORECASE,
            ):
                integrated_video = re.match(
                    r"Gráficos do processador ‡:\s*(.+)$",
                    integrated_video_clean,
                    flags=re.IGNORECASE,
                )
                if integrated_video:
                    return integrated_video.group(1).strip()
            else:
                continue

    return integrated_video or ""


def get_socket(section: Locator) -> str:
    """
    Retorna o socket no formato "LGA1200", "1700", "AM4", etc.
    """
    # padrões de label que devem ser capturados
    patterns = [
        r"Socket:",
        r"Soquete:",
        r"Soquetes suportados:",
        r"Pacote:",
        r"Soquete da CPU:",
    ]

    for pat in patterns:
        # usa text=/…/i para casar qualquer linha que comece com o label
        loc = section.locator(f"text=/{pat}/i")
        if not loc.count():
            continue
        txt = loc.first.inner_text().strip()
        # remove prefixos tipo "-" ou espaços
        cleaned = re.sub(r"^[-\s]*", "", txt)
        # captura tudo após ":"
        m = re.search(r":\s*(.+)$", cleaned)
        if m:
            return m.group(1).strip()

    return ""


def get_core_number(section: Locator) -> str:
    """
    Retorna o número de núcleos no formato:
    - "20"
    - "10 (6P+4E)"
    etc.
    """
    patterns = [
        r"N[úu]cleos do processador\s*\(P-cores \+ E-cores\):",
        r"N[úu]cleos:",
        r"Número de núcleos:",
        r"Nº de núcleos de CPU:",
    ]

    for pat in patterns:
        loc = section.locator(f"text=/{pat}/i")
        if not loc.count():
            continue
        txt = loc.first.inner_text().strip()
        # limpa o "-", espaços, quebras de linha…
        cleaned = re.sub(r"^[-\s]*", "", txt)
        # extrai tudo que vier depois do “:”
        m = re.search(r":\s*(.+)$", cleaned)
        if m:
            return m.group(1).strip()
    return ""


def get_threads(section: Locator) -> str:
    """
    Retorna o número de threads no formato:
    - "16"
    - "28"
    etc.
    """
    patterns = [
        r"Threads do processador:",
        r"Threads:",
        r"Número de threads:",
        r"Nº de threads:",
    ]

    for pat in patterns:
        loc = section.locator(f"text=/{pat}/i")
        if not loc.count():
            continue
        txt = loc.first.inner_text().strip()
        cleaned = re.sub(r"^[-\s]*", "", txt)
        m = re.search(r":\s*(\d+)", cleaned)
        if m:
            return m.group(1)
    return ""


def get_frequency(section: Locator, name: str) -> str:
    frequency = ""

    # 1) tente achar no HTML alguma linha que fale de "base" ou "básico"
    patterns = [
        r"Frequ[eê]ncia de base[:\s–-]*([\d,]+\s*GHz)",
        r"Frequ[eê]ncia base[:\s–-]*([\d,]+\s*GHz)",
        r"Rel[oó]gio b[aá]sico[:\s–-]*([\d,]+\s*GHz)",
    ]
    for pat in patterns:
        # usar o text selector com regex para encontrar o parágrafo inteiro
        loc = section.locator(f"text=/{pat}/i")
        if loc.count():
            txt = loc.first.inner_text().strip()
            m = re.search(pat, txt, flags=re.IGNORECASE)
            if m:
                # normaliza vírgula para ponto e retorna só o número + unidade
                frequency = m.group(1).replace(",", ".")

    # Se não encontrar na descrição, tenta achar no nome do produto
    m = re.search(
        r"(\d+[.,]?\d*)\s*[-–—]\s*\d+[.,]?\d*\s*GHz",
        name,
        flags=re.IGNORECASE,
    )
    if m:
        frequency = m.group(1).replace(",", ".") + " GHz"
    # ou, se for só "3.6GHz" lá no nome
    m2 = re.search(r"(\d+[.,]?\d*)\s*GHz", name, flags=re.IGNORECASE)
    if m2:
        frequency = m2.group(1).replace(",", ".") + " GHz"

    # se não encontrar no bloco
    return frequency or ""


def get_mem_speed(section: Locator) -> str:
    """
    Extrai todas as velocidades de memória (DDR4 e DDR5)
    de dentro da seção técnica, seja num parágrafo com <br>
    ou em vários <p> abaixo de um <strong>.
    Retorna algo como "DDR5 4800 | DDR4 3200 | DDR4 2933 | DDR4 2667"
    """
    text = section.inner_text().strip()

    raw = re.findall(
        r"(DDR[45])[-\s]?(\d{3,4})(?:\s*MT/s)?",
        text,
        flags=re.IGNORECASE,
    )

    seen = set()
    out = []
    for mod, freq in raw:
        speed = f"{mod.upper()} {freq}"
        if speed not in seen:
            seen.add(speed)
            out.append(speed)

    return " | ".join(out)
