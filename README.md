# ClimaBot

Bot de Telegram para consultar el clima actual y el pronóstico extendido de cualquier ciudad del mundo.

**No requiere API key** — usa [Open-Meteo](https://open-meteo.com), gratuito y sin registro.

## Características

- `/weather <ciudad>` — Clima actual (temperatura, sensación térmica, humedad, presión, viento, precipitaciones, amanecer/atardecer)
- `/forecast [ciudad]` — Pronóstico de 3 días con min/max y precipitaciones
- `/setciudad <ciudad>` — Guardar ciudad favorita por usuario
- `/ahora` — Clima de la ciudad favorita guardada
- Soporte para cualquier ciudad del mundo con geocodificación automática
- Base de datos SQLite por usuario (sin archivos JSON compartidos)

## Instalación

```bash
git clone https://github.com/camammoli/climabot.git
cd climabot

python3 -m venv env
source env/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Editar .env y poner el TELEGRAM_TOKEN

python climabot.py
```

## Variables de entorno

| Variable | Descripción | Requerida |
|---|---|---|
| `TELEGRAM_TOKEN` | Token del bot (obtener en @BotFather) | Sí |
| `DB_FILE` | Ruta del archivo SQLite | No (default: `climabot.db`) |

## Ejecutar como servicio systemd

```ini
[Unit]
Description=ClimaBot Telegram
After=network.target

[Service]
Type=simple
User=tu_usuario
WorkingDirectory=/ruta/a/climabot
ExecStart=/ruta/a/climabot/env/bin/python climabot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo cp climabot.service /etc/systemd/system/
sudo systemctl enable --now climabot
```

## Datos meteorológicos

Powered by [Open-Meteo](https://open-meteo.com) — API abierta, sin API key, sin límites de uso para proyectos no comerciales.

## Versión

v3.0 — migración a Open-Meteo, base de datos SQLite, sin dependencia de OpenWeatherMap.

## Licencia

GNU GPL v3.0 — Carlos Ariel Mammoli, Mendoza, Argentina
