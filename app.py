import streamlit as st
import requests
import pandas as pd
import numpy as np
import duckdb
import plotly.express as px
from datetime import datetime, timedelta

# Importamos la función desde forecast.py
from forecast import fetch_forecast_7days

# Configuración de la página
st.set_page_config(
    page_title="AgroTech Chile - Inteligencia Climática",
    page_icon="🌾",
    layout="wide"
)

# -------------------------------------------------------------------
# DICCIONARIO DE ZONAS AGRÍCOLAS EN CHILE (Latitud / Longitud)
# -------------------------------------------------------------------
ZONAS_CHILE = {
    "Valle del Aconcagua (Quillota)": {"lat": -32.879, "lon": -71.248},
    "Valle del Maipo (Paine)": {"lat": -33.811, "lon": -70.741},
    "Valle del Cachapoal (Rancagua)": {"lat": -34.170, "lon": -70.740},
    "Valle del Maule (Curicó)": {"lat": -34.985, "lon": -71.239},
    "Valle del Itata (Chillán)": {"lat": -36.606, "lon": -72.103},
    "Zona Sur (Temuco)": {"lat": -38.736, "lon": -72.590}
}

DB_FILE = "agrotech_chile.duckdb"

# -------------------------------------------------------------------
# FUNCIÓN AUXILIAR: DETERMINAR ESTACIÓN DEL AÑO (HEMISFERIO SUR)
# -------------------------------------------------------------------
def obtener_estacion_chile(fecha):
    m = fecha.month
    d = fecha.day
    
    if (m == 12 and d >= 21) or m in [1, 2] or (m == 3 and d < 21):
        return "Verano ☀️"
    elif (m == 3 and d >= 21) or m in [4, 5] or (m == 6 and d < 21):
        return "Otoño 🍂"
    elif (m == 6 and d >= 21) or m in [7, 8] or (m == 9 and d < 21):
        return "Invierno ❄️"
    else:
        return "Primavera 🌸"

# -------------------------------------------------------------------
# PIPELINE ETL CON LIMPIEZA Y ENRIQUECIMIENTO DE DATOS HISTÓRICOS
# -------------------------------------------------------------------
@st.cache_data(ttl=3600)
def fetch_and_clean_data(zona_nombre, lat, lon):
    fechas_fin = datetime.now()
    fechas_inicio = fechas_fin - timedelta(days=730)
    
    start_str = fechas_inicio.strftime("%Y%m%d")
    end_str = fechas_fin.strftime("%Y%m%d")
    
    url = "https://power.larc.nasa.gov/api/temporal/daily/point"
    params = {
        "parameters": "T2M,T2M_MIN,T2M_MAX,PRECTOTCORR,RH2M",
        "community": "AG",
        "longitude": lon,
        "latitude": lat,
        "start": start_str,
        "end": end_str,
        "format": "JSON"
    }
    
    response = requests.get(url, params=params, timeout=30)
    if response.status_code != 200:
        st.error("Error al conectar con la API de la NASA")
        return pd.DataFrame()
        
    json_data = response.json()
    properties = json_data['properties']['parameter']
    
    df = pd.DataFrame({
        'fecha_str': list(properties['T2M'].keys()),
        'temp_media': list(properties['T2M'].values()),
        'temp_min': list(properties['T2M_MIN'].values()),
        'temp_max': list(properties['T2M_MAX'].values()),
        'precipitacion_mm': list(properties['PRECTOTCORR'].values()),
        'humedad_relativa': list(properties['RH2M'].values())
    })
    
    df['fecha'] = pd.to_datetime(df['fecha_str'], format='%Y%m%d')
    df.drop(columns=['fecha_str'], inplace=True)
    
    # Data Cleaning: Reemplazar códigos nulos (-999) por NaN
    cols_numericas = ['temp_media', 'temp_min', 'temp_max', 'precipitacion_mm', 'humedad_relativa']
    for col in cols_numericas:
        df[col] = df[col].apply(lambda x: np.nan if x <= -900 else x)
    
    df.dropna(subset=['temp_min', 'temp_max', 'precipitacion_mm'], inplace=True)
    
    # Enriquece los datos con variables de análisis agrícola
    df['riesgo_helada'] = df['temp_min'].apply(lambda x: 1 if x <= 0 else 0)
    df['amplitud_termica'] = df['temp_max'] - df['temp_min']
    df['estacion'] = df['fecha'].apply(obtener_estacion_chile)
    df['zona'] = zona_nombre
    
    # Almacena en la base de datos DuckDB
    con = duckdb.connect(DB_FILE)
    con.execute("CREATE TABLE IF NOT EXISTS registro_climatico AS SELECT * FROM df WHERE 1=0")
    con.execute("DELETE FROM registro_climatico WHERE zona = ?", [zona_nombre])
    con.execute("INSERT INTO registro_climatico SELECT * FROM df")
    con.close()
    
    return df

# -------------------------------------------------------------------
# INTERFAZ PRINCIPAL STREAMLIT
# -------------------------------------------------------------------
st.title("🌾 AgroTech Chile: Inteligencia Climática & Alerta Temprana")
st.caption("Sistema de Monitoreo Agroclimático | API Open-Meteo (Pronóstico) & NASA POWER / DuckDB (Histórico)")

# --- BARRA LATERAL ---
st.sidebar.header("⚙️ Configuración del Análisis")
zona_seleccionada = st.sidebar.selectbox("1. Zona Agrícola:", list(ZONAS_CHILE.keys()))
coords = ZONAS_CHILE[zona_seleccionada]

# --- SECCIÓN DE PRONÓSTICO A 7 DÍAS ---
st.markdown(f"### 🔮 Pronóstico Preventivo Oficial a 7 Días ({zona_seleccionada})")
df_pronostico = fetch_forecast_7days(coords['lat'], coords['lon'])

