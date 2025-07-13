import json
from datetime import datetime
import re

produtos_tera = []
produtos_amazon = []


MAP_CATEGORIAS = {
    "perifericos/teclado": "keyboard",
    "perifericos/mouse": "mouse",
    "hardware/placas-de-video": "gpu",
    "hardware/processadores": "cpu",
    "monitores": "monitor",
}


def buscar_campo(tecnica, *possiveis_nomes):
    for nome in possiveis_nomes:
        if nome in tecnica:
            return tecnica[nome]
    return "Não informado"

def extrair_numerico(valor):
    if not valor:
        return 0
    match = re.findall(r'[\d.,]+', valor)
    if match:
        num_str = match[0].replace(".", "").replace(",", ".")
        try:
            return float(num_str)
        except ValueError:
            return 0
    return 0

file_path_tera = "/app/track_save/webscrapping_amazon/scraper/resultados_terabyte/terabyte_perfeito.json"
try:
    with open(file_path_tera, "r") as file:
        produtos_tera = json.load(file)
except Exception as e:
    print(e)

file_path_amazon = "resultados_amazon/amazon_perfeito.json"
try:
    with open(file_path_amazon, "r") as file:
        produtos_amazon = json.load(file)
except Exception as e:
    print(e)


except FileNotFoundError:
    print(f"Error: The file '{file_path_tera}' was not found.")
except json.JSONDecodeError:
    print(f"Error: Could not decode JSON from '{file_path_tera}'. Check file format.")

teclados_terabyte = [
    item for item in produtos_tera if item.get("tipo_produto") == "perifericos/teclado"
]
mouses_terabyte = [
    item for item in produtos_tera if item.get("tipo_produto") == "perifericos/mouse"
]
gpu_terabyte = [
    item
    for item in produtos_tera
    if item.get("tipo_produto") == "hardware/placas-de-video"
]
processadores_terabyte = [
    item
    for item in produtos_tera
    if item.get("tipo_produto") == "hardware/processadores"
]
monitores_terabyte = [
    item for item in produtos_tera if item.get("tipo_produto") == "monitores"
]


