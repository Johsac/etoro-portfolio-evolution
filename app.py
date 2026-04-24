import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from data_loader import load_etoro_data
from financial_metrics import calculate_performance_metrics, calculate_risk_metrics, get_monthly_returns
from forecasting import monte_carlo_simulation, get_monte_carlo_percentiles, trend_forecasting
from portfolio_reconstructor import reconstruct_portfolio

# Configuración de página
st.set_page_config(
    page_title="eToro Portfolio Evolution",
    layout="wide",
    page_icon="📈",
    initial_sidebar_state="expanded"
)

# Estilo Premium
st.markdown("""
<style>
    /* Global styles and typography */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Metrics panel glassmorphism */
    div[data-testid="metric-container"] {
        background-color: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 5% 5% 5% 10%;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
</style>
""", unsafe_allow_html=True)

# --- Sidebar Control & Inputs ---
with st.sidebar:
    with st.expander("📂 Carga de Datos", expanded=True):
        st.markdown("Sube tu archivo de estado de cuenta de eToro.")
        uploaded_file = st.file_uploader("Upload Excel (.xlsx)", type=['xlsx'])
        
        if uploaded_file is None:
            # Mostramos estado vacío
            st.info("👈 Sube tu archivo de eToro ('Account Statement') exportado en Excel para comenzar el análisis.")
            st.stop()

        # --- Procesar Archivo ---
        with st.spinner("Procesando datos..."):
            try:
                data_dict = load_etoro_data(uploaded_file)
                activity = data_dict['activity']
                closed_pos = data_dict['closed_positions']
                dividends = data_dict['dividends']
                st.success("¡Datos cargados con éxito!")
            except Exception as e:
                st.error(f"Error al analizar el archivo: {e}")
                st.stop()
    
    st.markdown("<br><br><br>", unsafe_allow_html=True) # Espaciador para empujar abajo
    st.markdown("---")
    # Estilo especial para el toggle de IA
    st.markdown("""
        <style>
        /* 1. RESETEO TOTAL */
        [data-testid="stSidebar"] label p {
            font-size: 1rem !important;
            font-weight: normal !important;
            color: white !important;
        }

        /* 2. ESTILO EXCLUSIVO MEDIANTE ANCLA */
        #ai-anchor + div {
            border: 3px solid #00ff9d !important;
            border-radius: 15px !important;
            padding: 15px !important;
            background: rgba(0, 255, 157, 0.1) !important;
            margin-top: 20px !important;
        }

        #ai-anchor + div label p {
            font-size: 1.4rem !important;
            font-weight: 900 !important;
            color: #00ff9d !important;
            text-transform: uppercase !important;
            letter-spacing: 0px !important;
        }

        #ai-anchor + div [data-baseweb="checkbox"] {
            transform: scale(1.4) !important;
        }
        </style>
        <div id="ai-anchor"></div>
    """, unsafe_allow_html=True)
    
    show_ai = st.toggle("Preguntar a la IA", value=False, key="toggle_ia_pro")

# --- Mapeo de Benchmarks ---
BENCHMARKS = {
    'S&P 500': '^GSPC',
    'NASDAQ 100': '^NDX',
    'MSCI World': 'URTH'
}

# --- Layout Principal Dinámico ---
if show_ai:
    main_col, ai_col = st.columns([0.7, 0.3])
else:
    main_col = st.container()

