# ClimaBot

**Versión actual:** v2.2  
**Fecha:** 2025-03-22  
**Autor:** Carlos Ariel Mammoli  
**Ubicación:** Mendoza, Argentina  
**Repositorio:** [GitHub - camammoli/bots](https://github.com/camammoli/bots)

ClimaBot es un bot de Telegram que permite consultar el estado del clima actual y el pronóstico extendido para cualquier ciudad del mundo. También permite guardar una ciudad favorita por usuario para consultas rápidas.

Este bot está desarrollado en Python 3, utiliza la API de OpenWeatherMap y se ejecuta en un entorno Debian. Fue creado como parte de un proyecto personal y asistido en su desarrollo por ChatGPT.

## Características

- Consultar clima actual con `/weather <ciudad>`
- Pronóstico extendido de 3 días con `/forecast [ciudad]`
- Guardar ciudad favorita por usuario con `/setciudad`
- Obtener el clima de la ciudad guardada con `/ahora`
- Información de versión (`/version`), ayuda (`/help`) y autor (`/about`)
- Respuesta enriquecida con emojis según el estado del clima

## Requisitos

- Python 3.9 o superior
- `python-telegram-bot`
- `requests`
- `python-dotenv`
- Acceso a la API de [OpenWeatherMap](https://openweathermap.org/api)
- Bot creado en [BotFather](https://t.me/botfather) con su token

## Licencia

Este proyecto está licenciado bajo los términos de la Licencia Pública General GNU v3.0. Ver archivo `LICENSE`.

## Instalación

Ver archivo `install.md` para detalles paso a paso de instalación y despliegue.

## Mejoras futuras

Ver archivo `mejoras_clima.md`.