def get_terabyte():
    terabyte_output = []
    amazon_output = []
    for produto in produtos_tera:
        tipo_scraping = produto.get("tipo_produto")
        categoria_django = MAP_CATEGORIAS.get(tipo_scraping)
        produto["categoria"] = categoria_django
        if not categoria_django:
            print(
                f"⚠️ Categoria não mapeada: {tipo_scraping}. Produto ignorado: {produto.get('nome')}"
            )
            continue

        tecnica = produto.get("tecnica", {})
        descricao = produto.get("descricao", "") or "Não informado"
        preco_str = (
            produto.get("preco", "0")
            .replace("R$", "")
            .replace(".", "")
            .replace(",", ".")
            .strip()
        )

        try:
            preco_float = float(preco_str)
        except ValueError:
            preco_float = 0.0

        # Preparar spec_fields padrão
        spec_fields = {
            "model": buscar_campo(tecnica, "Modelo", "Model"),
            "store": "Terabyte",
            "url": produto.get("url"),
            "available": True,
            "value": preco_float,
            "collection_date": datetime.now(),
        }

        match categoria_django:
            case "keyboard":
                spec_fields.update(
                    {
                        "key_type": buscar_campo(
                            tecnica, "Switch", "Tipo de switch", "Tipo de tecla"
                        ) or "Não informado",
                        "layout": buscar_campo(
                            tecnica, "Nomeros de teclas", "Número de teclas", "Layout"
                        ) or "Não informado",
                        "connectivity": buscar_campo(
                            tecnica, "Cabo", "Conectividade", "Tipo de conexão"
                        )
                        or "Não informado",
                        "dimension": buscar_campo(
                            tecnica, "Tamanho do teclado", "Dimensão", "Tamanho", "Dimensões","Dimensoes", "Dimensao"
                        ) or "Não informado",
                    }
                )
            case "cpu":
                spec_fields.update(
                    {
                        "integrated_video": buscar_campo(
                            tecnica, "Vídeo Integrado", "Vídeo onboard", "GPU Integrada"
                        )
                        or "Não informado",
                        "socket": buscar_campo(tecnica, "Soquete", "Socket"),
                        "core_number": extrair_numerico(buscar_campo(
                            tecnica, "Núcleos de CPU", "Núcleos", "Cores"
                        )),
                        "thread_number": extrair_numerico(buscar_campo(
                            tecnica, "Threads", "Número de threads"
                        )),
                        "frequency": extrair_numerico(buscar_campo(
                            tecnica, "Clock base", "Frequência base", "Clock"
                        )),
                        "mem_speed": extrair_numerico(buscar_campo(
                            tecnica, "Memória", "Velocidade Memória", "Velocidade RAM"
                        )),
                    }
                )
            case "gpu":
                spec_fields.update(
                    {
                        "vram": extrair_numerico(buscar_campo(
                            tecnica, "Memory Size", "Memória", "Capacidade de memória"
                        )),
                        "chipset": buscar_campo(tecnica, "Chipset", "Modelo", "GPU"),
                        "max_resolution": buscar_campo(
                            tecnica, "Digital max resolution", "Resolução Máxima"
                        ),
                        "output": buscar_campo(
                            tecnica, "Output", "Saídas", "Conectores", "Portas"
                        ),
                        "tech_support": buscar_campo(
                            tecnica, "DirectX", "OpenGL", "Tecnologias suportadas"
                        ),
                    }
                )
            case "mouse":
                spec_fields.update(
                    {
                        "brand": buscar_campo(tecnica, "Marca", "marca") or "Não informado",
                        "dpi": extrair_numerico(buscar_campo(tecnica, "DPI", "Resolução")) or 0,
                        "connectivity": buscar_campo(
                            tecnica, "Conectividade", "Cabo", "Tipo de conexão"
                        )
                        or "Fio",
                        "color": buscar_campo(tecnica, "Cor", "Cor predominante") or "Não informado",
                    }
                )
            case "monitor":
                spec_fields.update(
                    {
                        "inches": extrair_numerico(buscar_campo(
                            tecnica, "Tamanho da tela", "Polegadas", "Tamanho"
                        )),
                        "panel_type": buscar_campo(
                            tecnica, "Tipo de luz de fundo", "Painel", "Tipo Painel"
                        ),
                        "proportion": buscar_campo(
                            tecnica, "Proporção", "Aspect Ratio"
                        ),
                        "resolution": buscar_campo(
                            tecnica, "Resolução", "Resolução Máxima"
                        ),
                        "refresh_rate": buscar_campo(
                            tecnica,
                            "Taxa de atualização",
                            "Frequência",
                            "Taxa de contraste",
                        ),
                        "color_support": buscar_campo(
                            tecnica, "RGB", "Suporte a cores", "Cores"
                        ),
                        "output": buscar_campo(
                            tecnica, "Portas", "Conectores", "Entradas", "Saídas"
                        ),
                          "model": buscar_campo(
                            tecnica, "model", "Model", "modelo", "Modelo"
                        ) or "Não informado",
                    }
                )
            case _:
                pass
        brand = buscar_campo(tecnica, "Marca")
        produto["spec_fields"] = spec_fields

    return produtos_tera

