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

```

⚙️ Componentes del Sistema
app.py:Interfaz interactiva desarrollada en Streamlit. Incluye selectores regionales dinámicos, filtros de fecha personalizados, indicadores KPIs y visualización por estaciones del año (Hemisferio Sur).
forecast.py: Integración con la API meteorológica de Open-Meteo (modelos ECMWF/GFS) para proyectar condiciones climáticas reales a 7 días sin alucinaciones.
ml_risk.py: Modelo de clasificación con RandomForestClassifier de Scikit-Learn que evalúa el nivel de riesgo operativo (Bajo, Moderado, Crítico) según la interacción de variables climáticas.
alerts.py: Bot automatizado de Telegram que emite notificaciones preventivas inmediatas al teléfono del usuario si el modelo detecta días con $T_{min} \le 0^\circ\text{C}$.agrotech_chile.
duckdb: Motor de base de datos analítica empotrada (OLAP) para consultas de alta velocidad.

🧠 Criterio Técnico & Calidad de Datos (Data Quality)
1. Tratamiento de Códigos Nulos (-999)Las APIs satelitales como NASA POWER retornan la constante -999 para representar días cuyo procesamiento aún no concluye.Solución aplicada: El pipeline ETL detecta automáticamente estos valores extremados ($\le -900$), los transforma en NaN e imputa o descarta registros incompletos, evitando distorsiones en totales acumulados de precipitación y escala térmica.
2. Decisiones de Ingeniería y Ética de Machine LearningEn lugar de entrenar modelos ingenuos de Time-Series para intentar predecir el clima desde cero (lo cual es impreciso y riesgoso para uso operacional real), el sistema reutiliza los pronósticos de súper-computadoras globales (Open-Meteo) y aplica el Machine Learning para resolver el problema de negocio: estimar el impacto y la probabilidad de daño operacional en el cultivo.

🚀 Instalación y Ejecución Local
Requisitos PreviosPython 3.10 o superior.
Git instalado.

Pasos
Clonar el repositorio: 
git clone [https://github.com/TU_USUARIO/agrosentinel-chile.git](https://github.com/TU_USUARIO/agrosentinel-chile.git)
cd agrosentinel-chile

Crear y activar un entorno virtual:
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate

Instalar dependencias:
pip install -r requirements.txt

Ejecutar la aplicación en Streamlit:
python -m streamlit run app.py

📦 Stack TecnológicoLenguaje: 
Python 3.10+
Almacenamiento Analítico: DuckDB
Manipulación de Datos: Pandas, NumPy
Visualización: Streamlit, Plotly Express
Machine Learning: Scikit-Learn (Random Forest)
APIs Integradas: NASA POWER API, Open-Meteo API, Telegram Bot API

✉️ Contacto & Redes
Desarrollado como proyecto de ingeniería de datos aplicado al sector agrícola en Chile.
LinkedIn: www.linkedin.com/in/LSValenzuela
GitHub: @LuisSaldiasV
---
