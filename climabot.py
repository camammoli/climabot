#!/usr/bin/env python3
import os
import json
import requests
from datetime import datetime
from urllib.parse import quote
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Cargar configuración desde .env
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENWEATHERMAP_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY")
CIUDADES_FILE = os.getenv("CIUDADES_FILE", "ciudades_favoritas.json")
VERSION = 'ClimaBot v2.2'

# Funciones auxiliares

def obtener_emoji(descripcion):
    descripcion = descripcion.lower()
    if "lluvia" in descripcion:
        return "🌧️"
    elif "nublado" in descripcion:
        return "☁️"
    elif "despejado" in descripcion:
        return "☀️"
    elif "tormenta" in descripcion:
        return "⛈️"
    elif "nieve" in descripcion:
        return "❄️"
    else:
        return "🌤️"

def guardar_ciudad(user_id, ciudad):
    ciudades = {}
    if os.path.exists(CIUDADES_FILE):
        with open(CIUDADES_FILE, 'r') as f:
            ciudades = json.load(f)
    ciudades[str(user_id)] = ciudad
    with open(CIUDADES_FILE, 'w') as f:
        json.dump(ciudades, f)

def obtener_ciudad(user_id):
    if os.path.exists(CIUDADES_FILE):
        with open(CIUDADES_FILE, 'r') as f:
            ciudades = json.load(f)
            return ciudades.get(str(user_id))
    return None

# Comandos
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🌦️ ¡Hola! Soy tu bot del clima. Usá /help para ver los comandos disponibles.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 *Comandos disponibles:*\n"
        "/start - Bienvenida\n"
        "/help - Mostrar esta ayuda\n"
        "/weather <ciudad> - Clima actual\n"
        "/forecast [ciudad] - Pronóstico extendido\n"
        "/setciudad <ciudad> - Guardar ciudad favorita\n"
        "/ahora - Clima actual de tu ciudad favorita\n"
        "/version - Ver versión del bot\n"
        "/about - Información del proyecto",
        parse_mode='Markdown'
    )

async def version(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🛠️ Versión actual: {VERSION}")

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *ClimaBot* - Asistente de clima personalizado\n"
        "📍 Desarrollado por Carlos Ariel Mammoli en Mendoza, Argentina\n"
        "💡 Usa la API de OpenWeatherMap para brindar información del clima\n"
        "🧠 Potenciado con sugerencias generadas con la ayuda de ChatGPT\n"
        "📅 Proyecto personal iniciado en 2025",
        parse_mode='Markdown'
    )

async def setciudad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Indicá una ciudad. Ej: /setciudad Mendoza")
        return
    ciudad = " ".join(context.args)
    guardar_ciudad(update.effective_user.id, ciudad)
    await update.message.reply_text(f"✅ Ciudad favorita guardada: *{ciudad}*", parse_mode='Markdown')

async def ahora(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ciudad = obtener_ciudad(update.effective_user.id)
    if not ciudad:
        await update.message.reply_text("❗ No tenés una ciudad guardada. Usá /setciudad primero.")
        return
    context.args = [ciudad]
    await weather(update, context)

async def weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Indicá una ciudad. Ej: /weather Córdoba")
        return

    city = " ".join(context.args)
    url = (
        f"http://api.openweathermap.org/data/2.5/weather?q={quote(city)}"
        f"&appid={OPENWEATHERMAP_API_KEY}&units=metric&lang=es"
    )

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get("cod") != 200:
            mensaje = data.get("message", "Ciudad no encontrada.")
            await update.message.reply_text(f"🌩️ No se pudo obtener el clima para *{city}*:\n_{mensaje}_", parse_mode='Markdown')
            return

        temp = data['main']['temp']
        feels_like = data['main']['feels_like']
        pressure = data['main']['pressure']
        humidity = data['main']['humidity']
        visibility = data.get('visibility', 0) // 1000
        wind_speed = data['wind']['speed']
        description = data['weather'][0]['description']
        emoji = obtener_emoji(description)
        sunrise = datetime.fromtimestamp(data['sys']['sunrise']).strftime('%H:%M')
        sunset = datetime.fromtimestamp(data['sys']['sunset']).strftime('%H:%M')

        message = (
            f"{emoji} *Clima en {city.title()}*\n"
            f"• Estado: {description.capitalize()}\n"
            f"• Temperatura: {temp:.1f} °C (sensación {feels_like:.1f} °C)\n"
            f"• Humedad: {humidity}%\n"
            f"• Presión: {pressure} hPa\n"
            f"• Visibilidad: {visibility} km\n"
            f"• Viento: {wind_speed:.1f} m/s\n"
            f"🌅 Amanecer: {sunrise} | 🌇 Atardecer: {sunset}"
        )
        await update.message.reply_text(message, parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"❌ Error al obtener el clima:\n`{e}`", parse_mode='Markdown')

async def forecast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        city = " ".join(context.args)
    else:
        ciudad_fav = obtener_ciudad(update.effective_user.id)
        if not ciudad_fav:
            await update.message.reply_text("⚠️ No se indicó ciudad ni tenés una guardada. Usá /forecast Mendoza o /setciudad primero.")
            return
        city = ciudad_fav

    url = (
        f"https://api.openweathermap.org/data/2.5/forecast?q={quote(city)}"
        f"&appid={OPENWEATHERMAP_API_KEY}&units=metric&lang=es"
    )

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get("cod") != "200":
            await update.message.reply_text(f"❌ No se pudo obtener el pronóstico para {city}.")
            return

        pronostico = {}
        for entrada in data["list"]:
            fecha = entrada["dt_txt"].split(" ")[0]
            if fecha not in pronostico:
                pronostico[fecha] = []
            pronostico[fecha].append(entrada)

        mensaje = f"📅 *Pronóstico extendido para {city.title()}*\n"
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

        await update.message.reply_text(mensaje, parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"❌ Error al obtener el pronóstico:\n`{e}`", parse_mode='Markdown')

# Iniciar el bot
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("version", version))
    app.add_handler(CommandHandler("about", about))
    app.add_handler(CommandHandler("weather", weather))
    app.add_handler(CommandHandler("forecast", forecast))
    app.add_handler(CommandHandler("setciudad", setciudad))
    app.add_handler(CommandHandler("ahora", ahora))
    print("☁️ ClimaBot iniciado...")
    app.run_polling()

if __name__ == '__main__':
    main()