if not df_pronostico.empty:
    heladas_proximas = df_pronostico[df_pronostico['riesgo_helada'] == 1]
    
    if not heladas_proximas.empty:
        st.error(f"⚠️ **¡ALERTA OPERACIONAL!** Se detectaron {len(heladas_proximas)} días con riesgo de helada (≤0°C) en los próximos 7 días.")
    else:
        st.success("✅ **Condiciones Estables:** Sin riesgo de heladas proyectado para los próximos 7 días.")
    
    # Renderizado en 7 columnas fijas
    cols_forecast = st.columns(len(df_pronostico))
    for idx, row_data in df_pronostico.iterrows():
        with cols_forecast[idx]:
            fecha_lbl = row_data['fecha'].strftime("%d/%m")
            t_min = row_data['temp_min']
            t_max = row_data['temp_max']
            precip = row_data['precipitacion_mm']
            
            alerta = "❄️" if t_min <= 0 else ("🌧️" if precip > 1 else "☀️")
            st.metric(
                label=f"{fecha_lbl} {alerta}", 
                value=f"{t_min:.1f}°C", 
                delta=f"Máx: {t_max:.1f}°C"
            )

st.divider()

# --- ANÁLISIS HISTÓRICO ---
with st.spinner(f"Cargando registro histórico para {zona_seleccionada}..."):
    df_raw = fetch_and_clean_data(zona_seleccionada, coords['lat'], coords['lon'])

if not df_raw.empty:
    st.sidebar.markdown("---")
    st.sidebar.subheader("2. Rango Histórico")
    
    min_date = df_raw['fecha'].min().date()
    max_date = df_raw['fecha'].max().date()
    
    rango_fechas = st.sidebar.date_input(
        "Selecciona el período:",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    if isinstance(rango_fechas, tuple) and len(rango_fechas) == 2:
        fecha_inicio, fecha_fin = rango_fechas
        df = df_raw[(df_raw['fecha'].dt.date >= fecha_inicio) & (df_raw['fecha'].dt.date <= fecha_fin)].copy()
    else:
        df = df_raw.copy()

    # --- KPIs HISTÓRICOS ---
    col1, col2, col3, col4 = st.columns(4)
    dias_validos = len(df)
    temp_promedio = df['temp_media'].mean() if not df.empty else 0
    precip_total = df['precipitacion_mm'].sum() if not df.empty else 0
    dias_helada = df['riesgo_helada'].sum() if not df.empty else 0

    col1.metric("Días Analizados", f"{dias_validos}")
    col2.metric("Temp. Promedio", f"{temp_promedio:.1f} °C")
    col3.metric("Lluvia Acumulada", f"{precip_total:.1f} mm")
    col4.metric("Heladas Registradas (≤0°C)", f"{int(dias_helada)}", delta_color="inverse")

    st.divider()

    # --- SECCIÓN 1: ANÁLISIS ESTACIONAL ---
    st.subheader("🍂 Análisis Estacional Histórico (Hemisferio Sur)")
    
    df_estaciones = df.groupby('estacion').agg({
        'riesgo_helada': 'sum',
        'precipitacion_mm': 'sum',
        'temp_media': 'mean'
    }).reset_index()

    col_est1, col_est2 = st.columns(2)
    
    with col_est1:
        fig_est_heladas = px.bar(
            df_estaciones,
            x='estacion',
            y='riesgo_helada',
            title="Días de Helada acumulados por Estación",
            labels={'riesgo_helada': 'Días ≤0°C', 'estacion': 'Estación'},
            color='estacion',
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        st.plotly_chart(fig_est_heladas, use_container_width=True)
        
    with col_est2:
        fig_est_precip = px.bar(
            df_estaciones,
            x='estacion',
            y='precipitacion_mm',
            title="Precipitación Acumulada por Estación (mm)",
            labels={'precipitacion_mm': 'Agua (mm)', 'estacion': 'Estación'},
            color='estacion',
            color_discrete_sequence=px.colors.sequential.Blues
        )
        st.plotly_chart(fig_est_precip, use_container_width=True)

    st.divider()

    # --- SECCIÓN 2: EVOLUCIÓN DÍA A DÍA ---
    st.subheader("🌡️ Evolución Térmica y Umbral Crítico")
    
    fig_temp = px.line(
        df, 
        x='fecha', 
        y=['temp_max', 'temp_media', 'temp_min'],
        labels={'value': 'Temperatura (°C)', 'fecha': 'Fecha', 'variable': 'Métrica'},
        color_discrete_map={
            'temp_max': '#ef4444',
            'temp_media': '#f59e0b',
            'temp_min': '#3b82f6'
        }
    )
    fig_temp.add_hline(y=0, line_dash="dash", line_color="red", annotation_text="Límite Helada (0°C)")
    st.plotly_chart(fig_temp, use_container_width=True)

    col_izq, col_der = st.columns([2, 1])

    with col_izq:
        st.subheader("🌧️ Histórico de Precipitaciones Diarias (mm)")
        fig_precip = px.bar(
            df, 
            x='fecha', 
            y='precipitacion_mm',
            labels={'precipitacion_mm': 'Agua (mm)', 'fecha': 'Fecha'},
            color_discrete_sequence=['#0284c7']
        )
        st.plotly_chart(fig_precip, use_container_width=True)

    with col_der:
        st.subheader("❄️ Detalle de Eventos de Helada")
        df_heladas = df[df['riesgo_helada'] == 1][['fecha', 'estacion', 'temp_min']].sort_values(by='fecha', ascending=False)
        if not df_heladas.empty:
            st.dataframe(df_heladas, use_container_width=True, hide_index=True)
        else:
            st.success("No se registraron días ≤0°C en el período seleccionado.")