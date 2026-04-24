import pandas as pd
import numpy as np

def calculate_daily_equity(activity_df):
    """
    Reconstruye la curva de equidad diaria (Equity Curve) usando 'Saldo'.
    Tomando el último 'Saldo' de cada día.
    """
    if activity_df.empty:
         return pd.DataFrame()
         
    df_daily = activity_df.groupby('Date').last().reset_index()
    # Rellenar fechas intermedias sin actividad con el saldo anterior
    idx = pd.date_range(start=df_daily['Date'].min(), end=df_daily['Date'].max())
    df_daily.set_index('Date', inplace=True)
    df_daily.index = pd.to_datetime(df_daily.index)
    
    df_daily = df_daily.reindex(idx).ffill()
    df_daily.index.name = 'Date'
    return df_daily.reset_index()

def calculate_performance_metrics(equity_curve, activity_df=None):
    """
    Calcula: 
    - CAGR y TWRR Verdadero (Neutralizando depósitos)

    """
    if equity_curve.empty or len(equity_curve) < 2:
        return {'CAGR': 0, 'TWRR': 0, 'Total Return': 0}

    df = equity_curve.copy()
    df['Prev_Net_Value'] = df['Net_Value'].shift(1)
    
    # Calculate daily TWRR return with cash flows
    df['Daily_TWRR'] = np.where(
        df['Prev_Net_Value'] > 0, 
        (df['Net_Value'] - df.get('Net_Flow', 0)) / df['Prev_Net_Value'] - 1, 
        0
    )
    df.loc[df.index[0], 'Daily_TWRR'] = 0
    total_twrr = (1 + df['Daily_TWRR']).prod() - 1

    start_value = df['Net_Value'].iloc[0]
    end_value = df['Net_Value'].iloc[-1]
    
    if start_value == 0:
         return {'CAGR': 0, 'TWRR': 0, 'Total Return': 0}

    # Calculo de dias
    days = (df['Date'].iloc[-1] - df['Date'].iloc[0]).days
    years = days / 365.25
    
    # Total Nominal Return
    total_nominal = (end_value / start_value) - 1
    
    # CAGR
    if years > 0 and (1 + total_twrr) > 0:
        cagr = (1 + total_twrr) ** (1 / years) - 1
    else:
        cagr = 0
        
    return {
        'CAGR': cagr,
        'TWRR': total_twrr, 
        'Total Return': total_nominal
    }

def calculate_risk_metrics(equity_curve, risk_free_rate=0.04):
    """
    Volatilidad anualizada (30 días), Sharpe, Sortino, Drawdown.
    """
    if equity_curve.empty or len(equity_curve) < 2:
        return {'Volatility': 0, 'Sharpe': 0, 'Sortino': 0, 'Max Drawdown': 0}

    # Daily returns via TWRR if available, else pct_change
    if 'Daily_TWRR' in equity_curve.columns:
        equity_curve['Return'] = equity_curve['Daily_TWRR']
    else:
        equity_curve['Return'] = equity_curve['Net_Value'].pct_change()
    
    # Volatilidad móvil y total (anualizada, asumiendo 365 dias para portafolios criptos/eToro o 252 para bolsa. Usare 252)
    daily_returns = equity_curve['Return'].dropna()
    volatility = daily_returns.std() * np.sqrt(252)
    
    # Sharpe Ratio
    avg_annual_return = daily_returns.mean() * 252
    sharpe = (avg_annual_return - risk_free_rate) / volatility if volatility > 0 else 0
    
    # Sortino Ratio (solo desviacion estandar de rendimientos negativos)
    downside_returns = daily_returns[daily_returns < 0]
    downside_volatility = downside_returns.std() * np.sqrt(252)
    sortino = (avg_annual_return - risk_free_rate) / downside_volatility if downside_volatility > 0 else 0
    
    # Drawdown
    equity_curve['Peak'] = equity_curve['Net_Value'].cummax()
    equity_curve['Drawdown'] = (equity_curve['Net_Value'] - equity_curve['Peak']) / equity_curve['Peak']
    max_drawdown = equity_curve['Drawdown'].min()
    
    return {
        'Volatility': volatility,
        'Sharpe': sharpe,
        'Sortino': sortino,
        'Max Drawdown': max_drawdown,
        'Current Drawdown': equity_curve['Drawdown'].iloc[-1]
    }
    
def get_monthly_returns(equity_curve):
    """
    Agrupa los retornos diarios en una matriz por Año y Mes.
    Ideal para un Heatmap.
    """
    if equity_curve.empty:
        return pd.DataFrame()
        
    df = equity_curve.copy()
    if 'Daily_TWRR' not in df.columns:
        df['Prev_Net_Value'] = df['Net_Value'].shift(1)
        df['Daily_TWRR'] = np.where(df['Prev_Net_Value'] > 0, 
            (df['Net_Value'] - df.get('Net_Flow', 0)) / df['Prev_Net_Value'] - 1, 0)
            
    df['Year'] = df['Date'].dt.year
    df['Month'] = df['Date'].dt.month
    
    # Compound returns for the month
    df['1_plus_r'] = 1 + df['Daily_TWRR']
    monthly = df.groupby(['Year', 'Month'])['1_plus_r'].prod() - 1
    monthly = monthly.reset_index()
    monthly.rename(columns={'1_plus_r': 'Returns'}, inplace=True)
    
    # Pivot for heatmap
    heatmap_df = monthly.pivot(index='Year', columns='Month', values='Returns')
    heatmap_df.columns = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][:len(heatmap_df.columns)]
    
    return heatmap_df

import yfinance as yf
import streamlit as st
import numpy as np

@st.cache_data(show_spinner=False, ttl=86400)
def get_portfolio_pe(pos_summary):
    # Calcula el P/E ponderado armónico del portafolio (para ser precisos financieramente)
    # Ignora activos sin P/E (efectivo, cryptos)
    if pos_summary.empty:
        return np.nan
        
    pes = []
    weights = []
    
    total_val = pos_summary['Valor Neto ($)'].sum()
    if total_val == 0: return np.nan
    
    for _, row in pos_summary.iterrows():
        ticker = row['Activo']
        val = row['Valor Neto ($)']
        
        try:
            info = yf.Ticker(ticker).info
            pe = info.get('trailingPE', None)
            if pe and pe > 0: # Evitar EPS negativo
                pes.append(pe)
                weights.append(val)
        except:
            pass
            
    if not pes:
        return np.nan
        
    weights = np.array(weights) / np.sum(weights)
    pes = np.array(pes)
    
    # Harmonic Mean for P/E
    # P/E_port = 1 / sum(weight_i / P/E_i)
    weighted_pe = 1 / np.sum(weights / pes)
    return weighted_pe
