import pandas as pd
from pymongo import MongoClient, UpdateOne
from datetime import datetime

# Configuración de MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["CHIRPS"]  # Asegúrate de usar la BD correcta
collection = db["pruebas"]  # Asegúrate de usar la colección correcta

# Ruta del archivo CSV
csv_file = "../../datos/chirps/csv/precip_tumaco_series_temporales.csv"  # Reemplaza con la ruta real

# Procesar CSV en lotes
chunksize = 10000  # Ajusta según la RAM disponible
with pd.read_csv(csv_file, chunksize=chunksize, parse_dates=["Fecha"]) as reader:  # Parsear fechas al leer
    for chunk in reader:
        chunk.columns = ["Fecha", "Precipitacion", "Latitud", "Longitud"]
        
        # Verificar si las fechas se están leyendo correctamente
        print(chunk["Fecha"].head())

        bulk_operations = []
        for fecha, grupo in chunk.groupby("Fecha"):
            documento = {
                "timestamp": fecha,
                "point_data": [
                    {
                        "point_id": f"point_{i+1}",
                        "latitude": row["Latitud"],
                        "longitude": row["Longitud"],
                        "value": row["Precipitacion"]
                    }
                    for i, row in grupo.iterrows()
                ]
            }
            bulk_operations.append(
                UpdateOne(
                    {"timestamp": fecha},  # Busca por timestamp (respeta el índice)
                    {"$set": documento},   # Actualiza si existe, inserta si no
                    upsert=True            # upsert=True: inserta si no existe
                )
            )
            print(f'Registro {fecha} añadido.')

        # Insertar en la base de datos de forma eficiente
        with client.start_session() as session:
            with session.start_transaction():
                collection.bulk_write(bulk_operations, ordered=False)

print("Carga de datos completada garantizando índice único en timestamp.")
