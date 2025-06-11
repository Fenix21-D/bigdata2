from cProfile import label
from matplotlib import markers
from sympy import true
from api_somo import DataFetcher, fetch_qf 
from utils.utils import categorize_precipitation
import matplotlib.pyplot as plt
import logging

# Setting up logging for the main script
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

api_url = "http://127.0.0.1:8000/database/filter-serie/"
params = {
    "station_name": "tumaco",
    "variable_name": "Precipitación acumulada",
    "processing_level_name": "Control de calidad",
    "start_date":"2009-01-01",
    "end_date":"2009-12-31"
    }

try:
    # 1. Fetch and process the data
    historical_series = DataFetcher.fetch_and_process_data(api_url, params)

    if historical_series.empty:
        raise ValueError("The historical series is empty.")

    # Additional processing with the historical series
    logger.info(f"Fetched historical series: {historical_series.head(0)}")

except Exception as e:
    logger.error(f"Error fetching historical series: {e}")

print(historical_series.describe())

plt.figure()

plt.plot(historical_series.index, historical_series['value'], marker='o', label='precipitaciones')
plt.title('grafico de recipitaciones', fontsize=16)
plt.xlabel('Fecha')
plt.ylabel('precipitaciones (ml)')
plt.grid(true, linestyle='--', alpha=0.7)
plt.legend(fontsize=12)
plt.tight_layout()

plt.show()