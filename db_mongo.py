import pandas as pd
from pymongo import MongoClient, UpdateOne
from datetime import datetime

# Cargar el conjunto de datos
df = pd.read_csv('./dataset.csv')

# Imprimir los nombres de las columnas para inspección
print("Columnas del archivo CSV:", df.columns)

# Establecer la conexión a MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['CHIRPS']
collection = db['sensor_data']

# Asegurarse de que existe un índice único en 'timestamp' para evitar duplicados
collection.create_index([("timestamp", 1)], unique=True)

# Preparar los datos para la inserción
batch_size = 1000  # Tamaño del lote de inserciones
batch = []

for idx, row in df.iterrows():
    # Preparar el registro
    record = {
        "timestamp": datetime.strptime(row['timestamp'], '%Y-%m-%d'),  # Convertir la fecha al formato datetime
        "point_data": []
    }

    # Iterar sobre las columnas (excepto la primera columna 'timestamp')
    for i in range(1, len(df.columns)):
        # Asegurarse de que la columna contiene datos de latitud y longitud en el formato correcto
        lat_lon = df.columns[i].strip('"')  # Eliminar las comillas dobles
        try:
            latitude, longitude = map(float, lat_lon.split(', '))  # Separar latitud y longitud y convertir a float
        except ValueError as e:
            print(f"Error al procesar las coordenadas para {df.columns[i]}: {e}")
            continue
        
        # Obtener el valor del sensor correspondiente
        value = row[i]

        # Añadir los datos del sensor al registro
        record['point_data'].append({
            "point_id": f"point_{i}",
            "latitude": latitude,
            "longitude": longitude,
            "value": value
        })

    # Añadir la operación de actualización a un lote
    batch.append(UpdateOne(
        {"timestamp": record["timestamp"]},  # Buscar por timestamp
        {"$set": record},  # Establecer el registro si se encuentra
        upsert=True  # Si no existe, se inserta uno nuevo
    ))

    # Cuando el tamaño del lote alcanza el tamaño especificado, realizar la inserción en lote
    if len(batch) >= batch_size:
        try:
            result = collection.bulk_write(batch)
            print(f"Batch de {len(batch)} documentos insertados/actualizados.")
        except Exception as e:
            print(f"Error al insertar el batch: {e}")
        # Resetear el lote para el siguiente ciclo
        batch = []

# Asegurarse de que se inserten los datos restantes en el último lote (si hay)
if batch:
    try:
        result = collection.bulk_write(batch)
        print(f"Batch de {len(batch)} documentos insertados/actualizados.")
    except Exception as e:
        print(f"Error al insertar el último batch: {e}")
