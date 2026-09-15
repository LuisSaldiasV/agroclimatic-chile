# 🌾 AgroSentinel Chile — Sistema de Inteligencia Agroclimática & Alerta Temprana de Heladas

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30%2B-FF4B4B.svg)](https://streamlit.io/)
[![DuckDB](https://img.shields.io/badge/DuckDB-Analytical%20DB-FFF000.svg)](https://duckdb.org/)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-Machine%20Learning-F7931E.svg)](https://scikit-learn.org/)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)]()

> **Plataforma modular de Ingeniería de Datos y Alerta Temprana** diseñada para monitorear, analizar y clasificar el riesgo operacional de heladas ($\le 0^\circ\text{C}$) en las principales zonas agrícolas de Chile (Valle del Aconcagua, Maipo, Cachapoal, Maule, Itata y Zona Sur).

---

## 📌 Contexto & Problema de Negocio

En el sector agroexportador de Chile (cerezos, viñedos, nogales, manzanos), una sola noche de helada no detectada durante las etapas de floración o brotación puede destruir el **100% de la producción anual**. 

Los productores agrícolas necesitan herramientas confiables para:
1. **Analizar la frecuencia histórica** y comportamiento estacional de temperaturas extremas.
2. **Consultar pronósticos oficiales** basados en modelos físicos atmosféricos.
3. **Clasificar el riesgo operacional** según variables combinadas (temperatura mínima, humedad relativa y amplitud térmica).
4. **Recibir alertas preventivas automatizadas** directamente en su teléfono antes de que ocurra el evento.

---

## 🛠️ Arquitectura de Datos y Flujo de Trabajo

El proyecto sigue una arquitectura modular y descompuesta en responsabilidades claras (*Separation of Concerns*):

```text
               ┌────────────────────────┐
               │   NASA POWER API       │ (Datos Históricos Satelitales)
               └───────────┬────────────┘
                           │ Extract & Clean (-999 Null Imputation)
                           ▼
               ┌────────────────────────┐
               │    DuckDB Storage      │ (agrotech_chile.duckdb)
               └───────────┬────────────┘
                           │
┌────────────────────────┐ │ ┌────────────────────────┐
│    Open-Meteo API      ├─┼─►   Scikit-Learn ML      │ (Clasificador de Riesgo
│ (Pronóstico a 7 días)  │ │ │ (RandomForest Model)   │  Operacional)
└───────────┬────────────┘ │ └───────────┬────────────┘
            │              │             │
            └──────────────┼─────────────┘
                           │
                           ▼
               ┌────────────────────────┐
               │   Streamlit Dashboard  │ (Visualización Interactiva)
               └───────────┬────────────┘
                           │
                           ▼
               ┌────────────────────────┐
               │  Telegram Alert Bot    │ (Push Notification System)
               └────────────────────────┘