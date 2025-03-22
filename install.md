# Guía de instalación de ClimaBot

## 1. Clonar el repositorio

```bash
git clone https://github.com/camammoli/bots.git
cd bots/clima
```

## 2. Crear entorno virtual y activarlo

```bash
python3 -m venv env
source env/bin/activate
```

## 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

O manualmente:

```bash
pip install python-telegram-bot requests python-dotenv
```

## 4. Crear archivo `.env`

Copiar `.env.example` a `.env` y completarlo:

```bash
cp .env.example .env
nano .env
```

Campos requeridos:

```
TELEGRAM_TOKEN=tu_token
OPENWEATHERMAP_API_KEY=tu_api_key
CIUDADES_FILE=ciudades_favoritas.json
```

## 5. Probar el bot

```bash
python climabot.py
```

## 6. Instalar como servicio systemd (opcional)

Crear `/etc/systemd/system/climabot.service`:

```
[Unit]
Description=ClimaBot de Telegram
After=network.target

[Service]
ExecStart=/ruta/a/env/bin/python /ruta/a/climabot.py
WorkingDirectory=/ruta/a/
Restart=always
User=tu_usuario
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

Activar el servicio:

```bash
sudo systemctl daemon-reexec
sudo systemctl enable climabot
sudo systemctl start climabot
```

## 7. Contactar al bot

Buscá tu bot en Telegram con el nombre configurado en BotFather (ej: @climabot_ariel_bot).
