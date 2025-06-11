from urllib import response
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.stattools import acf
from statsmodels.tsa.stattools import adfuller


def decompose_time_series(serie, periods_s=6):
    """
    Performs seasonal decomposition of a time series into trend, seasonal, and residual components.
    
    Parameters:
    - serie (pd.Series): A Series with a DateTimeIndex containing the time series data.
    - periods_s (int): The number of periods to adjust seasonality (default: 30).
    
    Returns:
    - response (dict): A dictionary with components as pd.Series:
        - 'trend': The trend component.
        - 'seasonal': The seasonal component.
        - 'ajusted_seasonal': The adjusted seasonal component (seasonal * trend).
        - 'resid': The residual (noise) component.
    """
    model = 'additive'
    
    # Ensure the index is of type DatetimeIndex
    if not isinstance(serie.index, pd.DatetimeIndex):
        raise ValueError("The index must be of type DatetimeIndex.")
    
    # Infer frequency
    frequency = pd.infer_freq(serie.index)
    print(f"Frecuencia inferida: {frequency}")
    
    # Convert frequency to integer
    frequency_int = None
    if frequency == 'h':
        frequency_int = 1
    elif frequency == 'D':
        frequency_int = 1*24
    elif frequency == 'W':
        frequency_int = 7*24
    elif frequency == 'ME':
        frequency_int = 30*24
    elif frequency == 'Q':
        frequency_int = 90*24
    elif frequency == 'Y':
        frequency_int = 365*24
    else:
        print(f"Frecuencia '{frequency}' no soportada para conversión.")
        return None
    
    # Perform seasonal decomposition
    decomposition = seasonal_decompose(serie, model=model, period=periods_s * frequency_int)
    
    # Extract components
    trend = decomposition.trend
    seasonal = decomposition.seasonal
    resid = decomposition.resid
    ajusted_seasonal = seasonal * trend  # Adjusted seasonal component
    
    # Return as series
    response = {
        'trend': trend,
        'seasonal': seasonal,
        'ajusted_seasonal': ajusted_seasonal,
        'resid': resid
    }
    return response



def correlation(serie, lags):
    """
    Calcula la autocorrelación para una serie temporal y retorna un DataFrame.
    
    Parámetros:
    - serie (pd.Series): Serie temporal para calcular la autocorrelación.
    - lags (int): Número máximo de lags a calcular.
    
    Retorna:
    - pd.DataFrame: DataFrame con las columnas 'lag' y 'autocorrelation'.
    """
    # Calcular la autocorrelación para los lags especificados
    autocorr_values = acf(serie, nlags=lags, fft=True)
    lag_indices = np.arange(len(autocorr_values))
    
    # Crear el DataFrame
    autocorr_df = pd.DataFrame({
        'lag': lag_indices,
        'values': autocorr_values
    })
    autocorr_df.set_index('lag', inplace=True)
    return autocorr_df


def test_stationarity(time_series):
    """
    Realiza la prueba de Dickey-Fuller aumentada para verificar la estacionariedad de una serie de tiempo.
    """
    # Aplicar la prueba de Dickey-Fuller
    result = adfuller(time_series, autolag='AIC')

    print("Resultados de la Prueba de Dickey-Fuller Aumentada:")
    print(f"Estadístico de Prueba: {result[0]}")
    print(f"Valor P: {result[1]}")
    print(f"Número de Retardos Usados: {result[2]}")
    print(f"Número de Observaciones: {result[3]}")
    print("Valores Críticos:")
    for key, value in result[4].items():
        print(f"  {key}: {value}")

    # Conclusión
    if result[1] <= 0.05:
        print("\nLa serie es estacionaria (se rechaza H₀).")
    else:
        print("\nLa serie no es estacionaria (no se rechaza H₀).")
