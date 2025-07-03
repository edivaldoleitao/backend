import asyncio
import json
import os
import time
import urllib.parse

from playwright.async_api import async_playwright

AMAZON = "https://www.amazon.com.br/s?k="
OUTPUT_DIR = "resultados_amazon"
OUTPUT_DIR_TERA = "resultados_terabyte"
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR_TERA, exist_ok=True)


produtos_terabyte = {
    "teclado": "perifericos/teclado",
    "mouse_gamer": "perifericos/mouse",
    "monitor": "monitores",
    "placa_de_video": "hardware/placas-de-video",
    "processador_intel_amd": "hardware/processadores",
}


async def scrape_terabyte(termo_pesquisa):
    async with async_playwright() as p:
        # Configuração do navegador
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36",
        )

        page = await context.new_page()

        try:
            # Acessa o site
            print("🛒 Acessando Terabyte Shop...")
            await page.goto(
                f"https://www.terabyteshop.com.br/{termo_pesquisa}", timeout=60000
            )

            # Aguarda carregamento dos produtos
            print("⏳ Aguardando carregamento dos produtos...")
            await page.wait_for_selector(".product-item__box", timeout=30000)

            # Rola a página para carregar todos os produtos
            print("🔄 Rolando página para carregar mais produtos...")
            await page.evaluate("""
                window.scrollTo(0, document.body.scrollHeight);
                setTimeout(() => window.scrollTo(0, 0), 500);
            """)
            await asyncio.sleep(2)

            # Coleta os produtos
            print("🔍 Coletando dados dos produtos...")
            produtos = []
            items = await page.query_selector_all(".product-item__box")

            print(f"✅ Encontrados {len(items)} produtos na página inicial")

            # Processa cada produto
            for item in items:
                try:
                    # Nome do produto
                    nome_element = await item.query_selector(".product-item__name h2")
                    nome = await nome_element.inner_text() if nome_element else "N/A"

                    # Preço normal
                    preco_element = await item.query_selector(
                        ".product-item__new-price span"
                    )
                    preco = await preco_element.inner_text() if preco_element else "N/A"

                    # URL do produto
                    url_element = await item.query_selector("a.product-item__name")
                    url = (
                        await url_element.get_attribute("href")
                        if url_element
                        else "N/A"
                    )

                    # Extrai o SKU da URL
                    sku = "N/A"
                    if url and "product/" in url:
                        try:
                            sku = url.split("/product/")[1].split("/")[0]
                        except:
                            pass

                    # Verifica se tem promoção
                    promo_element = await item.query_selector(".product-item__labels")
                    promocao = "Sim" if promo_element else "Não"

                    produtos.append(
                        {
                            "sku": sku,
                            "nome": nome.strip(),
                            "preco": preco.strip(),
                            "url": url,
                            "promocao": promocao,
                        }
                    )
                except Exception as e:
                    print(f"⚠️ Erro em um produto: {str(e)}")
                    continue

            # Salva os resultados
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            if "/" in termo_pesquisa:
                termo_pesquisa = termo_pesquisa.split("/")[1]
            filename = f"terabyte_produtos_{timestamp}_{termo_pesquisa}.json"

            output_path = os.path.join(OUTPUT_DIR_TERA, filename)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(produtos, f, ensure_ascii=False, indent=2)

            print(f"\n✅ Sucesso! {len(produtos)} produtos salvos em '{filename}'")

            return filename

        except Exception as e:
            print(f"\n❌ Erro durante scraping: {str(e)}")
            return None

        finally:
            await browser.close()


async def scrape_amazon(url: str):
    produtos = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url)

        items = await page.query_selector_all("a.s-no-outline")

        for i, item in enumerate(items):
            href = await item.get_attribute("href")
            nome = await item.query_selector("img")
            nome_texto = await nome.get_attribute("alt") if nome else ""

            preco_span = await page.query_selector_all("span.a-price span.a-offscreen")
            nota_span = await page.query_selector_all("span.a-icon-alt")

            preco = await preco_span[i].inner_text() if i < len(preco_span) else ""
            nota = await nota_span[i].inner_text() if i < len(nota_span) else ""

            produtos.append(
                {
                    "url": "https://www.amazon.com.br" + href if href else "",
                    "name": nome_texto,
                    "price": preco,
                    "rating": nota[:3] if nota else "",
                }
            )

        await browser.close()
    return produtos


lista_produtos = [
    "teclado",
    "mouse_gamer",
    "monitor",
    "placa_de_video",
    "processador_intel_amd",
]


def montar_url(termo_pesquisa):
    return urllib.parse.quote(termo_pesquisa, safe="")


lista_produtos_amazon = []


async def search():
    todos_amazon = []
    for termo in lista_produtos:
        for page in range(1, 11):
            url = f"{AMAZON}{montar_url(termo)}&page={page}"
            print(f"[+] Buscando: {url}")
            resultados = await scrape_amazon(url)
            if resultados:
                todos_amazon.extend(resultados)
            await asyncio.sleep(1)

        if todos_amazon:
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            filename = f"amazon_{termo}_{timestamp}.json"
            path = os.path.join(OUTPUT_DIR, filename)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(todos_amazon, f, ensure_ascii=False, indent=2)
            print(f"✅ Amazon: {len(todos_amazon)} produtos salvos em {filename}")
            todos_amazon.clear()
        await scrape_terabyte(produtos_terabyte[termo])


if __name__ == "__main__":
    asyncio.run(search())
