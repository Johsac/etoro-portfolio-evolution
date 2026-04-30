import pandas as pd
import numpy as np
import yfinance as yf
import streamlit as st

TICKER_MAPPING = {
    'ISP': 'ISP.MI',
    'ENG': 'ENG.MC',
    'SAND': 'SAND-USD',
    'THETA': 'THETA-USD',
    'MANA': 'MANA-USD',
    'BTC': 'BTC-USD',
    'LTC': 'LTC-USD',
    'ENJ': 'ENJ-USD',
    'A': 'ADA-USD',
    'PBR.A': 'PBR-A',
}

@st.cache_data(show_spinner=False)
def fetch_yfinance_data(tickers, start_date):
    """
    Descarga el histórico de todos los tickers en un solo request eficiente.
    Aplica limpieza para los tickers especiales (ej. BRK.B -> BRK-B)
    """
    # Limpieza previa de eToro Tickers a Yahoo Tickers
    cleaned_tickers = []
    mapping = {}
    for t in tickers:
        yf_ticker = t.upper()
        # Reglas de limpieza eToro
        yf_ticker = yf_ticker.replace('.RTH', '') 
        yf_ticker = yf_ticker.replace('BRK.B', 'BRK-B')
        
        # Crypto check (a veces eToro aade /USD)
        if len(yf_ticker) > 5 and not yf_ticker.endswith('.MI') and not yf_ticker.endswith('.L'):
            if yf_ticker in ['BTC', 'ETH', 'ADA', 'XRP', 'LTC']:
                yf_ticker = f"{yf_ticker}-USD"
            elif 'BTC' in yf_ticker:
                 yf_ticker = 'BTC-USD'
        
        mapping[t] = yf_ticker
        cleaned_tickers.append(yf_ticker)
        
    cleaned_tickers = list(set(cleaned_tickers))
    
    # Descarga masiva
    try:
        data = yf.download(cleaned_tickers, start=start_date, progress=False)['Close']
        # Si es un solo ticker, data es una Serie, forzamos a DF
        if isinstance(data, pd.Series):
             data = data.to_frame(name=cleaned_tickers[0])
    except Exception as e:
        print(f"Error descargando datos: {e}")
        data = pd.DataFrame()
        
    # Hacer Forward fill para los fines de semana y festivos
    if not data.empty:
        idx = pd.date_range(start=data.index.min(), end=pd.Timestamp.today())
        data = data.reindex(idx).ffill()
        
    return data, mapping

