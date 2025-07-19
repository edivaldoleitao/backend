import getpass
import json
import os
import re
from pathlib import Path

import requests
from django.apps import apps
from django.core.serializers.json import DjangoJSONEncoder
from dotenv import load_dotenv
from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.prompts.chat import ChatPromptTemplate
from langchain.prompts.chat import HumanMessagePromptTemplate
from langchain.prompts.chat import SystemMessagePromptTemplate

env_path = Path(__file__).resolve().parent.parent / ".envs" / ".local" / ".api_key_gpt"
load_dotenv(dotenv_path=env_path)
API_SEARCH_URL = "http://localhost:8000/api/search/"

if not os.environ.get("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = getpass.getpass("Enter API key for OpenAI: ")


def generate_schema_string(app_label: str):
    schema_lines = []
    models = apps.get_app_config(app_label).get_models()

    for model in models:
        schema_lines.append(f"Tabela {model.__name__}:")
        for field in model._meta.fields:
            if field.name == "id":
                continue
            schema_lines.append(f" - {field.name}: {field.get_internal_type()}")
        schema_lines.append("")  # Linha em branco entre models

    return "\n".join(schema_lines)


def get_example_records(app_label: str) -> str:
    examples = {}

    app_config = apps.get_app_config(app_label)
    for model in app_config.get_models():
        inst = model.objects.first()
        if not inst:
            continue

        data = {}
        for field in inst._meta.get_fields():
            if field.one_to_many or field.many_to_many:
                continue
            if hasattr(field, "attname"):
                val = getattr(inst, field.attname)
                data[field.name] = val

        examples[model.__name__] = data

    return json.dumps(examples, cls=DjangoJSONEncoder, indent=2)


def carregar_contexto_llm(app_label="api"):
    examples_json = get_example_records(app_label)
    schema_str = generate_schema_string(app_label)
    print(f"Exemplos de registros:\n{examples_json}\n")
    print(f"Schema gerado: {schema_str}")
    return schema_str, examples_json


spec_prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate.from_template(
            "Você é um especialista em tecnologia. Seu papel é transformar as informações do usuário "
            "em um JSON completo, pronto para ser enviado à API de busca de produtos.\n\n"
            "**Use apenas as tabelas e colunas listadas abaixo**. Não crie novas tabelas nem campos.\n"
            "Antes de escolher qualquer coluna, **verifique** que ela consta no schema ou no exemplo de registro.\n\n"
            "Aqui está o schema do banco de dados:\n"
            "{schema}\n\n"
            "E aqui um exemplo de 1 registro de cada tabela (para referência de tipos e formatos):\n"
            "{examples}\n\n"
            "Observações:\n"
            "Regras de marca vs. chipset:\n"
            "- O campo **chipset** só deve receber valores **‘NVIDIA’** ou **‘AMD’**.\n"
            "- Quaisquer outros nomes de fabricantes (Asus, Gigabyte, MSI, Galax, Zotac, PNY, Corsair etc.)\n"
            "  são **brands**, não chipset — use-os apenas no campo **brand** quando disponível.\n\n"
            "Agora, considere a nova entrada do usuário abaixo:\n"
            "{input_json}\n\n"
            "Gere **apenas** um JSON no seguinte formato EXATO (sem explicações):\n\n"
            "{{\n"
            '  "searches": [\n'
            "    {{\n"
            '      "model_name": "NomeDoModel",\n'
            '      "columns": ["coluna1", "coluna2"],\n'
            '      "search_values": ["valor1", "valor2"]\n'
            "    }}\n"
            "  ]\n"
            "}}\n\n"
            "— Nunca use operadores como '>=', apenas valores literais.\n"
            "— Exemplo de valor de coluna: 'vram': '8GB'.\n",
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


def processar_recomendacao(input_data: dict):
    schema_str, examples_json = carregar_contexto_llm()

    llm = ChatOpenAI(model_name="gpt-4-turbo", temperature=0)
    user_input_json = json.dumps(input_data)

    spec_chain = LLMChain(llm=llm, prompt=spec_prompt)
    specs_json = spec_chain.run(
        {
            "schema": schema_str,
            "examples": examples_json,
            "input_json": user_input_json,
        },
    )

    match = re.search(r"({.*})", specs_json, re.DOTALL)
    if match:
        specs_json = match.group(1)

    try:
        specs_dict = json.loads(specs_json)
    except json.JSONDecodeError:
        return {"error": "Erro ao interpretar o JSON GERADO pelo LLM."}

    try:
        response = requests.post(API_SEARCH_URL, json=specs_dict)
        response.raise_for_status()
        search_results = response.json().get("results", [])
    except Exception as e:
        return {"error": f"Erro ao consultar API: {e!s} {specs_dict}"}

    rec_chain = LLMChain(llm=llm, prompt=recommendation_prompt)
    recommendation = rec_chain.run(
        {
            "specs_json": json.dumps(specs_dict, indent=2),
            "products_json": json.dumps(search_results, indent=2),
        },
    )

    return {
        "specs": specs_dict,
        "produtos": search_results,
        "recomendacao": recommendation,
    }
