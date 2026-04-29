#!/usr/bin/env python3
"""
ClimaBot v3.0 — Bot de Telegram para consultar el clima.
Usa Open-Meteo (https://open-meteo.com) — gratuito, sin API key.
"""
import os
import json
import sqlite3
import requests
from datetime import datetime, date
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
DB_FILE = os.getenv("DB_FILE", "climabot.db")
VERSION = "ClimaBot v3.0"

# ── Base de datos ──────────────────────────────────────────────────────────────

def init_db():
    con = sqlite3.connect(DB_FILE)
    con.execute("""
        CREATE TABLE IF NOT EXISTS ciudades_favoritas (
            user_id INTEGER PRIMARY KEY,
            ciudad  TEXT NOT NULL,
            lat     REAL,
            lon     REAL
        )
    """)
    con.commit()
    con.close()

def guardar_ciudad(user_id: int, ciudad: str, lat: float, lon: float):
    con = sqlite3.connect(DB_FILE)
    con.execute(
        "INSERT OR REPLACE INTO ciudades_favoritas (user_id, ciudad, lat, lon) VALUES (?,?,?,?)",
        (user_id, ciudad, lat, lon)
    )
    con.commit()
    con.close()

def obtener_ciudad(user_id: int) -> dict | None:
    con = sqlite3.connect(DB_FILE)
    row = con.execute(
        "SELECT ciudad, lat, lon FROM ciudades_favoritas WHERE user_id=?", (user_id,)
    ).fetchone()
    con.close()
    if row:
        return {"ciudad": row[0], "lat": row[1], "lon": row[2]}
    return None

# ── Open-Meteo API ─────────────────────────────────────────────────────────────

WMO_EMOJIS = {
    0: "☀️", 1: "🌤️", 2: "⛅", 3: "☁️",
    45: "🌫️", 48: "🌫️",
    51: "🌦️", 53: "🌦️", 55: "🌧️",
    61: "🌧️", 63: "🌧️", 65: "🌧️",
    71: "❄️", 73: "❄️", 75: "❄️", 77: "🌨️",
    80: "🌦️", 81: "🌧️", 82: "⛈️",
    85: "🌨️", 86: "🌨️",
    95: "⛈️", 96: "⛈️", 99: "⛈️",
}

WMO_DESC = {
    0: "Despejado", 1: "Mayormente despejado", 2: "Parcialmente nublado", 3: "Nublado",
    45: "Neblina", 48: "Niebla helada",
    51: "Llovizna leve", 53: "Llovizna moderada", 55: "Llovizna intensa",
    61: "Lluvia leve", 63: "Lluvia moderada", 65: "Lluvia intensa",
    71: "Nieve leve", 73: "Nieve moderada", 75: "Nieve intensa", 77: "Granizo",
    80: "Chaparrones leves", 81: "Chaparrones moderados", 82: "Chaparrones fuertes",
    85: "Nevadas leves", 86: "Nevadas intensas",
    95: "Tormenta", 96: "Tormenta con granizo leve", 99: "Tormenta con granizo fuerte",
}

def geocodificar(ciudad: str) -> dict | None:
    """Convierte nombre de ciudad a coordenadas usando Open-Meteo Geocoding."""
    try:
        r = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": ciudad, "count": 1, "language": "es", "format": "json"},
            timeout=10,
        )
        r.raise_for_status()
        resultados = r.json().get("results", [])
        if not resultados:
            return None
        res = resultados[0]
        return {
            "nombre": res.get("name", ciudad),
            "pais":   res.get("country", ""),
            "lat":    res["latitude"],
            "lon":    res["longitude"],
            "tz":     res.get("timezone", "auto"),
        }
    except Exception:
        return None

def obtener_clima_actual(lat: float, lon: float, tz: str = "auto") -> dict | None:
    try:
        r = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat, "longitude": lon,
                "current": "temperature_2m,relative_humidity_2m,apparent_temperature,"
                           "weather_code,surface_pressure,wind_speed_10m,precipitation",
                "daily": "sunrise,sunset",
                "timezone": tz,
                "forecast_days": 1,
            },
            timeout=10,
        )
        r.raise_for_status()
        return r.json()
    except Exception:
        return None

def obtener_pronostico(lat: float, lon: float, tz: str = "auto") -> dict | None:
    try:
        r = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat, "longitude": lon,
                "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum",
                "timezone": tz,
                "forecast_days": 4,
            },
            timeout=10,
        )
        r.raise_for_status()
        return r.json()
    except Exception:
        return None

def formatear_clima(data: dict, nombre_ciudad: str) -> str:
    cur = data["current"]
    code = cur["weather_code"]
    emoji = WMO_EMOJIS.get(code, "🌤️")
    desc  = WMO_DESC.get(code, "Desconocido")
    sunrise = data["daily"]["sunrise"][0][11:16] if data.get("daily") else "—"
    sunset  = data["daily"]["sunset"][0][11:16]  if data.get("daily") else "—"
    prec    = cur.get("precipitation", 0)

    return (
        f"{emoji} *Clima en {nombre_ciudad}*\n"
        f"• Estado: {desc}\n"
        f"• Temperatura: {cur['temperature_2m']:.1f} °C "
        f"(sensación {cur['apparent_temperature']:.1f} °C)\n"
        f"• Humedad: {cur['relative_humidity_2m']}%\n"
        f"• Presión: {cur['surface_pressure']:.0f} hPa\n"
        f"• Viento: {cur['wind_speed_10m']:.1f} km/h\n"
        f"• Precipitación: {prec:.1f} mm\n"
        f"🌅 Amanecer: {sunrise} | 🌇 Atardecer: {sunset}"
    )

