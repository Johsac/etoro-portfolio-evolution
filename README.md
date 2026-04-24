# 📈 eToro Portfolio Evolution

[![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: CC BY-NC-SA 4.0](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc-sa/4.0/)

## 📝 Overview
**eToro Portfolio Evolution** is a professional-grade financial analytics dashboard that allows investors to bypass brokerage interface limitations. By reconstructing your portfolio history from raw eToro account statements, the platform calculates critical performance metrics like **TWRR (Time-Weighted Rate of Return)**, neutralizing the impact of deposits and withdrawals to reveal your true investment skill.

---

## 📂 Project Structure
```text
eToro-Portfolio-Evolution/
├── app.py                     # 🖼️ Frontend: Streamlit UI & Orchestration
├── data_loader.py             # ⚙️ Core: Excel Parser & Data Cleaning
├── portfolio_reconstructor.py  # ⚙️ Core: Daily Portfolio Reconstruction Engine
├── financial_metrics.py        # 📊 Analytics: TWRR, CAGR, Sharpe & Risk Math
├── forecasting.py              # 📊 Analytics: Monte Carlo & Compound Simulators
├── requirements.txt            # 🛠️ Setup: Project Dependencies
├── LICENSE                    # 🛠️ Setup: CC BY-NC-SA 4.0 (Non-Commercial)
├── .env.example               # 🛠️ Setup: Template for Optional AI Keys
└── .gitignore                 # 🛠️ Setup: Files excluded from Git (e.g., .env, venv)
```

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

### 4. Configure API Key (Optional)
This dashboard works 100% without an API key. However, if you want to use the **AI Copilot** feature, create a file named `.env` and add:
```env
GEMINI_API_KEY=your_key_here
```

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

## 🔒 Security & Privacy
*   **100% Local:** All data processing happens on **your machine**. Your statements are never sent to external servers.
*   **Privacy First:** Your Excel files and `.env` credentials are automatically ignored by Git (via `.gitignore`), so they will never be uploaded to GitHub.

---

## 📜 License
Licensed under **CC BY-NC-SA 4.0**. 
**Commercial use is prohibited.** You are free to share and adapt the code for personal use, provided you attribute the original author and use the same license.
