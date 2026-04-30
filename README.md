# 📈 eToro Portfolio Evolution

[![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: CC BY-NC-SA 4.0](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc-sa/4.0/)

## 📝 Overview
**eToro Portfolio Evolution** is a professional-grade financial analytics dashboard built for investors who want to go beyond the limitations of their broker's interface. By forensically reconstructing your portfolio history from raw eToro account statements, the platform reveals your true investment performance — neutralizing the distortion of deposits and withdrawals.

### ✨ Key Features

| Feature | Description |
|---------|-------------|
| **📊 Performance Metrics** | TWRR, Total Return, Sharpe Ratio, Sortino Ratio, CAGR, and Annualized Volatility — calibrated against your broker's values. |
| **📈 Normalized Performance** | Compare your portfolio returns against multiple benchmarks (S&P 500, NASDAQ 100, MSCI World) on the same chart, with time filters (Max, 5Y, 1Y, YTD, 6M, 3M). |
| **📉 Risk & Drawdown Analysis** | Interactive drawdown charts with benchmark comparisons and a "Worst Drawdowns" table (depth, start date, end date, duration). |
| **🧮 Asset Breakdown** | Allocation by asset, category, and real-time valuation from Yahoo Finance with P&L per position. |
| **💰 Wealth Composition** | Visualize how your portfolio value evolved vs. your capital invested vs. dividends received. |
| **📅 Monthly Returns Heatmap** | Color-coded matrix of monthly TWRR returns by year. |
| **💸 Passive Income Tracking** | Dividend history with monthly, quarterly, or annual grouping. |
| **🔮 Monte Carlo Simulation** | Probability-based future projections with confidence intervals. |
| **🌱 Compound Interest Planner** | Strategic calculator for projecting future wealth with contributions, growth, dividends, and inflation. |
| **🤖 AI Copilot** | An intelligent assistant that can answer questions about your portfolio and search live market data to help with investment decisions. |
| **📚 Trade History** | Searchable, sortable table of all your historical transactions. |

---

## 📂 Project Structure
```text
etoro-portfolio-evolution/
├── app.py                         # Main dashboard (entry point)
├── engine/                        # Data processing engine
│   ├── data_loader.py             # Excel reading and cleaning logic
│   └── portfolio_reconstructor.py # Account history reconstruction
├── analysis/                      # Financial analytics modules
│   ├── financial_metrics.py       # Financial math (TWRR, Sharpe, etc.)
│   └── forecasting.py            # Predictive models (Monte Carlo)
├── requirements.txt               # Dependencies with exact versions
├── .env                           # API key configuration (Private)
├── .gitignore                     # Files excluded from Git
└── LICENSE                        # CC BY-NC-SA 4.0
```

---

## 📥 How to Get Your eToro Account Statement

Before using this dashboard, you need to download your account statement from eToro:

1. **Log in** to your eToro account at [etoro.com](https://www.etoro.com).
2. Go to **Settings** → **Account Statement** (or navigate directly to your portfolio section).
3. Select the **date range** you want to analyze (e.g., from the date you opened your account to today).
4. Click **Download** — eToro will generate an Excel file named like:
   ```
   etoro-account-statement-8-31-2021-4-20-2026.xlsx
   ```
   > **Note:** The filename includes the start and end dates of the statement period (MM-DD-YYYY format).
5. **Save this file** — you will upload it directly into the dashboard.

> ⚠️ **Important:** The Excel file contains multiple sheets (Account Summary, Activity, Dividends, etc.). Do NOT modify or rename the sheets — the dashboard reads them automatically.

---

## 🚀 Installation & Setup Guide

Following these steps will set up the application on your computer from scratch:

### 1. Clone the Repository
Open your terminal and run:
```bash
git clone https://github.com/Johsac/etoro-portfolio-evolution.git
cd etoro-portfolio-evolution
```

### 2. Create a Virtual Environment
This isolates the project dependencies.
```bash
# General command:
python -m venv venv

# Activate on Windows:
.\venv\Scripts\activate

# Activate on Linux/Mac:
source venv/bin/activate
```

### 3. Install Required Libraries
```bash
pip install -r requirements.txt
```

### 4. Configure the AI Copilot (Optional)

The AI Copilot feature requires a **free** Google Gemini API key. Here's how to get one:

1. Go to [Google AI Studio](https://aistudio.google.com/apikey).
2. Sign in with your Google account.
3. Click **"Create API Key"** → select or create a Google Cloud project.
4. **Copy the API key** that is generated.
5. Create a `.env` file in the project root directory:
   ```env
   GEMINI_API_KEY=your_api_key_here
   ```

> 💡 **Model Info:** The AI Copilot currently uses **`gemini-2.5-flash-lite`**, which has the best free-tier limits (15 requests/min, 1000 requests/day). As Google releases newer models, this may become deprecated. If you encounter errors like `RESOURCE_EXHAUSTED` or model not found, update the model name in `app.py` (search for `gemini-2.5-flash-lite` and replace with the latest available model from the [Gemini Models page](https://ai.google.dev/gemini-api/docs/models)).

---

## 🎮 How to Run the App

Once the installation is complete, you can launch the dashboard with a single command:

1. **Start the server:**
   ```bash
   streamlit run app.py
   ```
2. **Access the Dashboard:**
   Streamlit will automatically open your default web browser. If it doesn't, navigate to:
   `http://localhost:8501`

3. **Usage:**
   - Go to the **"Data Upload"** panel in the sidebar.
   - Upload your eToro Account Statement (`.xlsx`).
   - Explore the different tabs: Account Summary, Asset Breakdown, Risk Analysis, etc.

---

## 🤖 AI Copilot Architecture

The AI Copilot uses a **dual-strategy** architecture for reliability:

| Strategy | Method | When Used |
|----------|--------|-----------|
| **Strategy 1** (Primary) | Multi-Agent Orchestrator — 3 specialized agents (portfolio analyst, web search, coordinator) working together | First attempt for every query |
| **Strategy 2** (Fallback) | Direct single API call with portfolio context injected | Automatically activated if Strategy 1 hits rate limits (429/503 errors) |

Each response displays a small label indicating which strategy was used:
- 🤖 *Powered by Multi-Agent Orchestrator*
- ⚡ *Powered by Direct AI (lightweight mode)*

The copilot automatically detects the language of your question and responds in the same language.

---

## 🔒 Security & Privacy
*   **100% Local:** All data processing happens on **your machine**. Your financial statements are never sent to external servers.
*   **Privacy First:** Your Excel files and `.env` credentials are automatically ignored by Git (via `.gitignore`), so they will never be uploaded to GitHub.
*   **AI Copilot:** When using the AI feature, only a summarized context of your portfolio (not the raw Excel data) is sent to Google's Gemini API to generate responses.

---

## 🛠️ Troubleshooting

| Issue | Solution |
|-------|----------|
| `RESOURCE_EXHAUSTED (429)` | You've hit the free-tier API limit. Wait a few minutes or try again tomorrow (resets daily). |
| AI Copilot not responding | Verify your `.env` file has a valid `GEMINI_API_KEY`. Check that the model name is current. |
| Metrics look wrong after update | Clear Streamlit cache: press `C` in the app or delete the `__pycache__` folders. |
| Yahoo Finance download errors | Some delisted stocks (e.g., MRO) may fail. This is expected and doesn't affect the rest of the analysis. |
| Slow first load | The first run downloads historical prices from Yahoo Finance for all your positions. Subsequent runs use cached data. |

---

## 📜 License
Licensed under **CC BY-NC-SA 4.0**. 
**Commercial use is prohibited.** You are free to share and adapt the code for personal use, provided you attribute the original author and use the same license.