DIAS_ES = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]

def formatear_pronostico(data: dict, nombre_ciudad: str) -> str:
    daily = data["daily"]
    lineas = [f"📅 *Pronóstico para {nombre_ciudad}*\n"]
    for i in range(1, min(4, len(daily["time"]))):
        fecha = datetime.strptime(daily["time"][i], "%Y-%m-%d")
        dia   = DIAS_ES[fecha.weekday()]
        code  = daily["weather_code"][i]
        emoji = WMO_EMOJIS.get(code, "🌤️")
        desc  = WMO_DESC.get(code, "Desconocido")
        tmax  = daily["temperature_2m_max"][i]
        tmin  = daily["temperature_2m_min"][i]
        prec  = daily["precipitation_sum"][i]
        lineas.append(
            f"🗓️ *{dia} {fecha.strftime('%d/%m')}*\n"
            f"{emoji} {desc}\n"
            f"🌡️ {tmin:.0f}°C — {tmax:.0f}°C | 💧 {prec:.1f} mm\n"
        )
    return "\n".join(lineas)

# ── Comandos ───────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🌦️ *ClimaBot* — clima en tiempo real sin API key\n\n"
        "Usá /help para ver los comandos.",
        parse_mode="Markdown",
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 *Comandos disponibles:*\n"
        "/weather \\<ciudad\\> — Clima actual\n"
        "/forecast \\[ciudad\\] — Pronóstico 3 días\n"
        "/setciudad \\<ciudad\\> — Guardar ciudad favorita\n"
        "/ahora — Clima de tu ciudad favorita\n"
        "/version — Versión del bot\n"
        "/about — Información del proyecto",
        parse_mode="MarkdownV2",
    )

async def version(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🛠️ {VERSION}")

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"🤖 *{VERSION}*\n"
        "📍 Carlos Ariel Mammoli — Mendoza, Argentina\n"
        "🌐 Datos: [Open\\-Meteo](https://open-meteo.com) \\(gratuito, sin API key\\)\n"
        "💻 [GitHub](https://github.com/camammoli/climabot)",
        parse_mode="MarkdownV2",
        disable_web_page_preview=True,
    )

async def setciudad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Indicá una ciudad. Ej: /setciudad Mendoza")
        return
    ciudad = " ".join(context.args)
    geo = geocodificar(ciudad)
    if not geo:
        await update.message.reply_text(f"❌ No se encontró la ciudad: *{ciudad}*", parse_mode="Markdown")
        return
    guardar_ciudad(update.effective_user.id, geo["nombre"], geo["lat"], geo["lon"])
    await update.message.reply_text(
        f"✅ Ciudad favorita guardada: *{geo['nombre']}, {geo['pais']}*",
        parse_mode="Markdown",
    )

async def ahora(update: Update, context: ContextTypes.DEFAULT_TYPE):
    fav = obtener_ciudad(update.effective_user.id)
    if not fav:
        await update.message.reply_text("❗ No tenés ciudad favorita. Usá /setciudad primero.")
        return
    data = obtener_clima_actual(fav["lat"], fav["lon"])
    if not data:
        await update.message.reply_text("❌ No se pudo obtener el clima. Intentá de nuevo.")
        return
    await update.message.reply_text(formatear_clima(data, fav["ciudad"]), parse_mode="Markdown")

async def weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Indicá una ciudad. Ej: /weather Córdoba")
        return
    ciudad = " ".join(context.args)
    geo = geocodificar(ciudad)
    if not geo:
        await update.message.reply_text(f"❌ No se encontró: *{ciudad}*", parse_mode="Markdown")
        return
    data = obtener_clima_actual(geo["lat"], geo["lon"], geo["tz"])
    if not data:
        await update.message.reply_text("❌ No se pudo obtener el clima. Intentá de nuevo.")
        return
    nombre = f"{geo['nombre']}, {geo['pais']}"
    await update.message.reply_text(formatear_clima(data, nombre), parse_mode="Markdown")

async def forecast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        ciudad = " ".join(context.args)
        geo = geocodificar(ciudad)
    else:
        fav = obtener_ciudad(update.effective_user.id)
        if not fav:
            await update.message.reply_text("⚠️ Indicá ciudad o guardá una con /setciudad.")
            return
        geo = {"nombre": fav["ciudad"], "pais": "", "lat": fav["lat"], "lon": fav["lon"], "tz": "auto"}

    if not geo:
        await update.message.reply_text("❌ Ciudad no encontrada.")
        return

    data = obtener_pronostico(geo["lat"], geo["lon"], geo.get("tz", "auto"))
    if not data:
        await update.message.reply_text("❌ No se pudo obtener el pronóstico.")
        return

    nombre = f"{geo['nombre']}, {geo['pais']}" if geo.get("pais") else geo["nombre"]
    await update.message.reply_text(formatear_pronostico(data, nombre), parse_mode="Markdown")

# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    if not TELEGRAM_TOKEN:
        raise RuntimeError("TELEGRAM_TOKEN no configurado en .env")
    init_db()
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start",    start))
    app.add_handler(CommandHandler("help",     help_command))
    app.add_handler(CommandHandler("version",  version))
    app.add_handler(CommandHandler("about",    about))
    app.add_handler(CommandHandler("weather",  weather))
    app.add_handler(CommandHandler("forecast", forecast))
    app.add_handler(CommandHandler("setciudad", setciudad))
    app.add_handler(CommandHandler("ahora",    ahora))
    print(f"☁️  {VERSION} iniciado...")
    app.run_polling()

if __name__ == "__main__":
    main()
