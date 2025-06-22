import json
import os
import subprocess
import sys
import urllib.parse

AMAZON = "https://www.amazon.com.br/s?k="
OUTPUT_FILE_AMAZON = "Amazon.jl"  # nome do arquivo que será gerado pelo Scrapy
lista_produtos = [
    "teclado",
    "mouse_gamer",
    "monitor",
    "placa_de_video",
    "processador_intel_amd",
]


def search():
    for termo_pesquisa in lista_produtos:
        for number in range(1, 11):
            page_number = str(number)
            page = "&page=" + page_number
            consulta_amazon = AMAZON + montar_url(termo_pesquisa) + montar_url(page)
            consultas = [{"name": "Amazon", "url": consulta_amazon}]

            chamar_crawler(consultas, termo_pesquisa)
            file_name = termo_pesquisa
            result = [{"name": "Amazon", "products": file_name}]
    return result


def montar_url(termo_pesquisa):
    return urllib.parse.quote(termo_pesquisa, safe="")


def chamar_crawler(consultas, termo_pesquisa):
    for consulta in consultas:
        command = [
            sys.executable,  # Isso equivale a chamar o "python" correto
            "-m",
            "scrapy",
            "crawl",
            "track_save_crawler",
            "-a",
            f"url={consulta['url']}",
            "-s",
            f"FEED_URI={termo_pesquisa}_AMAZON.jl",
            "-s",
            "FEED_FORMAT=jsonlines",
            "-s",
            "FEED_EXPORT_ENCODING=utf8",
            "-s",
            "FEED_STORE_EMPTY=False",
            "-s",
            "FEED_EXPORT_APPEND=True",
        ]
        try:
            subprocess.run(command, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Erro ao rodar o crawler: {e}")


def carregar_json(filename):
    data = []
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    data.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return data


# execução pelo terminal
# python track_save/webscrapping_amazon/track_save/track_save/spiders/app.py


if __name__ == "__main__":
    search()
