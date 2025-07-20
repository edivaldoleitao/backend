import json
import re
from pathlib import Path

import requests
from dotenv import load_dotenv
from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.prompts.chat import ChatPromptTemplate
from langchain.prompts.chat import HumanMessagePromptTemplate
from langchain.prompts.chat import SystemMessagePromptTemplate
from django.core.serializers.json import DjangoJSONEncoder
from django.apps import apps

# Carregando variáveis de ambiente
env_path = Path(__file__).resolve().parent.parent / ".envs" / ".local" / ".api_key_gpt"
load_dotenv(dotenv_path=env_path)
API_SEARCH_URL = "http://localhost:8000/api/search/"


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


def get_example_records():
    """
    Retorna um dicionário onde as chaves são nomes de model
    e os valores são um único registro de exemplo (como dict).
    """
    examples = {}
    model_names = [
        "Alert", "Favorite", "Product", "ProductStore", "Price", "Storage",
        "Ram", "Cpu", "Gpu", "Motherboard", "PowerSupply", "Cooler"
    ]

    for name in model_names:
        try:
            Model = apps.get_model("api", name)
        except LookupError:
            continue
        inst = Model.objects.first()
        if not inst:
            continue

        data = {}
        for field in inst._meta.get_fields():
            if field.many_to_many or field.one_to_many:
                continue
            if hasattr(field, 'attname'):
                val = getattr(inst, field.attname)
                data[field.name] = val
        examples[name] = data

    return json.dumps(examples, cls=DjangoJSONEncoder, indent=2)


def carregar_contexto_llm():
    schema_str = generate_schema_string("api")
    examples_json = get_example_records()
    print(f"Exemplos de registros:\n{examples_json}\n")
    print(f"Schema gerado: {schema_str}")
    return schema_str, examples_json


# PROMPTS
upgrade_prompt = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(
        "Você é um especialista em hardware de computadores. Seu papel é, dado o setup atual do usuário, sua descrição de problema "
        "e o schema do banco de dados, gerar upgrades compatíveis e superiores no formato JSON.\n\n"
        "**Use somente as tabelas e colunas já definidas abaixo**. Não adicione nenhuma tabela nova nem campo extra.\n\n"
        "Aqui está o schema do banco:\n"
        "{schema}\n\n"
        "Aqui vão exemplos (1 por tabela) para referência:\n{examples}\n\nAgora, considere o setup..."
        "Agora, considere o setup atual do usuário e a descrição do problema:\n"
        "{setup_json}\n{descricao_dor}\n\n"
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
        "Inclua apenas colunas e valores relevantes do schema. Retorne **apenas o JSON**, sem explicações adicionais. "
        "Nunca use operadores como '>=', apenas indique valores mínimos reais. Exemplo correto: 'vram': '8GB'."
    ),
    HumanMessagePromptTemplate.from_template("{setup_json}\n{descricao_dor}")
])

recommendation_prompt = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(
        "Você é TrackBot, um consultor especializado em tecnologia. Seu papel é analisar as especificações atuais do usuário, "
        "os upgrades sugeridos e os produtos disponíveis no banco de dados.\n\n"
        "**Atenção:**\n"
        "- Só pode recomendar produtos que estão listados no banco de dados abaixo.\n"
        "- Se o banco estiver vazio, **não invente produtos.**\n"
        "- Informe educadamente que não foram encontrados produtos disponíveis.\n\n"
        "Especificações atuais do usuário:\n{setup_json}\n\n"
        "Upgrades sugeridos:\n{upgrade_specs}\n\n"
        "Produtos encontrados no banco:\n{products_json}\n\n"
        "Gere uma resposta explicando por que os produtos resolvem o problema, citando nome, preço e link.\n"
        "Se não houver produtos, informe que não há produtos disponíveis."
    ),
    HumanMessagePromptTemplate.from_template("{setup_json}\n{upgrade_specs}\n{products_json}")
])


# FUNÇÃO PRINCIPAL
def processar_upgrade(setup_json: dict, descricao_dor: str, dfs: dict):
    schema_str, examples_json = carregar_contexto_llm()
    llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)

    upgrade_chain = LLMChain(llm=llm, prompt=upgrade_prompt)
    upgrade_specs_json = upgrade_chain.run({
        "schema": schema_str,
        "examples": examples_json,
        "setup_json": json.dumps(setup_json),
        "descricao_dor": descricao_dor,
    })

    match = re.search(r"({.*})", upgrade_specs_json, re.DOTALL)
    if match:
        upgrade_specs_json = match.group(1)

    try:
        upgrade_specs = json.loads(upgrade_specs_json)
    except json.JSONDecodeError:
        return {"error": "Erro ao interpretar o JSON gerado pelo LLM."}

    try:
        response = requests.post(API_SEARCH_URL, json=upgrade_specs)
        response.raise_for_status()
        search_results = response.json().get("results", [])
    except Exception as e:
        return {"error": f"Erro ao consultar API: {e!s} {upgrade_specs}"}

    rec_chain = LLMChain(llm=llm, prompt=recommendation_prompt)
    recommendation = rec_chain.run({
        "setup_json": json.dumps(setup_json, indent=2),
        "upgrade_specs": json.dumps(upgrade_specs, indent=2),
        "products_json": json.dumps(search_results, indent=2),
    })

    return {
        "espc_gerado_pela_llm": upgrade_specs_json,
        "upgrade_specs": upgrade_specs,
        "produtos_encontrados": search_results,
        "resposta": recommendation,
    }
