import asyncio
import json
import os
import re
import time
import urllib.parse

from playwright.async_api import async_playwright

AMAZON = "https://www.amazon.com.br/s?k="
OUTPUT_DIR = "resultados_amazon"
OUTPUT_DIR_TERA = "resultados_terabyte"
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR_TERA, exist_ok=True)

banco_produtos_terabyte = []
banco_produtos_amazon = []

produtos_terabyte = {
    "teclado": "perifericos/teclado",
    "mouse_gamer": "perifericos/mouse",
    "monitor": "monitores",
    "placa_de_video": "hardware/placas-de-video",
    "processador_intel_amd": "hardware/processadores",
}


async def scrape_terabyte(termo_pesquisa):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36",
        )
        page = await context.new_page()

        try:
            print("🛒 Acessando Terabyte Shop...")
            await page.goto(
                f"https://www.terabyteshop.com.br/{termo_pesquisa}", timeout=60000
            )

            print("⏳ Aguardando carregamento dos produtos...")
            await page.wait_for_selector(".product-item__box", timeout=30000)

            print("🔄 Rolando página para carregar mais produtos...")
            await page.evaluate("""
                window.scrollTo(0, document.body.scrollHeight);
                setTimeout(() => window.scrollTo(0, 0), 500);
            """)
            await asyncio.sleep(2)

            print("🔍 Coletando dados dos produtos...")
            produtos = []
            items = await page.query_selector_all(".product-item__box")
            print(f"✅ Encontrados {len(items)} produtos na página inicial")

            for item in items:
                try:
                    nome_element = await item.query_selector(".product-item__name h2")
                    nome = await nome_element.inner_text() if nome_element else "N/A"

                    preco_element = await item.query_selector(
                        ".product-item__new-price span"
                    )
                    preco = await preco_element.inner_text() if preco_element else "N/A"

                    url_element = await item.query_selector("a.product-item__name")
                    url = (
                        await url_element.get_attribute("href")
                        if url_element
                        else "N/A"
                    )

                    sku = "N/A"
                    if url and "produto/" in url:
                        try:
                            sku = url.split("/produto/")[1].split("/")[0]
                        except:
                            pass

                    promo_element = await item.query_selector(".product-item__labels")
                    promocao = "Sim" if promo_element else "Não"

                    if url and not url.startswith("http"):
                        url = "https://www.terabyteshop.com.br" + url
                    if preco.strip() != "N/A":
                        produtos.append(
                            {
                                "sku": sku,
                                "nome": nome.strip(),
                                "preco": preco.strip(),
                                "url": url if url else "N/A",
                                "promocao": promocao,
                                "tipo_produto": termo_pesquisa,
                            }
                        )
                except Exception as e:
                    print(f"⚠️ Erro em um produto: {str(e)}")
                    continue

            banco_produtos_terabyte.extend(produtos)

            if "/" in termo_pesquisa:
                termo_pesquisa = termo_pesquisa.split("/")[1]
            filename = f"terabyte_produtos_{termo_pesquisa}.json"
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