def get_amazon():
    amazon_output = []
    for produto in produtos_tera:
        tipo_scraping = produto.get("tipo_produto")
        categoria_django = MAP_CATEGORIAS.get(tipo_scraping)
        produto["categoria"] = categoria_django
        if not categoria_django:
            print(
                f"⚠️ Categoria não mapeada: {tipo_scraping}. Produto ignorado: {produto.get('nome')}"
            )
            continue

        tecnica = produto.get("tecnica", {})
        descricao = produto.get("descricao", "") or "Não informado"
        preco_str = (
            produto.get("preco", "0")
            .replace("R$", "")
            .replace(".", "")
            .replace(",", ".")
            .strip()
        )

        try:
            preco_float = float(preco_str)
        except ValueError:
            preco_float = 0.0

        # Preparar spec_fields padrão
        spec_fields = {
            "model": buscar_campo(tecnica, "Modelo", "Model"),
            "store": "Terabyte",
            "url": produto.get("url"),
            "available": True,
            "value": preco_float,
            "collection_date": datetime.now(),
        }

        match categoria_django:
            case "keyboard":
                spec_fields.update(
                    {
                        "key_type": buscar_campo(
                            tecnica, "Switch", "Tipo de switch", "Tipo de tecla"
                        ) or "Não informado",
                        "layout": buscar_campo(
                            tecnica, "Nomeros de teclas", "Número de teclas", "Layout"
                        ) or "Não informado",
                        "connectivity": buscar_campo(
                            tecnica, "Cabo", "Conectividade", "Tipo de conexão"
                        )
                        or "Não informado",
                        "dimension": buscar_campo(
                            tecnica, "Tamanho do teclado", "Dimensão", "Tamanho", "Dimensões","Dimensoes", "Dimensao"
                        ) or "Não informado",
                    }
                )
            case "cpu":
                spec_fields.update(
                    {
                        "integrated_video": buscar_campo(
                            tecnica, "Vídeo Integrado", "Vídeo onboard", "GPU Integrada"
                        )
                        or "Não informado",
                        "socket": buscar_campo(tecnica, "Soquete", "Socket"),
                        "core_number": extrair_numerico(buscar_campo(
                            tecnica, "Núcleos de CPU", "Núcleos", "Cores"
                        )),
                        "thread_number": extrair_numerico(buscar_campo(
                            tecnica, "Threads", "Número de threads"
                        )),
                        "frequency": extrair_numerico(buscar_campo(
                            tecnica, "Clock base", "Frequência base", "Clock"
                        )),
                        "mem_speed": extrair_numerico(buscar_campo(
                            tecnica, "Memória", "Velocidade Memória", "Velocidade RAM"
                        )),
                    }
                )
            case "gpu":
                spec_fields.update(
                    {
                        "vram": extrair_numerico(buscar_campo(
                            tecnica, "Memory Size", "Memória", "Capacidade de memória"
                        )),
                        "chipset": buscar_campo(tecnica, "Chipset", "Modelo", "GPU"),
                        "max_resolution": buscar_campo(
                            tecnica, "Digital max resolution", "Resolução Máxima"
                        ),
                        "output": buscar_campo(
                            tecnica, "Output", "Saídas", "Conectores", "Portas"
                        ),
                        "tech_support": buscar_campo(
                            tecnica, "DirectX", "OpenGL", "Tecnologias suportadas"
                        ),
                    }
                )
            case "mouse":
                spec_fields.update(
                    {
                        "brand": buscar_campo(tecnica, "Marca", "marca") or "Não informado",
                        "dpi": extrair_numerico(buscar_campo(tecnica, "DPI", "Resolução")) or 0,
                        "connectivity": buscar_campo(
                            tecnica, "Conectividade", "Cabo", "Tipo de conexão"
                        )
                        or "Fio",
                        "color": buscar_campo(tecnica, "Cor", "Cor predominante") or "Não informado",
                    }
                )
            case "monitor":
                spec_fields.update(
                    {
                        "inches": extrair_numerico(buscar_campo(
                            tecnica, "Tamanho da tela", "Polegadas", "Tamanho"
                        )),
                        "panel_type": buscar_campo(
                            tecnica, "Tipo de luz de fundo", "Painel", "Tipo Painel"
                        ),
                        "proportion": buscar_campo(
                            tecnica, "Proporção", "Aspect Ratio"
                        ),
                        "resolution": buscar_campo(
                            tecnica, "Resolução", "Resolução Máxima"
                        ),
                        "refresh_rate": buscar_campo(
                            tecnica,
                            "Taxa de atualização",
                            "Frequência",
                            "Taxa de contraste",
                        ),
                        "color_support": buscar_campo(
                            tecnica, "RGB", "Suporte a cores", "Cores"
                        ),
                        "output": buscar_campo(
                            tecnica, "Portas", "Conectores", "Entradas", "Saídas"
                        ),
                          "model": buscar_campo(
                            tecnica, "model", "Model", "modelo", "Modelo"
                        ) or "Não informado",
                    }
                )
            case _:
                pass
        brand = buscar_campo(tecnica, "Marca")
        produto["spec_fields"] = spec_fields

    return produtos_amazon