with main_col:
    st.title(" eToro Portfolio Evolution")
    st.markdown("Plataforma de análisis profundo e histórico de tu patrimonio en eToro.")
    
    # --- Computaciones Base ---
    with st.spinner("Descargando precios históricos de Yahoo Finance y procesando Splits..."):
        try:
            equity_curve, pos_summary_realtime = reconstruct_portfolio(activity)
            perf_metrics = calculate_performance_metrics(equity_curve, activity)
            risk_metrics = calculate_risk_metrics(equity_curve)
        except Exception as e:
            st.error(f"Error en yfinance: {e}")
            st.stop()

    if equity_curve.empty:
        st.warning("No se pudo construir la Curva de Equidad Verdadera. Revisa los datos.")
        st.stop()

    # --- Layout de Pestañas ---
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "📊 Resumen de Cuenta", 
            "🧮 Desglose & Composición",
            "📉 Riesgo & Drawdown", 
            "🌱 Simulador Interés Compuesto",
            "🔮 Predicciones (Monte Carlo)",
            "📚 Histórico de Operaciones"
        ])

    with tab1:
        st.subheader("⚡ Métricas de Rendimiento Histórico")
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Total Return (Nominal)", f"{perf_metrics['Total Return']*100:.2f}%", help="Mide la ganancia total bruta del portafolio.")
        with col2:
            st.metric("TWRR (Flujos Ajustados)", f"{perf_metrics['TWRR']*100:.2f}%", help="Time-Weighted Return: Rendimiento real aislando el efecto de depósitos/retiros.")
        with col3:
            st.metric("Volatilidad Anualizada", f"{risk_metrics['Volatility']*100:.2f}%", help="Desviación típica anual; mide cuánto varían los precios históricamente.")
        with col4:
            st.metric("Ratio Sharpe", f"{risk_metrics['Sharpe']:.2f}", help="Retorno ajustado al riesgo. >1.0 es considerado aceptable, >2.0 es excelente.")
        with col5:
            from financial_metrics import get_portfolio_pe
            pe_ratio = get_portfolio_pe(pos_summary_realtime)
            if pd.notnull(pe_ratio):
                st.metric("📊 P/E del Portafolio", f"{pe_ratio:.1f}x", help="Price-to-Earnings Ratio promedio del portafolio (Trailling P/E promedio de las acciones activas).")
            else:
                st.metric("📊 P/E del Portafolio", "N/A", help="Price-to-Earnings Ratio promedio del portafolio (Trailling P/E promedio de las acciones activas).")

        # Fallback Nominal View (Old Chart)
        st.markdown("### 📊 Evolución del Saldo Nominal (Net Value Absoluto)")
        fig_abs = go.Figure()
        fig_abs.add_trace(go.Scatter(x=equity_curve['Date'], y=equity_curve['Net_Value'], mode='lines', 
                                    name='Valor Portafolio ($)', line=dict(color='#00ff9d', width=2),
                                    fill='tozeroy', fillcolor='rgba(0, 255, 157, 0.1)'))
        fig_abs.update_layout(template="plotly_dark", margin=dict(l=0, r=0, t=30, b=0),
                             hovermode="x unified", xaxis_title="", yaxis_title="Equidad Neta ($)")
        st.plotly_chart(fig_abs, use_container_width=True)

        # Benchmarks & Timeframes
        st.markdown("### 📈 Rendimiento Normalizado vs Benchmarks (Base 100%)")
        
        col_bench, col_time = st.columns([1, 2])
        with col_bench:
             bench_sel = st.selectbox("Añadir Benchmark", ['Ninguno'] + list(BENCHMARKS.keys()) + ['Personalizado'])
             custom_bench = ""
             if bench_sel == 'Personalizado':
                 custom_bench = st.text_input("Ingresa Ticker Yahoo Finance (Ej. URTH, ARKK):")
                 
        with col_time:
             st.write("Filtro Temporal:")
             timeframe = st.radio("Ventana:", ["Max", "5Y", "1Y", "YTD", "6M", "3M"], horizontal=True, label_visibility="collapsed")
        
        # Filtro Temporal
        df_plot = equity_curve.copy()
        end_date = df_plot['Date'].max()
        if timeframe == '5Y': start_date = end_date - pd.DateOffset(years=5)
        elif timeframe == '1Y': start_date = end_date - pd.DateOffset(years=1)
        elif timeframe == 'YTD': start_date = pd.to_datetime(f"{end_date.year}-01-01")
        elif timeframe == '6M': start_date = end_date - pd.DateOffset(months=6)
        elif timeframe == '3M': start_date = end_date - pd.DateOffset(months=3)
        else: start_date = df_plot['Date'].min()
        
        df_plot = df_plot[df_plot['Date'] >= start_date].copy()
        
        # Normalizar Retorno (Base 0 en start_date)
        # TWRR Acumulado desde start_date
        if 'Daily_TWRR' in df_plot.columns:
             df_plot['TWRR_Period'] = (1 + df_plot['Daily_TWRR']).cumprod() - 1
        else:
             # Fallback
             initial_val = df_plot['Net_Value'].iloc[0]
             df_plot['TWRR_Period'] = (df_plot['Net_Value'] / initial_val) - 1 if initial_val != 0 else 0
        
        fig_eq = go.Figure()
        fig_eq.add_trace(go.Scatter(x=df_plot['Date'], y=df_plot['TWRR_Period'], mode='lines', 
                                    name='Portafolio (TWRR)', line=dict(color='#00ff9d', width=3),
                                    fill='tozeroy', fillcolor='rgba(0, 255, 157, 0.1)'))
        
        # Agregar Benchmark
        if bench_sel != 'Ninguno':
            bench_ticker = custom_bench if bench_sel == 'Personalizado' else BENCHMARKS[bench_sel]
            if bench_ticker:
                import yfinance as yf
                try:
                    b_data = yf.download(bench_ticker.upper(), start=start_date, end=end_date+pd.Timedelta(days=1), progress=False)['Close']
                    if isinstance(b_data, pd.DataFrame) and not b_data.empty: 
                         b_data = b_data[bench_ticker.upper()] if bench_ticker.upper() in b_data.columns else b_data.iloc[:, 0]
                    b_data = b_data.reindex(df_plot['Date']).ffill().bfill()
                    b_ret = b_data.pct_change().fillna(0)
                    # Ensure the first day is exactly 0
                    b_ret.iloc[0] = 0
                    b_cum = (1 + b_ret).cumprod() - 1
                    fig_eq.add_trace(go.Scatter(x=df_plot['Date'], y=b_cum, mode='lines', 
                                                name=bench_ticker.upper(), line=dict(color='#ff9900', width=2, dash='dash')))
                except Exception as e:
                    pass

        fig_eq.update_layout(template="plotly_dark", margin=dict(l=0, r=0, t=30, b=0),
                             hovermode="x unified", xaxis_title="", yaxis_title="Retorno Acumulado",
                             yaxis_tickformat='.1%')
        st.plotly_chart(fig_eq, use_container_width=True)
        
        # Rendimientos Mensuales y Dividendos
        st.markdown("### 📅 Heatmap de Rendimientos Mensuales")
        monthly_ret = get_monthly_returns(equity_curve)
        if not monthly_ret.empty:
            fig_heat = px.imshow(monthly_ret * 100, text_auto=".1f", color_continuous_scale="RdYlGn",
                                 color_continuous_midpoint=0,
                                 labels=dict(x="Mes", y="Año", color="Retorno (%)"),
                                 template="plotly_dark")
            fig_heat.update_xaxes(side="top")
            st.plotly_chart(fig_heat, use_container_width=True)
            
        # SECTION DIVIDENDOS
        st.markdown("### 💸 Ingresos Pasivos (Dividendos eToro)")
        div_df = activity[activity['Tipo'].str.contains('dividendo', na=False, case=False)].copy()
        if not div_df.empty:
             col_div_op, _ = st.columns([1, 2])
             with col_div_op:
                 div_group = st.radio("Frecuencia:", ["Mensual", "Trimestral", "Anual"], horizontal=True)
                 
             freq_map = {"Mensual": "M", "Trimestral": "Q", "Anual": "Y"}
             freq = freq_map[div_group]
             
             div_df['Date'] = pd.to_datetime(div_df['Date'])
             div_df['Importe'] = pd.to_numeric(div_df['Importe'], errors='coerce').fillna(0)
             
             div_grouped = div_df.groupby(div_df['Date'].dt.to_period(freq))['Importe'].sum().reset_index()
             div_grouped['Date'] = div_grouped['Date'].dt.to_timestamp()
             
             fig_div = go.Figure()
             # Configurar el formato del eje X según el grupo
             x_format = "%b %Y" if freq == "M" else ("%Y-Q%q" if freq == "Q" else "%Y")
             
             fig_div.add_trace(go.Bar(x=div_grouped['Date'], y=div_grouped['Importe'], 
                                    marker_color='#f1c40f', name='Dividendos',
                                    text=div_grouped['Importe'].apply(lambda x: f"${x:.1f}"),
                                    textposition='auto'))
             fig_div.update_layout(template="plotly_dark", margin=dict(l=0, r=0, t=30, b=0),
                                  xaxis_title="", yaxis_title="Ingresos ($)",
                                  xaxis=dict(tickformat=x_format))
             st.plotly_chart(fig_div, use_container_width=True)
             
             # Suma total rápida
             st.caption(f"**Total Histórico Bruto:** ${div_df['Importe'].sum():.2f} USD generados pasivamente.")


    with tab2:
        st.header("🧮 Desglose Estratégico del Portafolio")
        
        st.markdown("#### 🥧 Distribución Actual")
        
        # Opciones de Agrupación
        groupby_opt = st.radio("Agrupar por:", ["Activo Individual", "Categoría (Acciones, ETF, etc.)"], horizontal=True)
        
        if not pos_summary_realtime.empty:
            df_pie = pos_summary_realtime[pos_summary_realtime['Valor Neto ($)'] > 1].copy()
            
            if groupby_opt == "Categoría (Acciones, ETF, etc.)":
                # Mapear desde df activity
                from portfolio_reconstructor import TICKER_MAPPING
                temp_act = activity[['Detalles', 'Tipo de activo']].dropna()
                temp_act['Ticker_Clean'] = temp_act['Detalles'].apply(lambda x: TICKER_MAPPING.get(str(x).split('/')[0].strip().upper(), str(x).split('/')[0].strip().upper()))
                
                category_map = temp_act.drop_duplicates('Ticker_Clean').set_index('Ticker_Clean')['Tipo de activo'].to_dict()
                df_pie['Agrupación'] = df_pie['Activo'].map(category_map).fillna('Desconocido')
                df_pie = df_pie.groupby('Agrupación')['Valor Neto ($)'].sum().reset_index()
                fig_pie = px.pie(df_pie, values='Valor Neto ($)', names='Agrupación', 
                                 hole=0.4, color_discrete_sequence=px.colors.sequential.Teal)
            else:
                fig_pie = px.pie(df_pie, values='Valor Neto ($)', names='Activo', 
                                 hole=0.4, color_discrete_sequence=px.colors.sequential.Teal)
                
            fig_pie.update_layout(template="plotly_dark", margin=dict(t=30, b=0, l=0, r=0))
            st.plotly_chart(fig_pie, use_container_width=True)
            
        st.markdown("---")
        st.markdown("#### 🧊 Evolución del Capital (Absoluto y Porcentual)")
        chart_mode = st.radio("Métrica:", ["Valor Absoluto (USD)", "Porcentaje Normalizado (%)"], horizontal=True)
        
        df_g = equity_curve.copy()
        
        # Base deposits
        initial_saldo = max(0, df_g['Net_Value'].iloc[0] - df_g['Net_Flow'].iloc[0]) if not df_g.empty else 0
        df_g['Depositos_Acumulados'] = df_g['Net_Flow'].cumsum() + initial_saldo
        
        # Dividends
        div_df_raw = activity[activity['Tipo'].str.contains('dividendo', na=False, case=False)].copy()
        if not div_df_raw.empty:
            div_df_raw['Date'] = pd.to_datetime(div_df_raw['Date'])
            div_daily = div_df_raw.groupby('Date')['Importe'].sum().reset_index()
            df_g = pd.merge(df_g, div_daily, on='Date', how='left')
            df_g['Importe'] = df_g['Importe'].fillna(0)
            df_g['Dividendos_Acumulados'] = df_g['Importe'].cumsum()
        else:
            df_g['Dividendos_Acumulados'] = 0.0
            
        df_g['Capital_Total'] = df_g['Net_Value']
        
        fig_stack = go.Figure()
        
        if chart_mode == "Valor Absoluto (USD)":
            y1 = df_g['Depositos_Acumulados']
            y2 = df_g['Depositos_Acumulados'] + df_g['Dividendos_Acumulados']
            y3 = df_g['Capital_Total']
            y_title = "Valor (USD)"
            tickfmt = "$.0f"
        else:
            # Safe divide by initial cap / cumulative deposits
            base = df_g['Depositos_Acumulados'].replace(0, 1) # Prevent div by 0
            y1 = (df_g['Depositos_Acumulados'] / base) * 100
            y2 = ((df_g['Depositos_Acumulados'] + df_g['Dividendos_Acumulados']) / base) * 100
            y3 = (df_g['Capital_Total'] / base) * 100
            y_title = "Crecimiento (%)"
            tickfmt = ".1f%"
            
        fig_stack.add_trace(go.Scatter(x=df_g['Date'], y=y1, mode='lines',
                                       name='Capital Aportado', line=dict(color='#888888', width=2, dash='dot')))
        fig_stack.add_trace(go.Scatter(x=df_g['Date'], y=y2, mode='lines',
                                       name='Capital + Dividendos', line=dict(color='#f1c40f', width=2)))
        fig_stack.add_trace(go.Scatter(x=df_g['Date'], y=y3, mode='lines',
                                       name='Portafolio Total (Con Ganancias)', line=dict(color='#00ff9d', width=3)))
        
        fig_stack.update_layout(template="plotly_dark", margin=dict(l=0, r=0, t=30, b=0), 
                                hovermode="x unified", yaxis_title=y_title, yaxis=dict(tickformat=tickfmt))
        st.plotly_chart(fig_stack, use_container_width=True)
        
        st.markdown("---")
        st.markdown("### Portafolio Actual en Tiempo Real (Yahoo Finance)")
        if not pos_summary_realtime.empty:
            st.dataframe(pos_summary_realtime.style.format({
                "Invertido ($)": "${:,.2f}",
                "Precio Actual ($)": "${:,.2f}",
                "Valor Neto ($)": "${:,.2f}",
                "G/P ($)": "${:,.2f}",
                "G/P (%)": "{:.2%}"
            }))
        else:
            st.info("No hay posiciones abiertas documentadas.")

    with tab3:
        st.subheader("Análisis de Riesgo y Series de Caídas (Drawdown)")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Peor Caída (Max Drawdown)", f"{risk_metrics['Max Drawdown']*100:.2f}%", delta_color="inverse", help="Mayor porcentaje histórico perdido desde el pico hasta el valle en la curva de capital.")
        with col2:
            st.metric("Ratio Sortino (Riesgo a la baja)", f"{risk_metrics['Sortino']:.2f}", help="Variante del Sharpe. Penaliza al portafolio únicamente por su volatilidad a la baja (pérdidas).")
        
        st.markdown("### 🎢 Evolución del Drawdown (Riesgo Histórico)")
        fig_dd = go.Figure()
        fig_dd.add_trace(go.Scatter(x=equity_curve['Date'], y=equity_curve['Drawdown'] * 100, mode='lines',
                                    name='Drawdown (%)', line=dict(color='#ff4b4b', width=1.5),
                                    fill='tozeroy', fillcolor='rgba(255, 75, 75, 0.2)'))
        fig_dd.update_layout(template="plotly_dark", yaxis_title="Drawdown (%)",
                             margin=dict(l=0, r=0, t=30, b=0), hovermode="x unified")
        st.plotly_chart(fig_dd, use_container_width=True)

    with tab4:
        st.subheader("🌱 Planificador: Interés Compuesto")
        st.markdown("Proyecta tu capital futuro basado en aportaciones recurrentes y el poder del interés compuesto.")
        
        col_inp, col_figs = st.columns([1, 2.5])
        
        with col_inp:
            st.markdown("##### Parámetros")
            
            # Valor default: ultimo valor de la cartera
            default_principal = equity_curve['Net_Value'].iloc[-1] if not equity_curve.empty else 10000.0
            c_principal = st.slider("Principal Inicial ($):", 0, 200000, int(default_principal), step=500, help="Tu capital de partida (se pre-carga con el tamaño actual de tu portafolio).")
            c_contrib = st.slider("Aportación Mensual ($):", 0, 5000, 200, step=50, help="Cuánto dinero nuevo inyectas al mes de forma constante.")
            c_rate = st.slider("Tasa de Crecimiento Anual:", 0.0, 0.25, 0.10, step=0.01, help="Rendimiento neto esperado del mercado (ej. S&P500 promedia ~10% anual).")
            c_div = st.slider("Tasa de Dividendo Anual:", 0.0, 0.10, 0.02, step=0.01, help="Porcentaje de tu portafolio que paga dividendos en efectivo / cash anualmente.")
            c_years = st.slider("Años a proyectar:", 1, 50, 20, step=1, help="Plazo temporal de la simulación hacia el futuro.")
            c_inf = st.slider("Tasa de Inflación Anual:", 0.0, 0.15, 0.03, step=0.01, help="Para ajustar qué tanto poder adquisitivo tendrá relamente tu dinero en el futuro (descuento del valor Real).")
            c_var = st.slider("Variación Tasa (Riesgo/Varianza):", 0.0, 0.15, 0.05, step=0.01, help="El porcentaje matemático de margen de error (Crea el abanico pesimista y optimista).")
            
            st.markdown("##### Estrategia")
            c_drip_opt = st.radio("Manejo de Dividendos:", ["Re-invertir (DRIP)", "Acumular Cash No-capitalizable"])
            drip_bool = True if "DRIP" in c_drip_opt else False
            
        with col_figs:
            from forecasting import compound_interest_simulator
            df_comp = compound_interest_simulator(c_principal, c_contrib, c_rate, c_div, c_years, c_inf, c_var)
            
            sub_tab_inv, sub_tab_var = st.tabs(["Gráfico de Inversión (Absoluto)", "Gráfico de Varianza (Crecimiento X Aportado)"])
            
            with sub_tab_inv:
                fig_inv = go.Figure()
                # Todos tienen la aportacion total base
                fig_inv.add_trace(go.Scatter(x=df_comp['Año'], y=df_comp['Contribucion_Total'], mode='lines',
                                             name='Capital Directo Depositado', line=dict(color='#888888', dash='dot')))
                                             
                if drip_bool:
                    fig_inv.add_trace(go.Scatter(x=df_comp['Año'], y=df_comp['DRIP_Total'], mode='lines',
                                                 name='Interés Compuesto Total', line=dict(color='#00ff9d', width=3)))
                    fig_inv.add_trace(go.Scatter(x=df_comp['Año'], y=df_comp['DRIP_Superior'], mode='lines',
                                                 name='Rango Superior (Optimista)', line=dict(color='rgba(0,255,157,0.5)', dash='dash')))
                    fig_inv.add_trace(go.Scatter(x=df_comp['Año'], y=df_comp['DRIP_Inferior'], mode='lines',
                                                 name='Rango Inferior (Pesimista)', line=dict(color='rgba(255,100,100,0.5)', dash='dash')))
                    fig_inv.add_trace(go.Scatter(x=df_comp['Año'], y=df_comp['DRIP_Ajustado_Inflacion'], mode='lines',
                                                 name='Poder Adquisitivo Real (Deflactado)', line=dict(color='#f1c40f', width=2)))
                else:
                    fig_inv.add_trace(go.Scatter(x=df_comp['Año'], y=df_comp['NoDRIP_Capital'], mode='lines',
                                                 name='Capital Base (Interés simple sobre div)', line=dict(color='#3498db', width=2)))
                    fig_inv.add_trace(go.Scatter(x=df_comp['Año'], y=df_comp['NoDRIP_Total'], mode='lines',
                                                 name='Capital Base + Dividendos Acumulados ($)', line=dict(color='#00ff9d', width=3)))
                                                 
                fig_inv.update_layout(template="plotly_dark", hovermode="x unified",
                                      xaxis_title="Años Proyectados", yaxis_title="Monto Acumulado ($)",
                                      margin=dict(l=0, r=0, t=20, b=0), yaxis=dict(tickformat="$.0f"))
                st.plotly_chart(fig_inv, use_container_width=True)
                
            with sub_tab_var:
                fig_var = go.Figure()
                if drip_bool:
                    fig_var.add_trace(go.Scatter(x=df_comp['Año'], y=df_comp['Factor_DRIP'], mode='lines',
                                                 name='Multiplicador Esperado (X veces)', line=dict(color='#00ff9d', width=3)))
                    fig_var.add_trace(go.Scatter(x=df_comp['Año'], y=df_comp['Factor_DRIP_Up'], mode='lines',
                                                 name='Límite Superior', line=dict(color='rgba(0,255,157,0.5)', dash='dash')))
                    fig_var.add_trace(go.Scatter(x=df_comp['Año'], y=df_comp['Factor_DRIP_Down'], mode='lines',
                                                 name='Límite Inferior', line=dict(color='rgba(255,100,100,0.5)', dash='dash')))
                else:
                    fig_var.add_trace(go.Scatter(x=df_comp['Año'], y=df_comp['Factor_NoDRIP'], mode='lines',
                                                 name='Multiplicador (No-DRIP)', line=dict(color='#00ff9d', width=3)))
                                                 
                fig_var.update_layout(template="plotly_dark", hovermode="x unified",
                                      xaxis_title="Años Proyectados", yaxis_title="Factor (Monto Final / Total Depositado)",
                                      margin=dict(l=0, r=0, t=20, b=0))
                st.plotly_chart(fig_var, use_container_width=True)


    with tab5:
        st.subheader("🔮 Proyecciones a Futuro y Simulaciones Monte Carlo")
        
        st.markdown("La Simulación Monte Carlo crea miles de posibles caminos futuros basados en la volatilidad y los retornos históricos. **(Esto toma un par de segundos)**")
        
        mc_years = st.slider("Años a simular:", 1, 50, 3)
        mc_days = mc_years * 252 # dias trading
        
        if st.button("🚀 Ejecutar 10,000 Simulaciones Monte Carlo"):
            with st.spinner("Procesando 10,000 universos paralelos..."):
                initial_price = equity_curve['Net_Value'].iloc[-1]
                # Solo visualizamos un subgrupo para no crashear plotly
                paths = monte_carlo_simulation(equity_curve, days_to_simulate=mc_days, simulations=10000)
                
                if paths.size > 0:
                    percentiles_df = get_monte_carlo_percentiles(paths, initial_price, days_to_simulate=mc_days)
                    
                    fig_mc = go.Figure()
                    # P90
                    fig_mc.add_trace(go.Scatter(x=percentiles_df['Day'], y=percentiles_df['P90 (Optimista)'],
                                                mode='lines', name='Optimista (P90)', line=dict(color='rgba(0,255,157, 0.8)', dash='dash')))
                    # P50
                    fig_mc.add_trace(go.Scatter(x=percentiles_df['Day'], y=percentiles_df['P50 (Esperado)'],
                                                mode='lines', name='Esperado (P50)', line=dict(color='#00ff9d', width=3)))
                    # P10
                    fig_mc.add_trace(go.Scatter(x=percentiles_df['Day'], y=percentiles_df['P10 (Pésimista)'],
                                                mode='lines', name='Pesimista (P10)', line=dict(color='rgba(255,75,75,0.8)', dash='dash'),
                                                fill='tonexty', fillcolor='rgba(0,255,157,0.1)'))
                    
                    fig_mc.update_layout(template="plotly_dark", title=f"Proyección a {mc_years} año(s)",
                                         xaxis_title="Días de Trading", yaxis_title="Equidad Proyectada (USD)")
                    st.plotly_chart(fig_mc, use_container_width=True)
                    
                    # Holt Winters trend
                    hw_trend = trend_forecasting(equity_curve, periods=mc_days)
                    if not hw_trend.empty:
                        st.markdown("### 📈 Suavizado Exponencial (Holt-Winters Trend)")
                        fig_hw = go.Figure()
                        # Historico
                        fig_hw.add_trace(go.Scatter(x=equity_curve['Date'], y=equity_curve['Net_Value'],
                                                    name="Histórico", line=dict(color="gray")))
                        # Prediccion
                        fig_hw.add_trace(go.Scatter(x=hw_trend['Date'], y=hw_trend['Forecast'],
                                                    name="Tendencia Proyectada", line=dict(color="#00ff9d", width=3)))
                        fig_hw.update_layout(template="plotly_dark")
                        st.plotly_chart(fig_hw, use_container_width=True)
                else:
                     st.error("No hay suficientes datos históricos para simular.")

    with tab6:
        st.header("📚 Rendimiento de Operaciones Cerradas")
        closed_pos = data_dict.get('closed_positions', pd.DataFrame())
        if not closed_pos.empty:
            # Intentar localizar columnas genéricas de PnL y Activo
            pnl_col = [c for c in closed_pos.columns if 'Beneficio' in c or 'Profit' in c or 'Ganancia' in c]
            if pnl_col:
                col_pnl = pnl_col[0]
                # Convertimos a numerico
                closed_pos[col_pnl] = pd.to_numeric(closed_pos[col_pnl], errors='coerce').fillna(0)
                total_profit = closed_pos[closed_pos[col_pnl] > 0][col_pnl].sum()
                total_loss = closed_pos[closed_pos[col_pnl] < 0][col_pnl].sum()
                net_pnl = total_profit + total_loss
                
                c1, c2, c3 = st.columns(3)
                c1.metric("💸 Ganancias Brutas", f"${total_profit:,.2f}")
                c2.metric("🩸 Pérdidas Brutas", f"${total_loss:,.2f}")
                c3.metric("⚖️ PnL Neto Cerrado", f"${net_pnl:,.2f}", delta=f"${net_pnl:,.2f}")
                
                st.markdown("---")
                col_rank1, col_rank2 = st.columns(2)
                with col_rank1:
                    st.markdown("#### 🏆 Top 5 Mejores Operaciones")
                    best_5 = closed_pos.nlargest(5, col_pnl)[['Acción', col_pnl]]
                    st.dataframe(best_5.style.format({col_pnl: "${:,.2f}"}).applymap(lambda x: "color: #00ff9d;", subset=[col_pnl]), use_container_width=True)
                with col_rank2:
                    st.markdown("#### 💀 Top 5 Peores Operaciones")
                    worst_5 = closed_pos.nsmallest(5, col_pnl)[['Acción', col_pnl]]
                    st.dataframe(worst_5.style.format({col_pnl: "${:,.2f}"}).applymap(lambda x: "color: #ff4b4b;", subset=[col_pnl]), use_container_width=True)
                
                st.markdown("#### Histórico de Operaciones Individuales")
                st.dataframe(closed_pos.style.applymap(lambda x: "color: #00ff9d;" if isinstance(x, (int, float)) and x > 0 else ("color: #ff4b4b;" if isinstance(x, (int, float)) and x < 0 else ""), subset=[col_pnl]), use_container_width=True)
            else:
                st.dataframe(closed_pos)
        else:
            st.info("No se completó la carga de Posiciones Cerradas.")

