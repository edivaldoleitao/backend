from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
import pandas as pd
import json
import os
from dotenv import load_dotenv
import getpass
from pathlib import Path

env_path = Path(__file__).resolve().parent.parent / '.envs' / '.local' / '.api_key_gpt'
load_dotenv(dotenv_path=env_path)

if not os.environ.get("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = getpass.getpass("Enter API key for OpenAI: ")

produtos = [
    {
        "nome": "Dell XPS 15",
        "processador": "i7",
        "ram": "16GB",
        "armazenamento": "512GB SSD",
        "placa_video": "RTX 3050",
        "preco": 4800,
        "categoria": "computador",
        "uso": "trabalhar",
        "link": "https://site.com/dellxps15"
    },
    {
        "nome": "Acer Nitro 5",
        "processador": "Intel Core i7",
        "ram": "16GB",
        "armazenamento": "1TB SSD",
        "placa_video": "RTX 3060",
        "preco": 4500,
        "categoria": "computador",
        "uso": "jogar",
        "link": "https://site.com/acernitro5"
    },
]

df_produtos = pd.DataFrame(produtos)

spec_prompt = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(
        "Você é um especialista em tecnologia. Seu papel é transformar as informações do usuário "
        "em um dicionário de especificações técnicas detalhadas, no contexto da categoria e do uso informado.\n\n"
        "Aqui está o histórico recente da conversa:\n"

        "Agora, considere a nova entrada do usuário abaixo:\n"
        "{input_json}\n\n"
        "Gere um JSON com especificações técnicas que podem incluir chaves como:\n"
        "- processador\n"
        "- ram\n"
        "- placa_video\n"
        "- dpi\n"
        "- tamanho_tela\n"
        "- preco_max\n\n"
        "Inclua apenas as especificações que façam sentido para a categoria e o uso.\n"
        "Retorne **apenas o JSON**, sem texto adicional.\n\n"
        "Exemplo de saída:\n"
        '{{"processador": "i5", "ram": "16GB", "placa_video": "RTX 3060"}}'
    ),
    HumanMessagePromptTemplate.from_template("{input_json}"),
])

recommendation_prompt = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(
        "Você é TrackBot, um consultor especializado em tecnologia. Seu papel é justificar "
        "por que os produtos encontrados atendem às necessidades do cliente, com base nas especificações solicitadas. "
        "Inclua o nome do produto, preço e link. Se não houver produtos, informe educadamente."
    ),
    HumanMessagePromptTemplate.from_template(
        "Especificações do cliente:\n{specs_json}\n\n"
        "Produtos encontrados:\n{products_json}\n\n"
        "Gere uma resposta explicando por que esses produtos atendem à necessidade."
    ),
])

def filtrar_produtos(filtro_front: dict, specs: dict, df: pd.DataFrame):
    filtro = df.copy()

    if "categoria" in filtro_front:
        filtro = filtro[
            filtro["categoria"].str.lower() == filtro_front["categoria"].lower()
        ]

    if "uso" in filtro_front:
        filtro = filtro[
            filtro["uso"].str.lower() == filtro_front["uso"].lower()
        ]

    if "preco" in filtro_front:
        filtro = filtro[filtro["preco"] <= filtro_front["preco"]]

    if "processador" in specs:
        filtro = filtro[
            filtro["processador"].str.lower().str.contains(specs["processador"].lower(), na=False)
        ]

    if "ram" in specs:
        filtro = filtro[
            filtro["ram"].str.lower().str.contains(specs["ram"].lower(), na=False)
        ]

    if "placa_video" in specs:
        filtro = filtro[
            filtro["placa_video"].str.lower().str.contains(specs["placa_video"].lower(), na=False)
        ]

    if "dpi" in specs and "dpi" in filtro.columns:
        filtro = filtro[filtro["dpi"] >= specs["dpi"]]

    if "tamanho_tela" in specs and "tamanho_tela" in filtro.columns:
        filtro = filtro[filtro["tamanho_tela"] >= specs["tamanho_tela"]]

    return filtro.reset_index(drop=True)


def processar_recomendacao(input_data: dict):
    llm = ChatOpenAI(model_name="gpt-4o", temperature=0)

    user_input_json = json.dumps(input_data)

    spec_chain = LLMChain(llm=llm, prompt=spec_prompt)
    specs_json = spec_chain.run({"input_json": user_input_json})

    try:
        specs_dict = json.loads(specs_json)
    except json.JSONDecodeError:
        return {"error": "Erro ao interpretar o JSON gerado pelo LLM."}

    filtros = ["categoria", "uso", "preco"]
    filtro_front = {k: input_data[k] for k in filtros if k in input_data}
    produtos_filtrados = filtrar_produtos(filtro_front, specs_dict, df_produtos)

    products_list = produtos_filtrados.to_dict(orient="records")

    rec_chain = LLMChain(llm=llm, prompt=recommendation_prompt)
    recommendation = rec_chain.run({
        "specs_json": str(specs_dict),
        "products_json": str(products_list)
    })

    return {
        "specs": specs_dict,
        "produtos": products_list,
        "recomendacao": recommendation
    }
