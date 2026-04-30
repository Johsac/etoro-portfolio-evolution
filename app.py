import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from engine.data_loader import load_etoro_data
from analysis.financial_metrics import calculate_performance_metrics, calculate_risk_metrics, get_monthly_returns
from analysis.forecasting import monte_carlo_simulation, get_monte_carlo_percentiles, trend_forecasting
from engine.portfolio_reconstructor import reconstruct_portfolio

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
                summary_attrs = data_dict.get('summary_attrs', {})
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
    equity_curve = pd.DataFrame()
    pos_summary_realtime = pd.DataFrame()
    perf_metrics = {}
    risk_metrics = {}
    
    with st.spinner("Fetching historical prices from Yahoo Finance & Processing Splits..."):
        try:
            equity_curve, pos_summary_realtime = reconstruct_portfolio(activity)
            equity_curve = equity_curve.copy()  # Prevent cache mutation
            
            # Bound equity_curve to Excel summary dates if available
            if not equity_curve.empty:
                if 'start_date' in summary_attrs and pd.notnull(summary_attrs['start_date']):
                    equity_curve = equity_curve[equity_curve['Date'] >= summary_attrs['start_date']]
                if 'end_date' in summary_attrs and pd.notnull(summary_attrs['end_date']):
                    equity_curve = equity_curve[equity_curve['Date'] <= summary_attrs['end_date']]
                    
                perf_metrics = calculate_performance_metrics(equity_curve, activity)
                risk_metrics = calculate_risk_metrics(equity_curve)
        except Exception as e:
            import traceback
            st.error(f"Error reconstruct_portfolio: {e}\n{traceback.format_exc()}")
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
            st.metric("Total Return (Nominal)", f"{perf_metrics.get('Total Return', 0)*100:.2f}%", help="Measures the total gross profit of the portfolio.")
        with col2:
            st.metric("TWRR (Flow Adjusted)", f"{perf_metrics.get('TWRR', 0)*100:.2f}%", help="Time-Weighted Return: Real performance isolating the effect of deposits/withdrawals.")
        with col3:
            st.metric("Annualized Volatility", f"{risk_metrics.get('Volatility', 0)*100:.2f}%", help="Annual standard deviation; measures historical price swings.")
        with col4:
            st.metric("Sharpe Ratio", f"{risk_metrics.get('Sharpe', 0):.2f}", help="Risk-adjusted return. >1.0 is acceptable, >2.0 is excellent.")
        with col5:
            from analysis.financial_metrics import get_portfolio_pe
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
             bench_selected = st.multiselect("Compare with Benchmarks:", list(BENCHMARKS.keys()), default=["S&P 500"])
             custom_bench = st.text_input("Add Custom Ticker (e.g., ARKK):", key="custom_bench_input")
                 
        with col_time:
             st.write("Time Filter:")
             timeframe = st.radio("Window:", ["Max", "5Y", "1Y", "YTD", "6M", "3M"], horizontal=True, label_visibility="collapsed")
             
             st.write("Return Type:")
             ret_type = st.radio("Type:", ["Absolute Profit (eToro Style)", "TWRR (Strict)"], index=1, horizontal=True, label_visibility="collapsed")
        
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
        if ret_type == "Absolute Profit (eToro Style)":
             base_deposits = df_plot['Cumulative_Net_Flow'].iloc[0]
             df_plot['Active_Deposits'] = df_plot['Cumulative_Net_Flow'] - base_deposits
             base_val = df_plot['Net_Value'].iloc[0]
             df_plot['Active_Profit'] = df_plot['Net_Value'] - base_val - df_plot['Active_Deposits']
             
             safe_deposits = df_plot['Active_Deposits'].replace(0, np.nan)
             df_plot['TWRR_Period'] = (df_plot['Active_Profit'] / safe_deposits).fillna(0)
        else:
             if 'Daily_TWRR' in df_plot.columns:
                  temp_twrr = df_plot['Daily_TWRR'].copy()
                  temp_twrr.iloc[0] = 0
                  df_plot['TWRR_Period'] = (1 + temp_twrr).cumprod() - 1
             else:
                  initial_val = df_plot['Net_Value'].iloc[0]
                  if initial_val != 0:
                      df_plot['TWRR_Period'] = (df_plot['Net_Value'] / initial_val) - 1
                  else:
                      df_plot['TWRR_Period'] = 0
        
        fig_eq = go.Figure()
        
        name_label = 'Portfolio (Absolute ROI)' if ret_type == "Absolute Profit (eToro Style)" else 'Portfolio (TWRR)'
        fig_eq.add_trace(go.Scatter(x=df_plot['Date'], y=df_plot['TWRR_Period'], mode='lines', 
                                    name=name_label, line=dict(color='#00ff9d', width=3),
                                    fill='tozeroy', fillcolor='rgba(0, 255, 157, 0.1)'))
        
        # Add Benchmarks (multi-select)
        import yfinance as yf
        bench_colors = {"S&P 500": "#ff9900", "NASDAQ 100": "#00bfff", "MSCI World": "#ff66ff"}
        all_bench_tickers = [(name, BENCHMARKS[name]) for name in bench_selected]
        if custom_bench.strip():
            all_bench_tickers.append((custom_bench.upper(), custom_bench.upper()))
        
        for bench_name, bench_ticker in all_bench_tickers:
            try:
                b_data = yf.download(bench_ticker.upper(), start=start_date, end=end_date+pd.Timedelta(days=1), progress=False)['Close']
                if isinstance(b_data, pd.DataFrame) and not b_data.empty: 
                     b_data = b_data.iloc[:, 0]
                if not b_data.empty:
                    b_start_val = b_data.iloc[0]
                    if b_start_val > 0:
                        b_cum = (b_data / b_start_val) - 1
                        color = bench_colors.get(bench_name, '#888888')
                        fig_eq.add_trace(go.Scatter(x=b_cum.index, y=b_cum, mode='lines', 
                                                    name=bench_name, line=dict(color=color, width=2, dash='dash')))
            except Exception:
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
                from engine.portfolio_reconstructor import TICKER_MAPPING
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
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Max Drawdown", f"{risk_metrics['Max Drawdown']*100:.2f}%", delta_color="inverse", help="Deepest historical drop from peak to trough in the equity curve.")
        with col2:
            st.metric("Sortino Ratio", f"{risk_metrics['Sortino']:.2f}", help="Sharpe variant that only penalizes downward volatility (losses).")
        with col3:
            st.metric("Sharpe Ratio", f"{risk_metrics['Sharpe']:.2f}", help="Risk-adjusted return. >1.0 is acceptable, >2.0 is excellent.")
        
        # --- Time Filter & Benchmark Controls ---
        col_dd_bench, col_dd_time = st.columns([1, 2])
        with col_dd_bench:
            dd_benchmarks = st.multiselect("Compare Drawdown vs:", ["S&P 500", "NASDAQ 100", "MSCI World"], default=["S&P 500"])
        with col_dd_time:
            dd_timeframe = st.radio("Time Filter:", ["Max", "5Y", "1Y", "YTD", "6M", "3M"], horizontal=True, key="dd_time")
        
        DD_BENCH_MAP = {"S&P 500": "^GSPC", "NASDAQ 100": "^NDX", "MSCI World": "URTH"}
        
        # Time filter logic
        dd_plot = equity_curve.copy()
        dd_end = dd_plot['Date'].max()
        if dd_timeframe == '5Y': dd_start = dd_end - pd.DateOffset(years=5)
        elif dd_timeframe == '1Y': dd_start = dd_end - pd.DateOffset(years=1)
        elif dd_timeframe == 'YTD': dd_start = pd.to_datetime(f"{dd_end.year}-01-01")
        elif dd_timeframe == '6M': dd_start = dd_end - pd.DateOffset(months=6)
        elif dd_timeframe == '3M': dd_start = dd_end - pd.DateOffset(months=3)
        else: dd_start = dd_plot['Date'].min()
        
        dd_plot = dd_plot[dd_plot['Date'] >= dd_start].copy()
        
        # Recalculate drawdown for filtered period using TWRR-based cumulative return
        if 'Daily_TWRR' in dd_plot.columns and len(dd_plot) > 1:
            temp_twrr = dd_plot['Daily_TWRR'].copy()
            temp_twrr.iloc[0] = 0
            dd_plot['Cum_Return'] = (1 + temp_twrr).cumprod()
            dd_plot['DD_Peak'] = dd_plot['Cum_Return'].cummax()
            dd_plot['DD_Series'] = (dd_plot['Cum_Return'] / dd_plot['DD_Peak']) - 1
        else:
            dd_plot['DD_Peak'] = dd_plot['Net_Value'].cummax()
            dd_plot['DD_Series'] = (dd_plot['Net_Value'] - dd_plot['DD_Peak']) / dd_plot['DD_Peak']
        
        st.markdown("### \U0001f3a2 Historical Drawdown Timeline (%)")
        fig_dd = go.Figure()
        fig_dd.add_trace(go.Scatter(x=dd_plot['Date'], y=dd_plot['DD_Series'], mode='lines',
                                    name='Portfolio', line=dict(color='#00ff9d', width=2),
                                    fill='tozeroy', fillcolor='rgba(0, 255, 157, 0.1)'))
        
        # Add benchmark drawdowns
        import yfinance as yf
        for bench_name in dd_benchmarks:
            bench_tick = DD_BENCH_MAP.get(bench_name, "^GSPC")
            try:
                b_data = yf.download(bench_tick, start=dd_start, end=dd_end + pd.Timedelta(days=1), progress=False)['Close']
                if isinstance(b_data, pd.DataFrame) and not b_data.empty:
                    b_data = b_data.iloc[:, 0]
                if not b_data.empty:
                    b_ret = b_data.pct_change().fillna(0)
                    b_ret.iloc[0] = 0
                    b_cum = (1 + b_ret).cumprod()
                    b_peak = b_cum.cummax()
                    b_dd = (b_cum / b_peak) - 1
                    colors = {"S&P 500": "#ff9900", "NASDAQ 100": "#00bfff", "MSCI World": "#ff66ff"}
                    fig_dd.add_trace(go.Scatter(x=b_data.index, y=b_dd, mode='lines',
                                                name=bench_name, line=dict(color=colors.get(bench_name, '#888'), width=1.5, dash='dash')))
            except Exception:
                pass
        
        fig_dd.update_layout(template="plotly_dark", yaxis_title="Drawdown (%)",
                             yaxis_tickformat='.1%',
                             margin=dict(l=0, r=0, t=30, b=0), hovermode="x unified",
                             legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig_dd, use_container_width=True)
        
        # --- Worst Drawdowns Table ---
        st.markdown("### \U0001f4c9 Worst Drawdowns")
        if 'DD_Series' in dd_plot.columns:
            # Identify drawdown periods
            in_dd = dd_plot['DD_Series'] < 0
            dd_groups = (~in_dd).cumsum()
            
            dd_periods = []
            for group_id, group_df in dd_plot[in_dd].groupby(dd_groups[in_dd]):
                if len(group_df) > 0:
                    depth = group_df['DD_Series'].min()
                    start_dt = group_df['Date'].iloc[0]
                    end_dt = group_df['Date'].iloc[-1]
                    months = max(1, round((end_dt - start_dt).days / 30))
                    dd_periods.append({
                        'Depth': depth,
                        'Start': start_dt.strftime('%b %Y'),
                        'End': end_dt.strftime('%b %Y'),
                        'Total Months': months
                    })
            
            if dd_periods:
                dd_table = pd.DataFrame(dd_periods).sort_values('Depth').head(5).reset_index(drop=True)
                dd_table['Depth'] = dd_table['Depth'].apply(lambda x: f"{x*100:.2f}%")
                st.dataframe(dd_table, use_container_width=True, hide_index=True)
            else:
                st.info("No drawdowns detected in the selected period.")

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
            from analysis.forecasting import compound_interest_simulator
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
                if drip_bool:
                    fig_var.add_trace(go.Scatter(x=df_comp['Año'], y=df_comp['Factor_DRIP_Up'], mode='lines',
                                                 name='Upper Bound (Bullish)', line=dict(color='rgba(0,255,157,0.5)', dash='dash')))
                    fig_var.add_trace(go.Scatter(x=df_comp['Año'], y=df_comp['Factor_DRIP_Down'], mode='lines',
                                                 name='Lower Bound (Bearish)', line=dict(color='rgba(255,100,100,0.5)', dash='dash')))
                                                 
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
                    
                    st.markdown("### 📊 Historical + Projected Timeline")
                    fig_full = go.Figure()
                    
                    # Historical Data
                    fig_full.add_trace(go.Scatter(x=equity_curve['Date'], y=equity_curve['Net_Value'],
                                                  mode='lines', name='Historical Value', line=dict(color='gray', width=2)))
                    
                    # Create future dates
                    last_date = equity_curve['Date'].iloc[-1]
                    future_dates = pd.date_range(start=last_date, periods=mc_days+1, freq='B')
                    
                    if len(future_dates) == len(percentiles_df):
                        fig_full.add_trace(go.Scatter(x=future_dates, y=percentiles_df['P90 (Bullish)'],
                                                      mode='lines', name='Bullish (P90)', line=dict(color='rgba(0,255,157, 0.8)', dash='dash')))
                        fig_full.add_trace(go.Scatter(x=future_dates, y=percentiles_df['P50 (Expected)'],
                                                      mode='lines', name='Expected (P50)', line=dict(color='#00ff9d', width=3)))
                        fig_full.add_trace(go.Scatter(x=future_dates, y=percentiles_df['P10 (Bearish)'],
                                                      mode='lines', name='Bearish (P10)', line=dict(color='rgba(255,75,75,0.8)', dash='dash'),
                                                      fill='tonexty', fillcolor='rgba(0,255,157,0.1)'))
                    
                    fig_full.update_layout(template="plotly_dark", title="Full Portfolio Evolution",
                                           xaxis_title="Date", yaxis_title="Total Equity ($)", hovermode="x unified")
                    st.plotly_chart(fig_full, use_container_width=True)
                    
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
                    st.dataframe(best_5.rename(columns={asset_col: 'Asset'}).style.format({col_pnl: "${:,.2f}"}).map(lambda x: "color: #00ff9d;", subset=[col_pnl]), use_container_width=True)
                with col_rank2:
                    st.markdown("#### 💀 Top 5 Losers")
                    worst_5 = closed_pos.nsmallest(5, col_pnl)[[asset_col, col_pnl]]
                    st.dataframe(worst_5.rename(columns={asset_col: 'Asset'}).style.format({col_pnl: "${:,.2f}"}).map(lambda x: "color: #ff4b4b;", subset=[col_pnl]), use_container_width=True)
                
                st.markdown("#### Complete Trade Log")
                st.dataframe(closed_pos.style.map(lambda x: "color: #00ff9d;" if isinstance(x, (int, float)) and x > 0 else ("color: #ff4b4b;" if isinstance(x, (int, float)) and x < 0 else ""), subset=[col_pnl]), use_container_width=True)
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
                if 'Sharpe' in risk_metrics:
                    context += f"Sharpe Ratio: {risk_metrics['Sharpe']:.2f}\n"
                if 'pe_ratio' in globals() and pd.notnull(pe_ratio):
                    context += f"Portfolio Weighted P/E: {pe_ratio:.2f}\n"

                if not pos_summary_realtime.empty:
                    context += "Active Holdings:\n"
                    for _, r in pos_summary_realtime.iterrows():
                        ticker = r['Asset']
                        context += f"- {ticker}: {r['Net Value ($)']} USD (PnL %: {r['PnL (%)']:+.2%})\n"
                
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
                prompt_text = st.session_state.messages[-1]["parts"][0]
                final_text = ""
                used_fallback = False
                
                # =========================================================
                # STRATEGY 1: Multi-Agent Orchestrator (ADK)
                # Uses 3 lightweight agents for complex queries.
                # =========================================================
                try:
                    from google.adk.agents import Agent
                    from google.adk.models.google_llm import Gemini
                    from google.adk.tools import google_search, AgentTool
                    from google.adk.runners import InMemoryRunner
                    from google.genai import types
                    import asyncio
                    
                    retry_config = types.HttpRetryOptions(
                        attempts=3,
                        exp_base=2,
                        initial_delay=1,
                        http_status_codes=[429, 500, 503, 504]
                    )
                    
                    portfolio_context = get_portfolio_context()
                    
                    portfolio_agent = Agent(
                        name="portfolio_agent",
                        model=Gemini(
                            model="gemini-2.5-flash-lite",
                            retry_options=retry_config
                        ),
                        instruction=f"You are an expert eToro portfolio analyst. Today is {datetime.now().strftime('%d %B %Y')}. Answer ONLY based on the following user account context. Do not invent data. IMPORTANT: Always respond in the SAME language the user writes in.\nContext:\n{portfolio_context}"
                    )
                    
                    web_search_agent = Agent(
                        name="web_search_agent",
                        model=Gemini(
                            model="gemini-2.5-flash-lite",
                            retry_options=retry_config
                        ),
                        instruction="You are a financial search assistant. Use google_search to find macroeconomic data, current stock prices (prioritize Yahoo Finance), and global market news. Respond concisely in the same language the user used.",
                        tools=[google_search]
                    )
                    
                    coordinator_agent = Agent(
                        name="coordinator",
                        model=Gemini(
                            model="gemini-2.5-flash-lite",
                            retry_options=retry_config
                        ),
                        instruction="You are a financial orchestrator. You have two tools: portfolio_agent and web_search_agent.\n1. Call portfolio_agent if the question is about the user's portfolio.\n2. Call web_search_agent if you need recent prices or macroeconomic news.\n3. You may call BOTH if the user wants to compare their portfolio with external market data.\n4. CRITICAL: Always respond in the SAME language the user writes in. If they write in Spanish, respond in Spanish. If in English, respond in English.",
                        tools=[AgentTool(portfolio_agent), AgentTool(web_search_agent)]
                    )
                    
                    runner = InMemoryRunner(agent=coordinator_agent)
                    
                    with st.spinner("🔍 Analyzing with Multi-Agent System..."):
                        response = asyncio.run(runner.run_debug(prompt_text))
                        
                        if isinstance(response, list):
                            for event in response:
                                if getattr(event, 'content', None) and getattr(event.content, 'parts', None):
                                    for part in event.content.parts:
                                        if getattr(part, 'text', None):
                                            final_text += part.text + "\n"
                        else:
                            final_text = str(response)
                        
                        if final_text.strip():
                            st.caption("🤖 *Powered by Multi-Agent Orchestrator*")
                            
                except Exception as e:
                    error_msg = str(e)
                    if "429" in error_msg or "503" in error_msg or "UNAVAILABLE" in error_msg or "TooManyRequests" in error_msg:
                        used_fallback = True
                    else:
                        final_text = ""
                        used_fallback = True
                
                # =========================================================
                # STRATEGY 2: Fallback — Single Direct API Call
                # Uses one lightweight call when agents hit rate limits.
                # =========================================================
                if not final_text.strip() or used_fallback:
                    try:
                        from google import genai
                        
                        api_key = os.environ.get("GEMINI_API_KEY", "")
                        client = genai.Client(api_key=api_key)
                        
                        portfolio_context = get_portfolio_context()
                        system_prompt = (
                            f"You are an expert financial advisor for eToro portfolios. "
                            f"Today is {datetime.now().strftime('%d %B %Y')}. "
                            f"Answer the user's question based on the portfolio data below. "
                            f"CRITICAL: Always respond in the SAME language the user writes in.\n\n"
                            f"PORTFOLIO DATA:\n{portfolio_context}"
                        )
                        
                        with st.spinner("💡 Using Direct AI (lightweight mode)..."):
                            response = client.models.generate_content(
                                model="gemini-2.5-flash-lite",
                                contents=f"{system_prompt}\n\nUser Question: {prompt_text}",
                            )
                            final_text = response.text if response.text else ""
                            
                        if final_text.strip():
                            st.caption("⚡ *Powered by Direct AI (lightweight mode)*")
                    except Exception as fallback_err:
                        final_text = f"Both AI strategies failed. Error: {fallback_err}"
                
                if not final_text.strip():
                    final_text = "Could not generate a response. Please check your API key configuration or try again later."
                
                st.markdown(final_text)
                st.session_state.messages.append({"role": "model", "parts": [final_text]})

        if prompt := st.chat_input("Ask a question about your portfolio..."):
            st.session_state.messages.append({"role": "user", "parts": [prompt]})
            st.rerun()
