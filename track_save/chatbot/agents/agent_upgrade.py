from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI
import pandas as pd
import json
from dotenv import load_dotenv
import os
from pathlib import Path

env_path = Path(__file__).resolve().parent.parent / '.envs' / '.local' / '.api_key_gpt'
load_dotenv(dotenv_path=env_path)

upgrade_prompt = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(
        "Você é um especialista em hardware de computadores. Seu papel é, dado o setup atual do usuário e sua descrição de problema, "
        "gerar upgrades compatíveis e superiores, no formato de JSON, com base nas tabelas do meu banco.\n\n"
        " **Tabelas e campos disponíveis:**\n"
        "- **Cpu:** model, socket, core_number, frequency\n"
        "- **Ram:** capacity, ddr, speed\n"
        "- **Graphics:** model, vram, chipset\n"
        "- **Monitor:** inches, resolution, refresh_rate\n"
        "- **Mouse:** dpi\n"
        "- **Keyboard:** layout, key_type\n\n"
        "Se não precisar sugerir upgrade para algum componente, não inclua ele no JSON.\n"
        "Inclua 'preco_max' se o usuário mencionar limite de orçamento.\n"
        "Nunca invente campos além desses.\n\n"
        "Exemplo de saída:\n"
        '{{"cpu": {{"model": "i5 12400", "socket": "LGA 1700", "core_number": "6", "frequency": "4.4GHz"}}, '
        '"graphics": {{"model": "RTX 4060", "vram": "8GB", "chipset": "NVIDIA"}}, '
        '"ram": {{"capacity": "32GB", "ddr": "DDR4", "speed": "3200MHz"}}, '
        '"preco_max": 4000}}'
        "\n\nResponda **apenas com o JSON**, sem texto adicional."
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

def filtrar_produtos_por_categoria(specs: dict, dfs: dict):
    resultados = {}

    if "cpu" in specs:
        df = dfs["cpu"]
        cpu = specs["cpu"]
        for key in ["model", "socket", "frequency"]:
            if key in cpu:
                df = df[df[key].str.contains(cpu[key], na=False, case=False)]
        if "core_number" in cpu:
            df = df[df["core_number"].astype(str) >= str(cpu["core_number"])]
        resultados["cpu"] = df.reset_index(drop=True)

    if "ram" in specs:
        df = dfs["ram"]
        ram = specs["ram"]
        for key in ["capacity", "ddr"]:
            if key in ram:
                df = df[df[key].str.contains(ram[key], na=False, case=False)]
        if "speed" in ram:
            df["speed_num"] = df["speed"].str.extract(r'(\d+)').astype(float)
            ram_speed = float(ram["speed"].replace("MHz", "").strip())
            df = df[df["speed_num"] >= ram_speed].drop(columns=["speed_num"])
        resultados["ram"] = df.reset_index(drop=True)

    if "graphics" in specs:
        df = dfs["graphics"]
        gpu = specs["graphics"]
        for key in ["model", "vram", "chipset"]:
            if key in gpu:
                df = df[df[key].str.contains(gpu[key], na=False, case=False)]
        resultados["graphics"] = df.reset_index(drop=True)

    if "monitor" in specs:
        df = dfs["monitor"]
        monitor = specs["monitor"]
        for key in ["inches", "resolution", "refresh_rate"]:
            if key in monitor:
                df = df[df[key].astype(str).str.contains(str(monitor[key]), na=False, case=False)]
        resultados["monitor"] = df.reset_index(drop=True)

    if "mouse" in specs:
        df = dfs["mouse"]
        mouse = specs["mouse"]
        if "dpi" in mouse:
            df = df[df["dpi"].str.contains(mouse["dpi"], na=False, case=False)]
        resultados["mouse"] = df.reset_index(drop=True)

    if "keyboard" in specs:
        df = dfs["keyboard"]
        keyboard = specs["keyboard"]
        for key in ["layout", "key_type"]:
            if key in keyboard:
                df = df[df[key].str.contains(keyboard[key], na=False, case=False)]
        resultados["keyboard"] = df.reset_index(drop=True)

    return resultados

def processar_upgrade(setup_json: dict, descricao_dor: str, dfs: dict):
    llm = ChatOpenAI(model_name="gpt-4o", temperature=0)

    # Gerar especificações de upgrade
    upgrade_chain = LLMChain(llm=llm, prompt=upgrade_prompt)
    upgrade_specs_json = upgrade_chain.run({
        "setup_json": setup_json,
        "descricao_dor": descricao_dor
    })

    try:
        upgrade_specs = json.loads(upgrade_specs_json)
    except json.JSONDecodeError:
        return {"error": "Erro ao interpretar o JSON gerado pelo LLM."}

    produtos_filtrados = filtrar_produtos_por_categoria(upgrade_specs, dfs)

    if all(df.empty for df in produtos_filtrados.values()):
        return {
            "upgrade_specs": upgrade_specs,
            "produtos_encontrados": {},
            "resposta": "No momento, não encontramos produtos disponíveis nas lojas que atendam às suas necessidades para este upgrade."
        }

    products_list = {k: df.to_dict(orient="records") for k, df in produtos_filtrados.items()}

    rec_chain = LLMChain(llm=llm, prompt=recommendation_prompt)
    recommendation = rec_chain.run({
        "setup_json": json.dumps(setup_json, indent=2),
        "upgrade_specs": json.dumps(upgrade_specs, indent=2),
        "products_json": json.dumps(products_list, indent=2)
    })

    return {
        "upgrade_specs": upgrade_specs,
        "produtos_encontrados": products_list,
        "resposta": recommendation
    }
