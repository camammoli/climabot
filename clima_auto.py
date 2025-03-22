#!/usr/bin/env python3
import os
import json
import requests
from dotenv import load_dotenv
from datetime import datetime
from urllib.parse import quote

# ---------------- CONFIGURACIÓN ----------------
# Cargar variables de entorno desde .env (en el mismo directorio del script)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

# Variables de configuración
CIUDADES_FILE = os.getenv("CIUDADES_FILE", "ciudades_favoritas.json")
OPENWEATHERMAP_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID", "0"))
# ------------------------------------------------

def obtener_emoji(desc):
    desc = desc.lower()
    if "lluvia" in desc: return "🌧️"
    elif "nublado" in desc: return "☁️"
    elif "despejado" in desc: return "☀️"
    elif "tormenta" in desc: return "⛈️"
    elif "nieve" in desc: return "❄️"
    return "🌤️"

def obtener_ciudad_favorita():
    try:
        with open(CIUDADES_FILE, "r") as f:
            ciudades = json.load(f)
            return ciudades.get("124659252")  # tu user_id
    except:
        return None

def enviar_mensaje_telegram(texto):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": texto, "parse_mode": "Markdown"}
    requests.post(url, data=data)

def obtener_forecast(ciudad):
    ciudad_encoded = quote(ciudad)
    url = (
        f"https://api.openweathermap.org/data/2.5/forecast?q={ciudad_encoded}"
        f"&appid={OPENWEATHERMAP_API_KEY}&units=metric&lang=es"
    )
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()

    if data.get("cod") != "200":
        return f"❌ No se pudo obtener el pronóstico para {ciudad}."

    pronostico = {}
    for entrada in data["list"]:
        fecha = entrada["dt_txt"].split(" ")[0]
        if fecha not in pronostico:
            pronostico[fecha] = []
        pronostico[fecha].append(entrada)

    mensaje = f"📅 *Pronóstico diario para {ciudad.title()}*\n"
    dias_mostrados = 0

    for fecha, entradas in sorted(pronostico.items()):
        temps = [e["main"]["temp"] for e in entradas]
        estados = [e["weather"][0]["description"] for e in entradas]
        max_temp = max(temps)
        min_temp = min(temps)
        estado = max(set(estados), key=estados.count)
        emoji = obtener_emoji(estado)
        dia = datetime.strptime(fecha, "%Y-%m-%d").strftime("%A %d/%m")

        mensaje += (
            f"\n🗓️ *{dia}*\n"
            f"{emoji} {estado.capitalize()}\n"
            f"🌡️ Mín: {min_temp:.1f}°C | Máx: {max_temp:.1f}°C\n"
        )

        dias_mostrados += 1
        if dias_mostrados >= 3:
            break

    return mensaje

def main():
    ciudad = obtener_ciudad_favorita()
    if not ciudad:
        enviar_mensaje_telegram("⚠️ No tenés una ciudad favorita guardada. Usá /setciudad en el bot.")
        return

    try:
        mensaje = obtener_forecast(ciudad)
        enviar_mensaje_telegram(mensaje)
    except Exception as e:
        enviar_mensaje_telegram(f"❌ Error al obtener el pronóstico:\n`{e}`")

if __name__ == "__main__":
    main()
