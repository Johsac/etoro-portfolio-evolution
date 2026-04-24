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

# Page Configuration
st.set_page_config(
    page_title="eToro Portfolio Evolution",
    layout="wide",
    page_icon="📈",
    initial_sidebar_state="expanded"
)

# Premium Style (Glassmorphism & Neon)
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
    with st.expander("📂 Data Upload", expanded=True):
        st.markdown("Upload your eToro account statement file.")
        uploaded_file = st.file_uploader("Upload Excel (.xlsx)", type=['xlsx'])
        
        if uploaded_file is None:
            # Empty state
            st.title(" eToro Portfolio Evolution")
            st.info("👈 Upload your eToro 'Account Statement' (Exported to Excel) to start the analysis.")
            st.stop()

        # --- Process File ---
        with st.spinner("Processing data..."):
            try:
                data_dict = load_etoro_data(uploaded_file)
                activity = data_dict['activity']
                closed_pos = data_dict['closed_positions']
                dividends = data_dict['dividends']
                st.success("Data loaded successfully!")
            except Exception as e:
                st.error(f"Error parsing file: {e}")
                st.stop()
    
    st.markdown("<br><br><br>", unsafe_allow_html=True) # Spacer
    st.markdown("---")
    # AI Toggle Premium Styling
    st.markdown("""
        <style>
        /* 1. GLOBAL RESET */
        [data-testid="stSidebar"] label p {
            font-size: 1rem !important;
            font-weight: normal !important;
            color: white !important;
        }

        /* 2. EXCLUSIVE ANCHOR STYLE */
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
    
    show_ai = st.toggle("Ask the AI Copilot", value=False, key="toggle_ia_pro")

# --- Benchmark Mapping ---
BENCHMARKS = {
    'S&P 500': '^GSPC',
    'NASDAQ 100': '^NDX',
    'MSCI World': 'URTH'
}

# --- Dynamic Main Layout ---
if show_ai:
    main_col, ai_col = st.columns([0.7, 0.3])
else:
    main_col = st.container()

with main_col:
    st.title(" eToro Portfolio Evolution")
    st.markdown("Advanced Forensic Analysis Platform for your eToro Wealth.")
    
    # --- Base Computations ---
    with st.spinner("Fetching historical prices from Yahoo Finance & Processing Splits..."):
        try:
            equity_curve, pos_summary_realtime = reconstruct_portfolio(activity)
            perf_metrics = calculate_performance_metrics(equity_curve, activity)
            risk_metrics = calculate_risk_metrics(equity_curve)
        except Exception as e:
            st.error(f"yfinance error: {e}")
            st.stop()

    if equity_curve.empty:
        st.warning("Could not reconstruct a valid Equity Curve. Please check data formatting.")
        st.stop()

    # --- Tabs Layout ---
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "📊 Account Summary", 
            "🧮 Asset Breakdown",
            "📉 Risk & Drawdown", 
            "🌱 Compound Interest Sim",
            "🔮 Monte Carlo Predictions",
            "📚 Trade History"
        ])

    with tab1:
        st.subheader("⚡ Historical Performance Metrics")
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Total Return (Nominal)", f"{perf_metrics['Total Return']*100:.2f}%", help="Measures the total gross profit of the portfolio.")
        with col2:
            st.metric("TWRR (Flow Adjusted)", f"{perf_metrics['TWRR']*100:.2f}%", help="Time-Weighted Return: Real performance isolating the effect of deposits/withdrawals.")
        with col3:
            st.metric("Annualized Volatility", f"{risk_metrics['Volatility']*100:.2f}%", help="Annual standard deviation; measures historical price swings.")
        with col4:
            st.metric("Sharpe Ratio", f"{risk_metrics['Sharpe']:.2f}", help="Risk-adjusted return. >1.0 is acceptable, >2.0 is excellent.")
        with col5:
            from financial_metrics import get_portfolio_pe
            pe_ratio = get_portfolio_pe(pos_summary_realtime)
            if pd.notnull(pe_ratio):
                st.metric("📊 Portfolio P/E", f"{pe_ratio:.1f}x", help="Average Price-to-Earnings Ratio for the active stock portfolio.")
            else:
                st.metric("📊 Portfolio P/E", "N/A", help="Average Price-to-Earnings Ratio for the active stock portfolio.")

        # Nominal View (Equity Curve)
        st.markdown("### 📊 Absolute Net Value Evolution ($)")
        fig_abs = go.Figure()
        fig_abs.add_trace(go.Scatter(x=equity_curve['Date'], y=equity_curve['Net_Value'], mode='lines', 
                                    name='Portfolio Value ($)', line=dict(color='#00ff9d', width=2),
                                    fill='tozeroy', fillcolor='rgba(0, 255, 157, 0.1)'))
        fig_abs.update_layout(template="plotly_dark", margin=dict(l=0, r=0, t=30, b=0),
                             hovermode="x unified", xaxis_title="", yaxis_title="Net Equity ($)")
        st.plotly_chart(fig_abs, use_container_width=True)

        # Benchmarks & Timeframes
        st.markdown("### 📈 Normalized Performance vs Benchmarks (Base 100%)")
        
        col_bench, col_time = st.columns([1, 2])
        with col_bench:
             bench_sel = st.selectbox("Compare with Benchmark", ['None'] + list(BENCHMARKS.keys()) + ['Custom'])
             custom_bench = ""
             if bench_sel == 'Custom':
                 custom_bench = st.text_input("Enter Yahoo Finance Ticker (e.g., URTH, ARKK):")
                 
        with col_time:
             st.write("Time Filter:")
             timeframe = st.radio("Window:", ["Max", "5Y", "1Y", "YTD", "6M", "3M"], horizontal=True, label_visibility="collapsed")
        
        # Time Filter Logic
        df_plot = equity_curve.copy()
        end_date = df_plot['Date'].max()
        if timeframe == '5Y': start_date = end_date - pd.DateOffset(years=5)
        elif timeframe == '1Y': start_date = end_date - pd.DateOffset(years=1)
        elif timeframe == 'YTD': start_date = pd.to_datetime(f"{end_date.year}-01-01")
        elif timeframe == '6M': start_date = end_date - pd.DateOffset(months=6)
        elif timeframe == '3M': start_date = end_date - pd.DateOffset(months=3)
        else: start_date = df_plot['Date'].min()
        
        df_plot = df_plot[df_plot['Date'] >= start_date].copy()
        
        # Normalize Return (Base 0 at start_date)
        if 'Daily_TWRR' in df_plot.columns:
             df_plot['TWRR_Period'] = (1 + df_plot['Daily_TWRR']).cumprod() - 1
        else:
             initial_val = df_plot['Net_Value'].iloc[0]
             df_plot['TWRR_Period'] = (df_plot['Net_Value'] / initial_val) - 1 if initial_val != 0 else 0
        
        fig_eq = go.Figure()
        fig_eq.add_trace(go.Scatter(x=df_plot['Date'], y=df_plot['TWRR_Period'], mode='lines', 
                                    name='Portfolio (TWRR)', line=dict(color='#00ff9d', width=3),
                                    fill='tozeroy', fillcolor='rgba(0, 255, 157, 0.1)'))
        
        # Add Benchmark
        if bench_sel != 'None':
            bench_ticker = custom_bench if bench_sel == 'Custom' else BENCHMARKS[bench_sel]
            if bench_ticker:
                import yfinance as yf
                try:
                    b_data = yf.download(bench_ticker.upper(), start=start_date, end=end_date+pd.Timedelta(days=1), progress=False)['Close']
                    if isinstance(b_data, pd.DataFrame) and not b_data.empty: 
                         b_data = b_data[bench_ticker.upper()] if bench_ticker.upper() in b_data.columns else b_data.iloc[:, 0]
                    b_data = b_data.reindex(df_plot['Date']).ffill().bfill()
                    b_ret = b_data.pct_change().fillna(0)
                    b_ret.iloc[0] = 0
                    b_cum = (1 + b_ret).cumprod() - 1
                    fig_eq.add_trace(go.Scatter(x=df_plot['Date'], y=b_cum, mode='lines', 
                                                name=bench_ticker.upper(), line=dict(color='#ff9900', width=2, dash='dash')))
                except Exception as e:
                    pass

        fig_eq.update_layout(template="plotly_dark", margin=dict(l=0, r=0, t=30, b=0),
                             hovermode="x unified", xaxis_title="", yaxis_title="Cumulative Return (%)",
                             yaxis_tickformat='.1%')
        st.plotly_chart(fig_eq, use_container_width=True)
        
        # Monthly Returns Heatmap
        st.markdown("### 📅 Monthly Returns Heatmap")
        monthly_ret = get_monthly_returns(equity_curve)
        if not monthly_ret.empty:
            fig_heat = px.imshow(monthly_ret * 100, text_auto=".1f", color_continuous_scale="RdYlGn",
                                 color_continuous_midpoint=0,
                                 labels=dict(x="Month", y="Year", color="Return (%)"),
                                 template="plotly_dark")
            fig_heat.update_xaxes(side="top")
            st.plotly_chart(fig_heat, use_container_width=True)
            
        # PASSIVE INCOME SECTION
        st.markdown("### 💸 Passive Income (eToro Dividends)")
        div_df = activity[activity['Tipo'].str.contains('dividendo', na=False, case=False)].copy()
        if not div_df.empty:
             col_div_op, _ = st.columns([1, 2])
             with col_div_op:
                 div_group = st.radio("Frequency:", ["Monthly", "Quarterly", "Annual"], horizontal=True)
                 
             freq_map = {"Monthly": "M", "Quarterly": "Q", "Annual": "Y"}
             freq = freq_map[div_group]
             
             div_df['Date'] = pd.to_datetime(div_df['Date'])
             div_df['Importe'] = pd.to_numeric(div_df['Importe'], errors='coerce').fillna(0)
             
             div_grouped = div_df.groupby(div_df['Date'].dt.to_period(freq))['Importe'].sum().reset_index()
             div_grouped['Date'] = div_grouped['Date'].dt.to_timestamp()
             
             fig_div = go.Figure()
             x_format = "%b %Y" if freq == "M" else ("%Y-Q%q" if freq == "Q" else "%Y")
             
             fig_div.add_trace(go.Bar(x=div_grouped['Date'], y=div_grouped['Importe'], 
                                    marker_color='#f1c40f', name='Dividends',
                                    text=div_grouped['Importe'].apply(lambda x: f"${x:.1f}"),
                                    textposition='auto'))
             fig_div.update_layout(template="plotly_dark", margin=dict(l=0, r=0, t=30, b=0),
                                  xaxis_title="", yaxis_title="Income ($)",
                                  xaxis=dict(tickformat=x_format))
             st.plotly_chart(fig_div, use_container_width=True)
             
             st.caption(f"**Total Historical Dividends:** ${div_df['Importe'].sum():.2f} USD generated passively.")


    with tab2:
        st.header("🧮 Strategic Portfolio Breakdown")
        st.markdown("#### 🥧 Asset Allocation")
        
        groupby_opt = st.radio("Group by:", ["Individual Asset", "Category (Stock, ETF, etc.)"], horizontal=True)
        
        if not pos_summary_realtime.empty:
            df_pie = pos_summary_realtime[pos_summary_realtime['Net Value ($)'] > 1].copy()
            
            if groupby_opt == "Category (Stock, ETF, etc.)":
                from portfolio_reconstructor import TICKER_MAPPING
                temp_act = activity[['Detalles', 'Tipo de activo']].dropna()
                temp_act['Ticker_Clean'] = temp_act['Detalles'].apply(lambda x: TICKER_MAPPING.get(str(x).split('/')[0].strip().upper(), str(x).split('/')[0].strip().upper()))
                
                category_map = temp_act.drop_duplicates('Ticker_Clean').set_index('Ticker_Clean')['Tipo de activo'].to_dict()
                df_pie['Category'] = df_pie['Asset'].map(category_map).fillna('Unknown')
                df_pie = df_pie.groupby('Category')['Net Value ($)'].sum().reset_index()
                fig_pie = px.pie(df_pie, values='Net Value ($)', names='Category', 
                                 hole=0.4, color_discrete_sequence=px.colors.sequential.Teal)
            else:
                fig_pie = px.pie(df_pie, values='Net Value ($)', names='Asset', 
                                 hole=0.4, color_discrete_sequence=px.colors.sequential.Teal)
                
            fig_pie.update_layout(template="plotly_dark", margin=dict(t=30, b=0, l=0, r=0))
            st.plotly_chart(fig_pie, use_container_width=True)
            
        st.markdown("---")
        st.markdown("#### 🧊 Portfolio Wealth Composition")
        chart_mode = st.radio("Metric:", ["Absolute Value (USD)", "Normalized Percentage (%)"], horizontal=True)
        
        df_g = equity_curve.copy()
        initial_saldo = max(0, df_g['Net_Value'].iloc[0] - df_g['Net_Flow'].iloc[0]) if not df_g.empty else 0
        df_g['Cum_Deposits'] = df_g['Net_Flow'].cumsum() + initial_saldo
        
        div_df_raw = activity[activity['Tipo'].str.contains('dividendo', na=False, case=False)].copy()
        if not div_df_raw.empty:
            div_df_raw['Date'] = pd.to_datetime(div_df_raw['Date'])
            div_daily = div_df_raw.groupby('Date')['Importe'].sum().reset_index()
            df_g = pd.merge(df_g, div_daily, on='Date', how='left')
            df_g['Importe'] = df_g['Importe'].fillna(0)
            df_g['Cum_Dividends'] = df_g['Importe'].cumsum()
        else:
            df_g['Cum_Dividends'] = 0.0
            
        df_g['Total_Capital'] = df_g['Net_Value']
        
        fig_stack = go.Figure()
        
        if chart_mode == "Absolute Value (USD)":
            y1 = df_g['Cum_Deposits']
            y2 = df_g['Cum_Deposits'] + df_g['Cum_Dividends']
            y3 = df_g['Total_Capital']
            y_title = "Value (USD)"
            tickfmt = "$.0f"
        else:
            base = df_g['Cum_Deposits'].replace(0, 1)
            y1 = (df_g['Cum_Deposits'] / base) * 100
            y2 = ((df_g['Cum_Deposits'] + df_g['Cum_Dividends']) / base) * 100
            y3 = (df_g['Total_Capital'] / base) * 100
            y_title = "Growth (%)"
            tickfmt = ".1f%"
            
        fig_stack.add_trace(go.Scatter(x=df_g['Date'], y=y1, mode='lines',
                                       name='Net Capital Invested', line=dict(color='#888888', width=2, dash='dot')))
        fig_stack.add_trace(go.Scatter(x=df_g['Date'], y=y2, mode='lines',
                                       name='Capital + Dividends', line=dict(color='#f1c40f', width=2)))
        fig_stack.add_trace(go.Scatter(x=df_g['Date'], y=y3, mode='lines',
                                       name='Total Portfolio Value', line=dict(color='#00ff9d', width=3)))
        
        fig_stack.update_layout(template="plotly_dark", margin=dict(l=0, r=0, t=30, b=0), 
                                hovermode="x unified", yaxis_title=y_title, yaxis=dict(tickformat=tickfmt))
        st.plotly_chart(fig_stack, use_container_width=True)
        
        st.markdown("---")
        st.markdown("### Real-time Holdings (Yahoo Finance Sourced)")
        if not pos_summary_realtime.empty:
            st.dataframe(pos_summary_realtime.rename(columns={
                "Asset": "Ticker"
            }).style.format({
                "Invested ($)": "${:,.2f}",
                "Current Price ($)": "${:,.2f}",
                "Net Value ($)": "${:,.2f}",
                "PnL ($)": "${:,.2f}",
                "PnL (%)": "{:.2%}"
            }))

    with tab3:
        st.subheader("Risk Analysis & Drawdown Series")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Max Drawdown", f"{risk_metrics['Max Drawdown']*100:.2f}%", delta_color="inverse", help="Deepest historical drop from peak to trough in the equity curve.")
        with col2:
            st.metric("Sortino Ratio", f"{risk_metrics['Sortino']:.2f}", help="Sharpe variant that only penalizes downward volatility (losses).")
        
        st.markdown("### 🎢 Historical Drawdown Timeline (%)")
        fig_dd = go.Figure()
        fig_dd.add_trace(go.Scatter(x=equity_curve['Date'], y=equity_curve['Drawdown'] * 100, mode='lines',
                                    name='Drawdown (%)', line=dict(color='#ff4b4b', width=1.5),
                                    fill='tozeroy', fillcolor='rgba(255, 75, 75, 0.2)'))
        fig_dd.update_layout(template="plotly_dark", yaxis_title="Drawdown (%)",
                             margin=dict(l=0, r=0, t=30, b=0), hovermode="x unified")
        st.plotly_chart(fig_dd, use_container_width=True)

    with tab4:
        st.subheader("🌱 Strategic Compound Interest Planner")
        st.markdown("Project your future capital based on recurring contributions and compound growth.")
        
        col_inp, col_figs = st.columns([1, 2.5])
        
        with col_inp:
            st.markdown("##### Simulation Parameters")
            default_principal = equity_curve['Net_Value'].iloc[-1] if not equity_curve.empty else 10000.0
            c_principal = st.slider("Initial Principal ($):", 0, 200000, int(default_principal), step=500)
            c_contrib = st.slider("Monthly Contribution ($):", 0, 5000, 200, step=50)
            c_rate = st.slider("Expected Annual Growth:", 0.0, 0.25, 0.10, step=0.01)
            c_div = st.slider("Est. Dividend Yield:", 0.0, 0.10, 0.02, step=0.01)
            c_years = st.slider("Years to Project:", 1, 50, 20, step=1)
            c_inf = st.slider("Expected Inflation Rate:", 0.0, 0.15, 0.03, step=0.01)
            c_var = st.slider("Variance (Volatility Risk):", 0.0, 0.15, 0.05, step=0.01)
            
            st.markdown("##### Strategy")
            c_drip_opt = st.radio("Dividend Management:", ["Re-invest (DRIP)", "Accumulate Cash"])
            drip_bool = True if "DRIP" in c_drip_opt else False
            
        with col_figs:
            from forecasting import compound_interest_simulator
            df_comp = compound_interest_simulator(c_principal, c_contrib, c_rate, c_div, c_years, c_inf, c_var)
            
            sub_tab_inv, sub_tab_var = st.tabs(["Accumulation Chart", "Multiplier Factor"])
            
            with sub_tab_inv:
                fig_inv = go.Figure()
                fig_inv.add_trace(go.Scatter(x=df_comp['Año'], y=df_comp['Contribucion_Total'], mode='lines',
                                             name='Direct Capital Invested', line=dict(color='#888888', dash='dot')))
                                             
                if drip_bool:
                    fig_inv.add_trace(go.Scatter(x=df_comp['Año'], y=df_comp['DRIP_Total'], mode='lines',
                                                 name='Total Compound Growth', line=dict(color='#00ff9d', width=3)))
                    fig_inv.add_trace(go.Scatter(x=df_comp['Año'], y=df_comp['DRIP_Superior'], mode='lines',
                                                 name='Upper Bound (Bullish)', line=dict(color='rgba(0,255,157,0.5)', dash='dash')))
                    fig_inv.add_trace(go.Scatter(x=df_comp['Año'], y=df_comp['DRIP_Inferior'], mode='lines',
                                                 name='Lower Bound (Bearish)', line=dict(color='rgba(255,100,100,0.5)', dash='dash')))
                    fig_inv.add_trace(go.Scatter(x=df_comp['Año'], y=df_comp['DRIP_Ajustado_Inflacion'], mode='lines',
                                                 name='Real Purchasing Power (Adjusted)', line=dict(color='#f1c40f', width=2)))
                else:
                    fig_inv.add_trace(go.Scatter(x=df_comp['Año'], y=df_comp['NoDRIP_Capital'], mode='lines',
                                                 name='Base Capital (Simple Interest)', line=dict(color='#3498db', width=2)))
                    fig_inv.add_trace(go.Scatter(x=df_comp['Año'], y=df_comp['NoDRIP_Total'], mode='lines',
                                                 name='Base + Accum. Dividends ($)', line=dict(color='#00ff9d', width=3)))
                                                 
                fig_inv.update_layout(template="plotly_dark", hovermode="x unified",
                                      xaxis_title="Simulation Years", yaxis_title="Total Value ($)",
                                      margin=dict(l=0, r=0, t=20, b=0), yaxis=dict(tickformat="$.0f"))
                st.plotly_chart(fig_inv, use_container_width=True)
                
            with sub_tab_var:
                fig_var = go.Figure()
                y_col = 'Factor_DRIP' if drip_bool else 'Factor_NoDRIP'
                fig_var.add_trace(go.Scatter(x=df_comp['Año'], y=df_comp[y_col], mode='lines',
                                             name='Expected Multiplier', line=dict(color='#00ff9d', width=3)))
                                                 
                fig_var.update_layout(template="plotly_dark", hovermode="x unified",
                                      xaxis_title="Projection Years", yaxis_title="Total Multiplier (Final / Invested)",
                                      margin=dict(l=0, r=0, t=20, b=0))
                st.plotly_chart(fig_var, use_container_width=True)


    with tab5:
        st.subheader("🔮 Probability Projections: Monte Carlo")
        st.markdown("Monte Carlo simulations generate 10,000 potential future paths based on historical volatility.")
        
        mc_years = st.slider("Simulate years forward:", 1, 50, 3)
        mc_days = mc_years * 252 
        
        if st.button("🚀 Run 10,000 Monte Carlo Simulations"):
            with st.spinner("Processing 10,000 parallel universes..."):
                initial_price = equity_curve['Net_Value'].iloc[-1]
                paths = monte_carlo_simulation(equity_curve, days_to_simulate=mc_days, simulations=10000)
                
                if paths.size > 0:
                    percentiles_df = get_monte_carlo_percentiles(paths, initial_price, days_to_simulate=mc_days)
                    
                    fig_mc = go.Figure()
                    # Bullish (P90)
                    fig_mc.add_trace(go.Scatter(x=percentiles_df['Day'], y=percentiles_df['P90 (Bullish)'],
                                                mode='lines', name='Bullish (P90)', line=dict(color='rgba(0,255,157, 0.8)', dash='dash')))
                    # Expected (P50)
                    fig_mc.add_trace(go.Scatter(x=percentiles_df['Day'], y=percentiles_df['P50 (Expected)'],
                                                mode='lines', name='Expected (P50)', line=dict(color='#00ff9d', width=3)))
                    # Bearish (P10)
                    fig_mc.add_trace(go.Scatter(x=percentiles_df['Day'], y=percentiles_df['P10 (Bearish)'],
                                                mode='lines', name='Bearish (P10)', line=dict(color='rgba(255,75,75,0.8)', dash='dash'),
                                                fill='tonexty', fillcolor='rgba(0,255,157,0.1)'))
                    
                    fig_mc.update_layout(template="plotly_dark", title=f"Projection for {mc_years} Year(s)",
                                         xaxis_title="Trading Days", yaxis_title="Projected Equity ($)")
                    st.plotly_chart(fig_mc, use_container_width=True)
                    
                    hw_trend = trend_forecasting(equity_curve, periods=mc_days)
                    if not hw_trend.empty:
                        st.markdown("### 📈 Exponential Smoothing (Holt-Winters Trend)")
                        fig_hw = go.Figure()
                        fig_hw.add_trace(go.Scatter(x=equity_curve['Date'], y=equity_curve['Net_Value'],
                                                    name="Historical", line=dict(color="gray")))
                        fig_hw.add_trace(go.Scatter(x=hw_trend['Date'], y=hw_trend['Forecast'],
                                                    name="Trend Forecast", line=dict(color="#00ff9d", width=3)))
                        fig_hw.update_layout(template="plotly_dark")
                        st.plotly_chart(fig_hw, use_container_width=True)

    with tab6:
        st.header("📚 Historical Trade Performance")
        closed_pos = data_dict.get('closed_positions', pd.DataFrame())
        if not closed_pos.empty:
            pnl_col = [c for c in closed_pos.columns if 'Beneficio' in c or 'Profit' in c or 'Ganancia' in c]
            if pnl_col:
                col_pnl = pnl_col[0]
                closed_pos[col_pnl] = pd.to_numeric(closed_pos[col_pnl], errors='coerce').fillna(0)
                total_profit = closed_pos[closed_pos[col_pnl] > 0][col_pnl].sum()
                total_loss = closed_pos[closed_pos[col_pnl] < 0][col_pnl].sum()
                net_pnl = total_profit + total_loss
                
                c1, c2, c3 = st.columns(3)
                c1.metric("💸 Gross Profits", f"${total_profit:,.2f}")
                c2.metric("🩸 Gross Losses", f"${total_loss:,.2f}")
                c3.metric("⚖️ Net Realized PnL", f"${net_pnl:,.2f}", delta=f"${net_pnl:,.2f}")
                
                st.markdown("---")
                col_rank1, col_rank2 = st.columns(2)
                with col_rank1:
                    st.markdown("#### 🏆 Top 5 Winners")
                    asset_col = 'Action' if 'Action' in closed_pos.columns else ('Asset' if 'Asset' in closed_pos.columns else 'Acción')
                    best_5 = closed_pos.nlargest(5, col_pnl)[[asset_col, col_pnl]]
                    st.dataframe(best_5.rename(columns={asset_col: 'Asset'}).style.format({col_pnl: "${:,.2f}"}).applymap(lambda x: "color: #00ff9d;", subset=[col_pnl]), use_container_width=True)
                with col_rank2:
                    st.markdown("#### 💀 Top 5 Losers")
                    worst_5 = closed_pos.nsmallest(5, col_pnl)[[asset_col, col_pnl]]
                    st.dataframe(worst_5.rename(columns={asset_col: 'Asset'}).style.format({col_pnl: "${:,.2f}"}).applymap(lambda x: "color: #ff4b4b;", subset=[col_pnl]), use_container_width=True)
                
                st.markdown("#### Complete Trade Log")
                st.dataframe(closed_pos.style.applymap(lambda x: "color: #00ff9d;" if isinstance(x, (int, float)) and x > 0 else ("color: #ff4b4b;" if isinstance(x, (int, float)) and x < 0 else ""), subset=[col_pnl]), use_container_width=True)
        else:
            st.info("Closed positions log not found or empty.")

# ==========================
# AI COPILOT SECTION (GEMINI)
# ==========================
if show_ai:
    with ai_col:
        st.markdown("### 🧠 AI Copilot (Gemini)")
        import os
        from dotenv import load_dotenv
        import yfinance as yf

        load_dotenv()
        GEMINI_KEY = os.getenv("GEMINI_API_KEY")
        
        if GEMINI_KEY:
            c1, c2 = st.columns([0.8, 0.2])
            if c2.button("🧹", help="Clear Memory", key="clear_chat_ai"):
                st.session_state.messages = []
                st.rerun()
            st.markdown("Query your metrics or evaluate assets in real-time.")
            
            try:
                import google.generativeai as genai
                genai.configure(api_key=GEMINI_KEY)
            except ImportError:
                st.warning("Google AI library not found. Please check requirements.txt.")
                st.stop()
        
        if "messages" not in st.session_state:
            st.session_state.messages = []
            
        chat_placeholder = st.container(height=650)
        
        for message in st.session_state.messages:
            role = "user" if message["role"] == "user" else "assistant"
            with chat_placeholder.chat_message(role):
                st.markdown(message["parts"][0])
                
        def get_portfolio_context():
            try:
                context = f"Current System Date: {datetime.now().strftime('%d %B %Y')}\n"
                context += "Portfolio Context:\n"
                if 'Net_Value' in equity_curve.columns:
                    context += f"Total Portfolio Value: ${equity_curve['Net_Value'].iloc[-1]:.2f}\n"
                if 'Total Return' in perf_metrics:
                    context += f"Overall Nominal Return: {perf_metrics['Total Return']*100:.2f}%\n"
                if 'TWRR' in perf_metrics:
                    context += f"TWRR (Flow-Adjusted): {perf_metrics['TWRR']*100:.2f}%\n"
                if 'Volatility' in risk_metrics:
                    context += f"Annualized Volatility: {risk_metrics['Volatility']*100:.2f}%\n"
                if 'Max Drawdown' in risk_metrics:
                    context += f"Max Historical Drawdown: {risk_metrics['Max Drawdown']*100:.2f}%\n"
                if 'Sortino' in risk_metrics:
                    context += f"Sortino Ratio: {risk_metrics['Sortino']:.2f}\n"
                if 'pe_ratio' in globals() and pd.notnull(pe_ratio):
                    context += f"Portfolio Weighted P/E: {pe_ratio:.2f}\n"

                if not pos_summary_realtime.empty:
                    context += "Active Holdings (Real-time Prices from Yahoo Finance):\n"
                    for _, r in pos_summary_realtime.head(5).iterrows():
                        ticker = r['Asset']
                        try:
                            curr_price = yf.Ticker(ticker).history(period="1d")['Close'].iloc[-1]
                            price_info = f"Yahoo Finance Live Price: ${curr_price:.2f}"
                        except:
                            price_info = "Live Price: Not available"
                        context += f"- {ticker}: {r['Net Value ($)']} USD ({price_info}, PnL %: {r['PnL (%)']:+.2%})\n"
                
                if 'closed_positions' in data_dict:
                    closed_df = data_dict['closed_positions']
                    if not closed_df.empty:
                        pnl_cols = [c for c in closed_df.columns if 'Beneficio' in c or 'Profit' in c or 'Ganancia' in c]
                        if pnl_cols:
                            c_pnl = pnl_cols[0]
                            closed_df[c_pnl] = pd.to_numeric(closed_df[c_pnl], errors='coerce').fillna(0)
                            tot_p = closed_df[closed_df[c_pnl] > 0][c_pnl].sum()
                            tot_l = closed_df[closed_df[c_pnl] < 0][c_pnl].sum()
                            context += f"Historical Realized PnL: ${tot_p+tot_l:.2f} (Profit: ${tot_p:.2f}, Loss: ${tot_l:.2f})\n"
                return context
            except:
                return "Portfolio data not available yet."

        if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
            with chat_placeholder.chat_message("assistant"):
                sys_inst = f"You are a professional financial portfolio analyst. Today is {datetime.now().strftime('%d %B %Y')}. DO NOT HALLUCINATE PRICES; use the ones provided. Data context:\n" + get_portfolio_context()
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
                    with st.spinner("Analyzing..."):
                        response = chat.send_message(st.session_state.messages[-1]["parts"][0])
                        st.markdown(response.text)
                    st.session_state.messages.append({"role": "model", "parts": [response.text]})
                except Exception as e:
                    st.error(f"AI Error: {e}")

        if prompt := st.chat_input("Ask a question about your portfolio..."):
            st.session_state.messages.append({"role": "user", "parts": [prompt]})
            st.rerun()