async def scrape_amazon(url: str, termo):
    produtos = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url)

        items = await page.query_selector_all("a.s-no-outline")

        for item in items:
            href = await item.get_attribute("href")
            nome = await item.query_selector("img")
            nome_texto = await nome.get_attribute("alt") if nome else ""

            preco_element = await item.query_selector("span.a-price span.a-offscreen")
            preco = await preco_element.inner_text() if preco_element else ""

            nota_element = await item.query_selector("span.a-icon-alt")
            nota = await nota_element.inner_text() if nota_element else ""
            if "cooler" not in nome_texto.lower() and "captura" not in nome_texto.lower() and "suporte" not in nome_texto.lower():
                produtos.append(
                    {
                        "url": "https://www.amazon.com.br" + href if href else "",
                        "name": nome_texto,
                        "price": preco,
                        "rating": nota[:3] if nota else "",
                        "tipo_produto": termo,
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


async def search():
    todos_amazon = []
    for termo in lista_produtos:
        for page_num in range(1, 3):
            url = f"{AMAZON}{montar_url(termo)}&page={page_num}"
            print(f"[+] Buscando: {url}")
            resultados = await scrape_amazon(url,termo)
            if resultados:
                todos_amazon.extend(resultados)
            await asyncio.sleep(1)

        if todos_amazon:
            filename = f"amazon_{termo}.json"
            path = os.path.join(OUTPUT_DIR, filename)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(todos_amazon, f, ensure_ascii=False, indent=2)
            print(f"✅ Amazon: {len(todos_amazon)} produtos salvos em {filename}")
            banco_produtos_amazon.extend(todos_amazon)
            todos_amazon.clear()

        await scrape_terabyte(produtos_terabyte[termo])


async def scrape_amazon_product(url, termo):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url)

        # 1) Botão "Continuar comprando"
        try:
            continuar_btn = page.locator("button.a-button-text", has_text="Continuar comprando")
            if await continuar_btn.is_visible():
                await continuar_btn.click()
                await page.wait_for_timeout(1000)
        except Exception:
            pass

        # 2) Expande todas as seções colapsáveis (Características, Especificações etc.)
        try:
            expanders = page.locator("a.a-expander-header")
            count = await expanders.count()
            for i in range(count):
                expander = expanders.nth(i)
                if await expander.is_visible():
                    aria = await expander.get_attribute("aria-expanded")
                    if aria in (None, "false"):
                        await expander.click()
                        await page.wait_for_timeout(500)
        except Exception:
            pass

        # 3) Título
        try:
            await page.wait_for_selector("#productTitle", timeout=15000)
            nome = (await page.locator("#productTitle").inner_text()).strip()
        except Exception:
            nome = ""

        # 4) Preço
        try:
            preco = await page.locator(".a-price .a-offscreen").first.inner_text()
        except Exception:
            preco = "Preço não encontrado"

        # 5) Nota
        try:
            nota = await page.locator("span.a-icon-alt").first.inner_text()
        except Exception:
            nota = "Sem nota"

        # 6) Descrição curta
        try:
            descricao_curta = await page.locator("#feature-bullets").inner_text()
        except Exception:
            descricao_curta = "Descrição curta não encontrada"

        # 7) Descrição detalhada
        try:
            descricao_detalhada = await page.locator("#productDescription").inner_text()
        except Exception:
            descricao_detalhada = "Descrição detalhada não encontrada"

        # 8) Descrição técnica (Especificações Técnicas)
        try:
            descricao_tecnica = {}
            tech_rows = page.locator("table#productDetails_techSpec_section_1 tr")
            tech_count = await tech_rows.count()
            for i in range(tech_count):
                key = (await tech_rows.nth(i).locator("th").inner_text()).strip()
                val = (await tech_rows.nth(i).locator("td").inner_text()).strip()
                descricao_tecnica[key] = val
        except Exception:
            # fallback para outro layout de specs
            try:
                texto = await page.locator("div#productDetails_detailBullets_sections1").inner_text()
                descricao_tecnica = {"técnica_unificada": texto.strip()}
            except Exception:
                descricao_tecnica = {}

        # 9) Detalhes adicionais (tabela a-keyvalue prodDetTable)
        detalhes = {}
        try:
            linhas = page.locator("table.a-keyvalue.prodDetTable tbody tr")
            count = await linhas.count()
            for i in range(count):
                th = linhas.nth(i).locator("th")
                td = linhas.nth(i).locator("td")
                chave = (await th.inner_text()).strip()
                valor = (await td.inner_text()).strip()
                detalhes[chave] = valor
        except Exception:
            detalhes = {}

        # 10) Imagem principal
        try:
            imagem = await page.locator("img#landingImage").get_attribute("src")
        except Exception:
            imagem = ""

        await browser.close()

        # Monta e retorna o dicionário final
        if nome:
            return {
                "nome": nome,
                "preco": preco,
                "nota": nota,
                "descricao_curta": descricao_curta,
                "descricao_detalhada": descricao_detalhada,
                "descricao_tecnica": descricao_tecnica,
                "detalhes_adicionais": detalhes,
                "url": url,
                "tipo_produto": termo,
                "imagem": imagem
            }
        return None


async def search_details_amazon():
    output = []
    for produto in banco_produtos_amazon:
        results = await scrape_amazon_product(produto["url"], produto["tipo_produto"])
        output.append(results)

    filename = "amazon_perfeito.json"
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"✅ Amazon: {len(output)} produtos salvos em {filename}")


