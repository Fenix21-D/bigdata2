import pandas as pd
import numpy as np
import logging
from pymongo import MongoClient
from utils.utils import reshample_time_serie
from api_somo import DataFetcher
import matplotlib.pyplot as plt
import seaborn as sns

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# URL del API y parámetros de consulta
api_url = "http://127.0.0.1:8000/database/filter-serie/"
params = {
    "station_name": "tumaco",
    "variable_name": "Precipitación acumulada",
    "processing_level_name": "Control de calidad",
    "start_date": "2009-01-01",
    "end_date": "2023-12-31"
}

try:
    # --- Conectar a MongoDB y obtener los datos de la colección ---
    client = MongoClient('localhost', 27017)  # Conexión a MongoDB
    db = client['EVC-SOMMO']  # Nombre de la base de datos (ajustar según corresponda)
    collection = db['sensor_data']  # Nombre de la colección

    # Recuperar datos de MongoDB sin filtro
    data = collection.find().limit(10)
    chirps = pd.DataFrame(list(data))


    # Convertir los documentos de MongoDB a DataFrame de pandas
    chirps = pd.DataFrame(list(data))

    if chirps.empty:
        raise ValueError("No se encontraron datos en MongoDB.")

    # Asegúrate de que 'timestamp', 'Latitud' y 'Longitud' existan
    chirps['timestamp'] = pd.to_datetime(chirps['Fecha'])  # Convertir la fecha a datetime
    chirps.drop(columns='Fecha', inplace=True)  # Eliminar la columna 'Fecha'
    chirps.set_index('timestamp', inplace=True)
    chirps["Coordenadas"] = chirps["Latitud"].astype(str) + ", " + chirps["Longitud"].astype(str)
    
    # Filtrar por el rango de fechas
    chirps = chirps['2009':'2023']

    # Pivotar las series por coordenadas
    df_pivot = chirps.pivot_table(index=chirps.index, columns="Coordenadas", values="Precipitación")
    
    # Asegurarse de que el índice sea tz-naive
    df_pivot.index = df_pivot.index.tz_localize(None)

    # --- Obtener y preprocesar las series históricas desde la API ---
    historical_series = DataFetcher.fetch_and_process_data(api_url, params)
    if historical_series.empty:
        raise ValueError("La serie histórica está vacía.")
    
    # Convertir timestamp y asegurarse que sea tz-naive
    historical_series.index = pd.to_datetime(historical_series.index).tz_localize(None)
    
    # Re-muestrear si es necesario
    historical_series = reshample_time_serie(historical_series, 'D', 'sum')  
    historical_series.loc[historical_series['qf'] != 1, 'value'] = np.nan  # Manejo de calidad
    
    # Obtener las coordenadas de la primera fila
    lat = historical_series['latitude'].iloc[0]  # Latitud de la primera fila
    lon = historical_series['longitude'].iloc[0]  # Longitud de la primera fila

    # Renombrar la columna 'value' con las coordenadas de la primera fila
    historical_series.rename(columns={'value': f'{lat}, {lon}'}, inplace=True)
    historical_series.drop(columns={'qf','latitude','longitude'}, inplace=True)

    # --- Combinar ambas series ---
    dataset = historical_series.join(df_pivot, how='inner')  # Usar 'outer' para mantener todas las fechas
    dataset.to_csv('dataset.csv',index=True)
    #dataset = dataset['2018':'2019']
    print(dataset.columns)

    # --- Graficar todas las series combinadas ---
    plt.figure(figsize=(12, 6))
    
    # Iterar sobre todas las columnas del dataset para graficarlas
    for col in dataset.columns:
        plt.plot(dataset.index, dataset[col], label=col)

    # Configuración del gráfico
    plt.title("Comparación de Series Temporales - Tumaco")
    plt.xlabel("Fecha")
    plt.ylabel("Precipitación (mm)")
    plt.grid(True)
    plt.legend(loc='center left', bbox_to_anchor=(1, 0.5), fontsize=8)  # Colocar la leyenda fuera
    plt.tight_layout()
    plt.show()

    # Calcular e imprimir la correlación
    correlation = dataset.corr()
    print("Matriz de correlación:")
    print(correlation)

    # Graficar la matriz de correlación
    plt.figure(figsize=(8, 6))
    sns.heatmap(correlation, annot=True, cmap="coolwarm", fmt=".2f")
    plt.title("Matriz de Correlación")
    plt.tight_layout()
    plt.show()

except Exception as e:
    logger.error(f"Error al procesar los datos: {e}")