@st.cache_data(show_spinner=False)
def reconstruct_portfolio(activity_df):
    """
    Motor central que calcula la curva de equidad Verdadera.
    1. Agrupa el Saldo (Cash Libre) diario.
    2. Modela las posiciones abiertas dia por dia.
    3. Multiplica Unidades * Precio de Cierre Histórico.
    """
    if activity_df.empty:
        return pd.DataFrame(), pd.DataFrame()
    
    act_df = activity_df.copy()
    
    # 1. SALDO DIARIO (Efectivo Disponible)
    # Primero nos aseguramos que este cronologico
    act_df = act_df.sort_values(['Date', 'Fecha']).reset_index(drop=True)
    daily_cash = act_df.groupby('Date').last()['Saldo'].reset_index()
    daily_cash['Date'] = pd.to_datetime(daily_cash['Date'])
    daily_cash.set_index('Date', inplace=True)
    # Expand date range to cover every day
    full_idx = pd.date_range(start=daily_cash.index.min(), end=pd.Timestamp.today().normalize())
    daily_cash = daily_cash.reindex(full_idx).ffill()
    import re
    
    # 2. SEGUIMIENTO DE POSICIONES
    # Extraemos Ticker desde Detalles
    # eToro Detalles: 'AAPL/USD' o 'AAPL'
    act_df['Ticker'] = act_df['Detalles'].astype(str).str.split('/').str[0].str.strip().str.upper()
    act_df['Ticker'] = act_df['Ticker'].replace(TICKER_MAPPING)
    col_id = [c for c in act_df.columns if 'ID de' in c][0]
    
    # NET FLOWS (Flujos de capital externo para TWRR)
    act_df['Importe'] = pd.to_numeric(act_df['Importe'], errors='coerce').fillna(0)
    external_flows = act_df[act_df['Tipo'].str.contains('ep.sito|etirada', na=False, case=False, regex=True)]
    daily_cf = external_flows.groupby('Date')['Importe'].sum()
    
    daily_cash['Net_Flow'] = 0.0
    # Alinear al df
    for d, val in daily_cf.items():
        d_ts = pd.to_datetime(d).normalize()
        if d_ts in daily_cash.index:
            daily_cash.loc[d_ts, 'Net_Flow'] += val
        else:
            # si cayo en finde, mover al lunes
            later_dates = daily_cash.index[daily_cash.index >= d_ts]
            if len(later_dates)>0:
                 daily_cash.loc[later_dates[0], 'Net_Flow'] += val
                 
    # Calcular Flujo Neto Acumulado para Retorno Absoluto
    daily_cash['Cumulative_Net_Flow'] = daily_cash['Net_Flow'].cumsum()
            
    # Lógica de SPLITS
    splits_df = act_df[act_df['Tipo'].str.contains('Split', na=False, case=False)].copy()
    splits_df['Ticker'] = splits_df['Detalles'].astype(str).str.split('/').str[0].str.strip().str.upper()
    splits_df['Ticker'] = splits_df['Ticker'].replace(TICKER_MAPPING)
    splits_df['Date'] = pd.to_datetime(splits_df['Fecha'], format='%d/%m/%Y %H:%M:%S', errors='coerce')
    def get_mult(txt):
        m = re.search(r'(\d+):1', str(txt))
        return float(m.group(1)) if m else 1.0
    splits_df['Multiplier'] = splits_df['Detalles'].apply(get_mult)
    unique_splits = splits_df.groupby(['Ticker', pd.Grouper(key='Date', freq='D')])['Multiplier'].first().reset_index()
    
    # Identificar las aperturas
    open_events = act_df[act_df['Tipo'].str.contains('abierta', na=False, case=False)].copy()
    close_events = act_df[act_df['Tipo'].str.contains('p.rdidas|cerrada', na=False, case=False, regex=True)].copy()
    
    # Eliminar las cerradas al instante (o ignorar unidades NaN)
    open_events['Unidades'] = pd.to_numeric(open_events['Unidades'], errors='coerce').fillna(0)
    open_events['Importe'] = pd.to_numeric(open_events['Importe'], errors='coerce').fillna(0)
    
    # Mapeo de fecha de apertura y cierre para cada ID
    pos_history = []
    for _, row in open_events.iterrows():
        pos_id = row[col_id]
        start_dt = pd.to_datetime(row['Date'])
        
        # Buscar cuando cerro
        close_row = close_events[close_events[col_id] == pos_id]
        if not close_row.empty:
            end_dt = pd.to_datetime(close_row['Date'].iloc[0])
        else:
            end_dt = pd.Timestamp.today().normalize()
            
        # MULTIPLICAR UNIDADES POR LOS SPLITS QUE CAIGAN DESPUES DE start_dt
        units = row['Unidades']
        splits_for_ticker = unique_splits[(unique_splits['Ticker'] == row['Ticker']) & (unique_splits['Date'] > start_dt)]
        if not splits_for_ticker.empty:
             for _, s in splits_for_ticker.iterrows():
                  units *= float(s['Multiplier'])
            
        pos_history.append({
            'ID': pos_id,
            'Ticker': row['Ticker'],
            'Start': start_dt,
            'End': end_dt,
            'Units': units,
            'Invested': row['Importe']
        })
        
    pos_df = pd.DataFrame(pos_history)
    
    # Si esta vacio cortamos
    if pos_df.empty:
        return daily_cash.reset_index().rename(columns={'index':'Date'}), pd.DataFrame()
        
    unique_tickers = pos_df['Ticker'].unique().tolist()
    unique_tickers = [t for t in unique_tickers if len(t)>0 and t!='NAN' and t!='NONE']
    
    start_market = daily_cash.index.min()
    prices_df, mapping = fetch_yfinance_data(unique_tickers, start_market)
    
    if prices_df.empty:
        daily_cash['Net_Value'] = daily_cash['Saldo']
        return daily_cash.reset_index().rename(columns={'index':'Date'}), pd.DataFrame()
        
    # 3. CONSTRUCCION MATRIZ DE UNIDADES DIARIAS
    # Para cada dia y para cada ticker, sumamos unidades abiertas
    dates = daily_cash.index
    unique_yf_tickers = list(set(mapping.values()))
    matrix_units = pd.DataFrame(index=dates, columns=unique_yf_tickers).fillna(0.0)
    matrix_invested = pd.DataFrame(index=dates, columns=unique_yf_tickers).fillna(0.0)
    
    for _, row in pos_df.iterrows():
        t = mapping.get(row['Ticker'])
        if t in matrix_units.columns:
            # Mask para el rango de fechas donde esta viva la posicion
            mask = (dates >= row['Start']) & (dates < row['End']) 
            matrix_units.loc[mask, t] += float(row['Units'])
            matrix_invested.loc[mask, t] += float(row['Invested'])
            
    # Agregamos la ultima posicion del vector de fechas
    # Si pos sigue abierta hoy:
    for _, row in pos_df.iterrows():
        t = mapping.get(row['Ticker'])
        if t in matrix_units.columns and row['End'].date() == pd.Timestamp.today().date():
            matrix_units.loc[pd.Timestamp.today().normalize(), t] += float(row['Units'])
            matrix_invested.loc[pd.Timestamp.today().normalize(), t] += float(row['Invested'])
            
    # 4. VALORACION DIARIA
    # Alinear prices_df a nuestro indice
    prices_df = prices_df.reindex(dates).ffill().bfill()
    
    # Evitar problemas si falta alguna columna
    common_cols = list(set(matrix_units.columns) & set(prices_df.columns))
    
    valor_posiciones_df = matrix_units[common_cols] * prices_df[common_cols]
    
    daily_cash['Invested_Active'] = matrix_invested[common_cols].sum(axis=1)
    daily_cash['Value_Positions'] = valor_posiciones_df.sum(axis=1)
    daily_cash['Unrealized_PNL'] = daily_cash['Value_Positions'] - daily_cash['Invested_Active']
    
    # ECUACION FINAL: EFECTIVO (SALDO) + VALOR DE ACTIVOS ABIERTOS MODO M2M
    daily_cash['Net_Value'] = daily_cash['Saldo'] + daily_cash['Value_Positions']
    
    # 5. CONSTRUIR RESUMEN ACTUAL (Equivalente a tu MESA "Resumen de Portafolio de Activos")
    current_units = matrix_units.iloc[-1]
    current_invested = matrix_invested.iloc[-1]
    
    # Solo los que tienen posiciones mayores a 0 hoy
    active_tickers = current_units[current_units > 0].index
    
    current_prices = prices_df.iloc[-1].fillna(1)
    
    resumen_lista = []
    for t in active_tickers:
        unidades = current_units[t]
        invertido = current_invested[t]
        precio_act = current_prices.get(t, 0)
        valor_neto = unidades * precio_act
        gp = valor_neto - invertido
        gp_pct = (gp / invertido) if invertido > 0 else 0
        
        orig_ticker = [k for k, v in mapping.items() if v == t]
        orig_ticker = orig_ticker[0] if orig_ticker else t
        
        resumen_lista.append({
            'Asset': orig_ticker,
            'Units': round(unidades, 5),
            'Invested ($)': round(invertido, 2),
            'Current Price ($)': round(precio_act, 2),
            'Net Value ($)': round(valor_neto, 2),
            'PnL ($)': round(gp, 2),
            'PnL (%)': gp_pct
        })
        
    df_resumen = pd.DataFrame(resumen_lista).sort_values(by='Net Value ($)', ascending=False).reset_index(drop=True)
    
    return daily_cash.reset_index().rename(columns={'index':'Date'}), df_resumen
