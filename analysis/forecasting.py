import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing

def monte_carlo_simulation(equity_curve, days_to_simulate=756, simulations=10000):
    """
    Ejecuta simulaciones de Monte Carlo basadas en los retornos diarios históricos.
    Por defecto: 756 días (~ 3 años de trading de 252 días).
    """
    if equity_curve.empty or len(equity_curve) < 30:
        return np.array([])
        
    if 'Daily_TWRR' in equity_curve.columns:
        daily_returns = equity_curve['Daily_TWRR'].dropna().values
    elif 'Return' in equity_curve.columns:
        daily_returns = equity_curve['Return'].dropna().values
    else:
        daily_returns = equity_curve['Net_Value'].pct_change().dropna().values
    
    # Parametros de la curva historica
    mu = np.mean(daily_returns)
    sigma = np.std(daily_returns)
    
    # Ultimo valor
    last_price = equity_curve['Net_Value'].iloc[-1]
    
    # Rellenar matriz de retornos (simulaciones, dias)
    simulated_returns = np.random.normal(mu, sigma, (simulations, days_to_simulate))
    
    # Calcular factor de crecimiento
    price_paths = np.zeros_like(simulated_returns)
    price_paths[:, 0] = last_price * (1 + simulated_returns[:, 0])
    
    for t in range(1, days_to_simulate):
        price_paths[:, t] = price_paths[:, t-1] * (1 + simulated_returns[:, t])
        
    return price_paths

def get_monte_carlo_percentiles(price_paths, initial_price, days_to_simulate):
    """
    Extrae los percentiles (P10, P50, P90) de las rutas simuladas para graficar el "abanico".
    """
    if price_paths.size == 0:
        return pd.DataFrame()
        
    p10 = np.percentile(price_paths, 10, axis=0)
    p50 = np.percentile(price_paths, 50, axis=0)
    p90 = np.percentile(price_paths, 90, axis=0)
    
    # Creamos un dataframe con los dias proyectados
    df_sim = pd.DataFrame({
        'Day': range(1, days_to_simulate + 1),
        'P10 (Bearish)': p10,
        'P50 (Expected)': p50,
        'P90 (Bullish)': p90
    })
    
    # Insert initial value
    initial_row = pd.DataFrame({
        'Day': [0],
        'P10 (Bearish)': [initial_price],
        'P50 (Expected)': [initial_price],
        'P90 (Bullish)': [initial_price]
    })
    
    return pd.concat([initial_row, df_sim], ignore_index=True)


def trend_forecasting(equity_curve, periods=365):
    """
    Usa Suavizado Exponencial (Holt-Winters) para proyectar la tendencia
    subyacente de la curva de patrimonio.
    """
    if equity_curve.empty or len(equity_curve) < 60:
        return pd.DataFrame()
        
    # Preparar DF con indices temporales
    ts_data = equity_curve[['Date', 'Net_Value']].set_index('Date')
    
    # Aplicar Holt con tendencia pero sin estacionalidad fuerte asegurada (asumimos ruido)
    # Si detectamos suficientes datos, podriamos usar seasonal=True, pero en portafolios es inestable.
    try:
        model = ExponentialSmoothing(ts_data['Net_Value'].values, trend='add', seasonal=None, initialization_method="estimated")
        fit_model = model.fit()
        forecast = fit_model.forecast(periods)
        
        # DataFrame de proyeccion
        forecast_dates = pd.date_range(start=ts_data.index[-1] + pd.Timedelta(days=1), periods=periods)
        df_forecast = pd.DataFrame({'Date': forecast_dates, 'Forecast': forecast.values})
        return df_forecast
    except Exception as e:
        print(f"Holt-Winters Error: {e}")
        return pd.DataFrame()

def compound_interest_simulator(principal, monthly_contrib, annual_rate, dividend_rate, years, inflation_rate, var_rate, drip=True):
    """
    Calcula el crecimiento del interes compuesto mensual.
    Retorna un DataFrame con las curvas de capitalización.
    """
    months = years * 12
    # Convertir tasas anuales a mensuales
    r_cap = annual_rate / 12
    r_div = dividend_rate / 12
    r_inf = inflation_rate / 12
    r_var = var_rate / 12
    
    # Matrices
    contrib_acc = np.zeros(months + 1)
    
    # Variante DRIP (Re-inversion automatica)
    drip_val = np.zeros(months + 1)
    drip_val_up = np.zeros(months + 1)
    drip_val_down = np.zeros(months + 1)
    
    # Variante No-DRIP (Efectivo paralelo)
    nodrip_cap = np.zeros(months + 1)
    nodrip_div = np.zeros(months + 1)
    
    # Iniciar valores (Mes 0)
    contrib_acc[0] = principal
    drip_val[0] = principal
    drip_val_up[0] = principal
    drip_val_down[0] = principal
    nodrip_cap[0] = principal
    nodrip_div[0] = 0
    
    for m in range(1, months + 1):
        # Aportacion
        contrib_acc[m] = contrib_acc[m-1] + monthly_contrib
        
        # DRIP (Dividendos se suman al capital y ganan interes)
        total_rate = r_cap + r_div
        drip_val[m] = drip_val[m-1] * (1 + total_rate) + monthly_contrib
        drip_val_up[m] = drip_val_up[m-1] * (1 + total_rate + r_var) + monthly_contrib
        drip_val_down[m] = drip_val_down[m-1] * (1 + total_rate - r_var) + monthly_contrib
        
        # NO-DRIP (El capital crece a r_cap. Los div se calculan sobre el capital del mes, y no crecen)
        nodrip_cap[m] = nodrip_cap[m-1] * (1 + r_cap) + monthly_contrib
        # Los dividendos que entraron este mes
        current_divs = nodrip_cap[m-1] * r_div
        nodrip_div[m] = nodrip_div[m-1] + current_divs
        
    # Calcular Efecto Real Deflactado de la opcion escogida (por defecto usaremos el DRIP para las graficas)
    drip_val_ajustado = np.zeros(months + 1)
    for m in range(months + 1):
        drip_val_ajustado[m] = drip_val[m] / ((1 + r_inf) ** m)
        
    df = pd.DataFrame({
        'Mes': range(months + 1),
        'Año': np.arange(months + 1) / 12,
        'Contribucion_Total': contrib_acc,
        'DRIP_Total': drip_val,
        'DRIP_Superior': drip_val_up,
        'DRIP_Inferior': drip_val_down,
        'DRIP_Ajustado_Inflacion': drip_val_ajustado,
        'NoDRIP_Capital': nodrip_cap,
        'NoDRIP_Dividendos': nodrip_div,
        'NoDRIP_Total': nodrip_cap + nodrip_div
    })
    
    # Calcular multiplicadores (Factor) para los graficos de varianza
    df['Factor_DRIP'] = df['DRIP_Total'] / df['Contribucion_Total'].replace(0, 1)
    df['Factor_DRIP_Up'] = df['DRIP_Superior'] / df['Contribucion_Total'].replace(0, 1)
    df['Factor_DRIP_Down'] = df['DRIP_Inferior'] / df['Contribucion_Total'].replace(0, 1)
    df['Factor_NoDRIP'] = df['NoDRIP_Total'] / df['Contribucion_Total'].replace(0, 1)
    
    return df