async def get_product_details(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
        )
        page = await context.new_page()
        await page.goto(url, timeout=60000)
        await page.wait_for_timeout(2000)

        try:
            await page.wait_for_selector("#bannerPop", timeout=5000)
            await page.evaluate("""
                () => {
                    const banner = document.getElementById('bannerPop');
                    if (banner) banner.remove();
                    document.querySelectorAll('.modal-backdrop, .fade.in').forEach(e => e.remove());
                }
            """)
        except:
            pass

        try:
            await page.evaluate(
                "document.querySelector('a[href=\"#esptec\"]').scrollIntoView()"
            )
            await page.click('a[href="#esptec"]')
        except:
            pass

        try:
            await page.evaluate(
                "document.querySelector('a[href=\"#cg\"]').scrollIntoView()"
            )
            await page.click('a[href="#cg"]')
            await page.wait_for_selector("div#cg", state="visible", timeout=10000)
        except:
            pass

        descricao = ""
        try:
            el = await page.query_selector("div.descricao section.bg_branco p")
            if el:
                descricao = await el.inner_text()
        except:
            pass

        if not descricao:
            try:
                el = await page.query_selector("div.descricao section.bg_preto p")
                if el:
                    descricao = await el.inner_text()
            except:
                pass

        if not descricao:
            try:
                el = await page.query_selector(
                    "div.descricao section.bg_preto div[style*='margin']"
                )
                if el:
                    textos = await page.eval_on_selector_all(
                        "div.descricao section.bg_preto div[style*='margin'] *",
                        "elements => elements.map(e => e.innerText).filter(Boolean).join(' ')",
                    )
                    descricao = textos
            except:
                pass

        specs_dict = {}
        try:
            await page.wait_for_selector("div.tecnicas", timeout=20000)
            p_tags = await page.query_selector_all("div.tecnicas > p")
            for ptag in p_tags:
                text = await ptag.inner_text()
                text = re.sub(r"\s+", " ", text).strip()
                if not text:
                    continue

                if ":" in text:
                    parts = text.split(":", 1)
                    key = parts[0].strip()
                    val = parts[1].strip().strip('"')
                    specs_dict[key] = val
                else:
                    specs_dict[text] = ""
        except:
            pass

        image_url = ""
        try:
            img_element = await page.query_selector("img.zoomImg")
            if img_element:
                image_url = await img_element.get_attribute("src")
        except:
            pass

        await browser.close()
        return descricao.strip(), specs_dict, image_url


async def search_details():
    if banco_produtos_terabyte:
        for produto in banco_produtos_terabyte:
            try:
                desc, esp, img = await get_product_details(produto["url"])
                produto["descricao"] = desc
                produto["tecnica"] = esp
                produto["imagem"] = img
                print(desc)
            except Exception as e:
                print(produto["url"])
                print(e)

    filename = "terabyte_perfeito.json"
    path = os.path.join(OUTPUT_DIR_TERA, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(banco_produtos_terabyte, f, ensure_ascii=False, indent=2)
    print(f"✅ Terabyte: {len(banco_produtos_terabyte)} produtos salvos em {filename}")


async def main():
    await search()
    print("buscar detalhes")
    await search_details()
    await search_details_amazon()


if __name__ == "__main__":
    asyncio.run(main())
