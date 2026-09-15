import requests
import pandas as pd

def fetch_forecast_7days(lat: float, lon: float) -> pd.DataFrame:
    """Obtiene el pronóstico real a 7 días desde la API de Open-Meteo."""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,relative_humidity_2m_mean",
        "timezone": "America/Santiago"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()['daily']
            df_forecast = pd.DataFrame({
                'fecha': pd.to_datetime(data['time']),
                'temp_max': data['temperature_2m_max'],
                'temp_min': data['temperature_2m_min'],
                'precipitacion_mm': data['precipitation_sum'],
                'humedad_relativa': data['relative_humidity_2m_mean']
            })
            df_forecast['riesgo_helada'] = df_forecast['temp_min'].apply(lambda x: 1 if x <= 0 else 0)
            return df_forecast
    except Exception as e:
        print(f"Error al consultar el pronóstico: {e}")
        
    return pd.DataFrame()