# ==========================
# CHATBOT GOOGLE GEMINI (OPCIONAL - SOLO SI TOGGLE ACTIVADO)
# ==========================
if show_ai:
    with ai_col:
        st.markdown("### 🧠 Copiloto IA (Gemini)")
        from dotenv import load_dotenv
        import os
        import yfinance as yf

        load_dotenv()
        GEMINI_KEY = os.getenv("GEMINI_API_KEY")
        
        if GEMINI_KEY:
            c1, c2 = st.columns([0.8, 0.2])
            if c2.button("🧹", help="Limpiar Memoria", key="clear_chat_ai"):
                st.session_state.messages = []
                st.rerun()
            st.markdown("Consulta métricas o evalúa activos en tiempo real.")
            
            try:
                import google.generativeai as genai
                genai.configure(api_key=GEMINI_KEY)
            except ImportError:
                st.warning("Librería de Google AI no instalada. Revisa requirements.txt.")
                st.stop()
        
        if "messages" not in st.session_state:
            st.session_state.messages = []
            
        # Contenedor con altura fija para que el chat use la pantalla y el input quede fijo abajo
        chat_placeholder = st.container(height=650)
        
        for message in st.session_state.messages:
            role = "user" if message["role"] == "user" else "assistant"
            with chat_placeholder.chat_message(role):
                st.markdown(message["parts"][0])
                
        def get_portfolio_context():
            try:
                context = f"Fecha Actual del Sistema: {datetime.now().strftime('%d de %B de %Y')}\n"
                context += "Contexto del Portafolio Actual:\n"
                if 'Net_Value' in equity_curve.columns:
                    context += f"Valor Total Actual: ${equity_curve['Net_Value'].iloc[-1]:.2f}\n"
                if 'Total Return' in perf_metrics:
                    context += f"Total Return (Nominal): {perf_metrics['Total Return']*100:.2f}%\n"
                if 'TWRR' in perf_metrics:
                    context += f"TWRR (Flujos Ajustados): {perf_metrics['TWRR']*100:.2f}%\n"
                if 'Volatility' in risk_metrics:
                    context += f"Volatilidad Anual: {risk_metrics['Volatility']*100:.2f}%\n"
                if 'Max Drawdown' in risk_metrics:
                    context += f"Peor Caída (Drawdown): {risk_metrics['Max Drawdown']*100:.2f}%\n"
                if 'Sortino' in risk_metrics:
                    context += f"Sortino Ratio: {risk_metrics['Sortino']:.2f}\n"
                if 'pe_ratio' in globals() and pd.notnull(pe_ratio):
                    context += f"P/E Ponderado del Portafolio: {pe_ratio:.2f}\n"
                if not pos_summary_realtime.empty:
                    context += "Top Activos Abiertos (Sincronizando Precios Yahoo Finance...):\n"
                    for _, r in pos_summary_realtime.head(5).iterrows():
                        ticker = r['Activo']
                        try:
                            # Inyección de precio real para evitar alucinaciones
                            curr_price = yf.Ticker(ticker).history(period="1d")['Close'].iloc[-1]
                            price_info = f"Precio Real Yahoo Finance: ${curr_price:.2f}"
                        except:
                            price_info = "Precio Real: No disponible en este momento"
                        context += f"- {ticker}: {r['Valor Neto ($)']} USD ({price_info}, G/P: {r['G/P (%)']:+.2%})\n"
                
                # Integrar top closed positions si data_dict lo posee:
                if 'closed_positions' in data_dict:
                    closed_df = data_dict['closed_positions']
                    if not closed_df.empty:
                        pnl_cols = [c for c in closed_df.columns if 'Beneficio' in c or 'Profit' in c or 'Ganancia' in c]
                        if pnl_cols:
                            c_pnl = pnl_cols[0]
                            closed_df[c_pnl] = pd.to_numeric(closed_df[c_pnl], errors='coerce').fillna(0)
                            
                            tot_profit = closed_df[closed_df[c_pnl] > 0][c_pnl].sum()
                            tot_loss = closed_df[closed_df[c_pnl] < 0][c_pnl].sum()
                            net_pnl = tot_profit + tot_loss

                            context += f"PnL Neto Cerrado (Total Histórico): ${net_pnl:.2f}\n"
                            context += f"Ganancias Brutas Cerradas: ${tot_profit:.2f}\n"
                            context += f"Pérdidas Brutas Cerradas: ${tot_loss:.2f}\n"
                            
                            best_5 = closed_df.nlargest(5, c_pnl)
                            context += "Top 5 Mejores Operaciones Cerradas Históricamente:\n"
                            for _, r in best_5.iterrows():
                                context += f"- {r.get('Acción', 'Activo')}: +${r[c_pnl]:.2f}\n"
                                
                            worst_5 = closed_df.nsmallest(5, c_pnl)
                            context += "Top 5 Peores Operaciones Cerradas Históricamente (Pérdidas):\n"
                            for _, r in worst_5.iterrows():
                                context += f"- {r.get('Acción', 'Activo')}: -${abs(r[c_pnl]):.2f}\n"
                                
                return context
            except:
                return "Datos de portafolio no definidos todavía."

        if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
            with chat_placeholder.chat_message("assistant"):
                sys_inst = f"Eres un analista de portafolio avanzado. Hoy es {datetime.now().strftime('%d de %B de %Y')}. NO ALUCINES PRECIOS, usa exactamente los que te proporciono. Su radiografía es:\n" + get_portfolio_context()
                try:
                    import google.generativeai as genai
                    try:
                        model = genai.GenerativeModel("gemini-3.1-flash-lite-preview", system_instruction=sys_inst)
                    except:
                        model = genai.GenerativeModel("gemini-3-flash-preview", system_instruction=sys_inst)
                    
                    history = []
                    for m in st.session_state.messages[:-1]:
                        g_role = "user" if m["role"] == "user" else "model"
                        history.append({"role": g_role, "parts": m["parts"]})
                        
                    chat = model.start_chat(history=history)
                    with st.spinner("Analizando..."):
                        response = chat.send_message(st.session_state.messages[-1]["parts"][0])
                        st.markdown(response.text)
                    
                    st.session_state.messages.append({"role": "model", "parts": [response.text]})
                except Exception as e:
                    st.error(f"Error AI: {e}")

        # Input siempre debe estar renderizado de último para evitar salto gráfico
        if prompt := st.chat_input("Escribe tu pregunta aquí..."):
            st.session_state.messages.append({"role": "user", "parts": [prompt]})
            st.rerun()
