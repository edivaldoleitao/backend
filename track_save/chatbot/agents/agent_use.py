import getpass
import json
import os
from pathlib import Path

import requests
from dotenv import load_dotenv
from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.prompts.chat import ChatPromptTemplate
from langchain.prompts.chat import HumanMessagePromptTemplate
from langchain.prompts.chat import SystemMessagePromptTemplate

env_path = Path(__file__).resolve().parent.parent / ".envs" / ".local" / ".api_key_gpt"
load_dotenv(dotenv_path=env_path)

if not os.environ.get("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = getpass.getpass("Enter API key for OpenAI: ")


from django.apps import apps


def generate_schema_string(app_label: str):
    schema_lines = []
    models = apps.get_app_config(app_label).get_models()

    for model in models:
        schema_lines.append(f"Tabela {model.__name__}:")
        for field in model._meta.fields:
            if (
                field.name == "id"
            ):  # Se quiser omitir o id, pode remover esta verificação
                continue
            schema_lines.append(f" - {field.name}: {field.get_internal_type()}")
        schema_lines.append("")  # Linha em branco entre models

    return "\n".join(schema_lines)


schema_str = generate_schema_string("api")
# print(schema_str)

spec_prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate.from_template(
            "Você é um especialista em tecnologia. Seu papel é transformar as informações do usuário "
            "em um JSON completo, pronto para ser enviado à API de busca de produtos.\n\n"
            "Aqui está o schema do banco de dados com modelos e colunas disponíveis:\n"
            "{schema}\n\n"
            "Agora, considere a nova entrada do usuário abaixo:\n"
            "{input_json}\n\n"
            "Gere um JSON no seguinte formato EXATO:\n\n"
            "{{\n"
            '  "searches": [\n'
            "    {{\n"
            '      "model_name": "NomeDoModel",\n'
            '      "columns": ["coluna1", "coluna2"],\n'
            '      "search_values": ["valor1", "valor2"]\n'
            "    }}\n"
            "  ]\n"
            "}}\n\n"
            "Inclua apenas colunas e valores relevantes para o contexto da necessidade do usuário.\n"
            "Retorne **apenas o JSON**, sem explicações adicionais.",
        ),
        HumanMessagePromptTemplate.from_template("{input_json}"),
    ],
)

recommendation_prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate.from_template(
            "Você é TrackBot, um consultor especializado em tecnologia. Seu papel é justificar "
            "por que os produtos encontrados atendem às necessidades do cliente, com base nas especificações solicitadas. "
            "Inclua o nome do produto, preço e link. Se não houver produtos, informe educadamente.",
        ),
        HumanMessagePromptTemplate.from_template(
            "Especificações do cliente:\n{specs_json}\n\n"
            "Produtos encontrados:\n{products_json}\n\n"
            "Gere uma resposta explicando por que esses produtos atendem à necessidade.",
        ),
    ],
)

API_SEARCH_URL = "http://localhost:8000/api/search/"

import re


def processar_recomendacao(input_data: dict, schema_str: str):
    print("TESTEEEEEEEEEEEEEEEEEE")
    llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)

    print("\n📥 Entrada do usuário:")
    print(json.dumps(input_data, indent=2))

    # 1. Gerar o JSON completo com spec_prompt
    spec_chain = LLMChain(llm=llm, prompt=spec_prompt)
    user_input_json = json.dumps(input_data)

    specs_json = spec_chain.run(
        {
            "schema": schema_str,
            "input_json": user_input_json,
        },
    )
    print("\n📄 JSON gerado pelo spec_prompt:", flush=True)

    match = re.search(r"({.*})", specs_json, re.DOTALL)
    if match:
        specs_json = match.group(1)

    try:
        specs_dict = json.loads(specs_json)
    except json.JSONDecodeError:
        return {"error": "Erro ao interpretar o JSON GERADO pelo LLM."}

    print("\n🔎 JSON completo gerado pelo spec_prompt:")
    print(json.dumps(specs_dict, indent=2))

    # 2. Enviar para API
    try:
        response = requests.post(API_SEARCH_URL, json=specs_dict)
        response.raise_for_status()
        search_results = response.json().get("results", [])
    except Exception as e:
        return {"error": f"Erro ao consultar API: {e!s} {specs_dict}"}

    print("\n✅ Produtos retornados da API:")
    print(json.dumps(search_results, indent=2))

    # 3. Gerar a recomendação
    rec_chain = LLMChain(llm=llm, prompt=recommendation_prompt)
    recommendation = rec_chain.run(
        {
            "specs_json": json.dumps(specs_dict, indent=2),
            "products_json": json.dumps(search_results, indent=2),
        },
    )

    print("\n💬 Recomendação final:")
    print(recommendation)

    return {
        "specs": specs_dict,
        "produtos": search_results,
        "recomendacao": recommendation,
    }
