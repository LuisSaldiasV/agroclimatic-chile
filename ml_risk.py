import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier

def clasificar_riesgo_operacional(row):
    """Asigna la etiqueta de riesgo operativo basado en umbrales agronómicos."""
    if row['temp_min'] <= 0:
        return 2  # Crítico: Helada directa
    elif row['temp_min'] <= 3 and row['humedad_relativa'] >= 80:
        return 2  # Crítico: Helada negra / alta congelación
    elif row['temp_min'] <= 4:
        return 1  # Moderado: Monitoreo preventivo
    return 0      # Bajo: Condiciones estables

def evaluar_riesgo_pronostico(df_historico: pd.DataFrame, df_pronostico: pd.DataFrame) -> pd.DataFrame:
    """Entrena el modelo con datos históricos e infiere el riesgo en el pronóstico a 7 días."""
    df_h = df_historico.copy().dropna()
    df_h['nivel_riesgo'] = df_h.apply(clasificar_riesgo_operacional, axis=1)
    
    # Variables predictoras
    features = ['temp_min', 'temp_max', 'humedad_relativa', 'amplitud_termica']
    X = df_h[features]
    y = df_h['nivel_riesgo']
    
    # Entrenamiento
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)
    
    # Inferencia en el pronóstico
    df_p = df_pronostico.copy()
    df_p['amplitud_termica'] = df_p['temp_max'] - df_p['temp_min']
    
    X_p = df_p[features]
    df_p['prediccion_riesgo'] = model.predict(X_p)
    df_p['probabilidad_critica'] = model.predict_proba(X_p)[:, -1] # Probabilidad de riesgo nivel 2
    
    return df_p