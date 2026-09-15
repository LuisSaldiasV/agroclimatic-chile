import os
import requests
import pandas as pd
import duckdb
from datetime import datetime, timedelta

# -------------------------------------------------------------------
# CONFIGURACIÓN DEL PROYECTO
# -------------------------------------------------------------------
# Coordenadas agrícolas: Curicó, Región del Maule, Chile
LATITUD = -34.985
LONGITUD = -71.239
REGION_NOMBRE = "Curicó - Valle del Maule"

# Definimos el rango de fechas (Últimos 365 días)
FECHA_FIN = datetime.now()
FECHA_INICIO = FECHA_FIN - timedelta(days=365)

START_DATE_STR = FECHA_INICIO.strftime("%Y%m%d")
END_DATE_STR = FECHA_FIN.strftime("%Y%m%d")

DB_FILE = "agrotech_maule.duckdb"

# -------------------------------------------------------------------
# 1. FUNCIÓN DE EXTRACCIÓN (NASA POWER API - Agroclimatology)
# -------------------------------------------------------------------
def fetch_nasa_weather_data(lat: float, lon: float, start: str, end: str) -> dict:
    """
    Obtiene parámetros meteorológicos diarios desde la API NASA POWER para agricultura.
    Parámetros:
    - T2M: Temperatura media a 2m (°C)
    - T2M_MIN: Temperatura mínima diaria (°C)
    - T2M_MAX: Temperatura máxima diaria (°C)
    - PRECTOTCORR: Precipitación total diaria (mm/día)
    - RH2M: Humedad relativa a 2m (%)
    """
    url = "https://power.larc.nasa.gov/api/temporal/daily/point"
    params = {
        "parameters": "T2M,T2M_MIN,T2M_MAX,PRECTOTCORR,RH2M",
        "community": "AG",  # Agroclimatology
        "longitude": lon,
        "latitude": lat,
        "start": start,
        "end": end,
        "format": "JSON"
    }
    
    print(f"📡 Consultando API NASA POWER para {REGION_NOMBRE} ({start} a {end})...")
    response = requests.get(url, params=params, timeout=30)
    
    if response.status_code == 200:
        print("✅ Datos extraídos con éxito.")
        return response.json()
    else:
        raise Exception(f"❌ Error en la API de la NASA. Status code: {response.status_code}")

# -------------------------------------------------------------------
# 2. FUNCIÓN DE TRANSFORMACIÓN (Pandas)
# -------------------------------------------------------------------
def transform_weather_data(json_data: dict) -> pd.DataFrame:
    """Transforma la respuesta JSON en un DataFrame limpio y añade indicadores agrícolas."""
    print("🔄 Transformando y calculando indicadores agrícolas...")
    properties = json_data['properties']['parameter']
    
    # Creamos el DataFrame
    df = pd.DataFrame({
        'fecha_str': list(properties['T2M'].keys()),
        'temp_media': list(properties['T2M'].values()),
        'temp_min': list(properties['T2M_MIN'].values()),
        'temp_max': list(properties['T2M_MAX'].values()),
        'precipitacion_mm': list(properties['PRECTOTCORR'].values()),
        'humedad_relativa': list(properties['RH2M'].values())
    })
    
    # Formatear la fecha
    df['fecha'] = pd.to_datetime(df['fecha_str'], format='%Y%m%d')
    df.drop(columns=['fecha_str'], inplace=True)
    
    # --- INDICADORES TÉCNICOS AGRO ---
    # 1. Indicador de Helada (Temperatura mínima <= 0°C)
    df['riesgo_helada'] = df['temp_min'].apply(lambda x: 1 if x <= 0 else 0)
    
    # 2. Ampitud Térmica (Diferencia Máx - Mín)
    df['amplitud_termica'] = df['temp_max'] - df['temp_min']
    
    # 3. Metadatos de ubicación
    df['zona'] = REGION_NOMBRE
    df['latitud'] = LATITUD
    df['longitud'] = LONGITUD
    
    # Reordenar columnas
    cols = ['fecha', 'zona', 'temp_media', 'temp_min', 'temp_max', 
            'amplitud_termica', 'precipitacion_mm', 'humedad_relativa', 'riesgo_helada']
    return df[cols]

# -------------------------------------------------------------------
# 3. FUNCIÓN DE ALMACENAMIENTO (DuckDB)
# -------------------------------------------------------------------
def load_to_duckdb(df: pd.DataFrame, db_path: str):
    """Guarda o actualiza la tabla analítica en DuckDB."""
    print(f"💾 Guardando datos en la base de datos DuckDB: {db_path}...")
    con = duckdb.connect(db_path)
    
    # Crear la tabla si no existe e insertar datos
    con.execute("""
        CREATE TABLE IF NOT EXISTS registro_climatico_agricola AS 
        SELECT * FROM df WHERE 1=0
    """)
    
    # Limpiamos tabla para evitar duplicados en esta prueba y cargamos el nuevo set
    con.execute("DELETE FROM registro_climatico_agricola WHERE zona = ?", [REGION_NOMBRE])
    con.execute("INSERT INTO registro_climatico_agricola SELECT * FROM df")
    
    # Verificación
    total_registros = con.execute("SELECT COUNT(*) FROM registro_climatico_agricola").fetchone()[0]
    heladas_totales = con.execute("SELECT SUM(riesgo_helada) FROM registro_climatico_agricola").fetchone()[0]
    
    print(f"📊 Carga completa. Registros en BD: {total_registros}")
    print(f"❄️ Días con riesgo de helada detectados en el período: {heladas_totales}")
    con.close()

# -------------------------------------------------------------------
# EJECUCIÓN PRINCIPAL (MAIN)
# -------------------------------------------------------------------
if __name__ == "__main__":
    try:
        raw_data = fetch_nasa_weather_data(LATITUD, LONGITUD, START_DATE_STR, END_DATE_STR)
        df_clean = transform_weather_data(raw_data)
        load_to_duckdb(df_clean, DB_FILE)
        print("\n🎉 ¡Pipeline ETL ejecutado con éxito!")
    except Exception as e:
        print(f"\n❌ Ocurrió un error en el pipeline: {e}")