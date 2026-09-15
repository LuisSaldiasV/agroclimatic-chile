import requests
from forecast import fetch_forecast_7days
import os
import streamlit as st

# Intenta leer desde Streamlit Secrets o desde Variables de Entorno
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or st.secrets.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID") or st.secrets.get("TELEGRAM_CHAT_ID", "")

# Obtén tu token gratis en Telegram hablando con @BotFather
TELEGRAM_BOT_TOKEN = ""
TELEGRAM_CHAT_ID = ""

def enviar_notificacion_telegram(mensaje: str):
    """Envía un mensaje de alerta formateado a un chat o grupo de Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensaje,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Error al enviar alerta por Telegram: {e}")

def verificar_y_alertar(zona_nombre: str, lat: float, lon: float):
    """Verifica el pronóstico y dispara la alerta si hay eventos de helada."""
    df_f = fetch_forecast_7days(lat, lon)
    heladas = df_f[df_f['temp_min'] <= 0]
    
    if not heladas.empty:
        msg = f"🚨 *ALERTA AGROCLIMÁTICA - {zona_nombre}*\n\n"
        msg += f"Se detectaron *{len(heladas)} eventos críticos* en los próximos 7 días:\n"
        for _, r in heladas.iterrows():
            msg += f"• *{r['fecha'].strftime('%d/%m')}*: Mínima de `{r['temp_min']:.1f}°C`\n"
        msg += "\n⚠️ *Acción recomendada:* Activar sistemas de defensa contra heladas."
        enviar_notificacion_telegram(msg)