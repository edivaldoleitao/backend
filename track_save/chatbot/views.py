from django.shortcuts import render

# Create your views here.

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

from .agents.agent_use import processar_recomendacao
from .agents.agent_upgrade import processar_upgrade
import pandas as pd

@csrf_exempt
def agent_use(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "JSON inválido"}, status=400)

        resultado = processar_recomendacao(data)

        return JsonResponse(resultado, safe=False)

    return JsonResponse({"error": "Método não permitido"}, status=405)


@csrf_exempt
def agent_upgrade(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            setup = data.get("setup")
            descricao = data.get("descricao")

            # Mock do banco
            df_cpu = pd.DataFrame([
                {"model": "Ryzen 5 5600X", "socket": "AM4", "core_number": "6", "frequency": "4.6GHz"},
                {"model": "Ryzen 7 5800X", "socket": "AM4", "core_number": "8", "frequency": "4.7GHz"},
                {"model": "Ryzen 5 3600",  "socket": "AM4", "core_number": "6", "frequency": "4.2GHz"}
            ])

            df_ram = pd.DataFrame([
                {"model": "Corsair Vengeance", "capacity": "32GB", "ddr": "DDR4", "speed": "3200MHz"},
                {"model": "Kingston Fury",     "capacity": "32GB", "ddr": "DDR4", "speed": "3200MHz"},
                {"model": "Corsair Vengeance", "capacity": "16GB", "ddr": "DDR4", "speed": "2666MHz"}
            ])

            df_graphics = pd.DataFrame([
                {"model": "RTX 3060", "vram": "12GB", "chipset": "NVIDIA"},
                {"model": "RTX 3060 Ti", "vram": "8GB", "chipset": "NVIDIA"},
                {"model": "RTX 4060", "vram": "8GB", "chipset": "NVIDIA"}
            ])

            df_monitor = pd.DataFrame([
                {"model": "LG UltraGear", "inches": "27", "resolution": "2560x1440", "refresh_rate": "144Hz"}
            ])

            df_mouse = pd.DataFrame([
                {"model": "Logitech G502", "dpi": "16000"}
            ])

            df_keyboard = pd.DataFrame([
                {"model": "HyperX Alloy", "layout": "ABNT2", "key_type": "Mecânico"}
            ])

            dfs = {
                "cpu": df_cpu,
                "ram": df_ram,
                "graphics": df_graphics,
                "monitor": df_monitor,
                "mouse": df_mouse,
                "keyboard": df_keyboard
            }

            resultado = processar_upgrade(setup, descricao, dfs)
            return JsonResponse(resultado, safe=False)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Método não permitido"}, status=405)