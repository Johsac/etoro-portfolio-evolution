# 📈 eToro Portfolio Evolution

[![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: CC BY-NC-SA 4.0](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc-sa/4.0/)

## 📝 Overview
**eToro Portfolio Evolution** is a professional-grade financial analytics dashboard that allows investors to bypass brokerage interface limitations. By reconstructing your portfolio history from raw eToro account statements, the platform calculates critical performance metrics like **TWRR (Time-Weighted Rate of Return)**, neutralizing the impact of deposits and withdrawals to reveal your true investment skill.

---

## 📂 Project Structure
The project is organized into logical modules to separate concerns between data processing, financial math, and user interface:

### 🖼️ Frontend & Orchestration
*   `app.py`: The main entry point. Handles the Streamlit UI, sidebar controls, and dashboard layout. 

### ⚙️ Core Engines
*   `data_loader.py`: **The Parser.** Robust logic to extract and clean data from eToro Excel statements.
*   `portfolio_reconstructor.py`: **The Brain.** Rebuilds your daily holdings, handles stock splits, and syncs historical prices from Yahoo Finance.

### 📊 Analytics & Mathematics
*   `financial_metrics.py`: **Performance Engine.** Calculates TWRR, CAGR, Sharpe Ratio, Sortino Ratio, and Drawdowns.
*   `forecasting.py`: **Intelligence Engine.** Powers Monte Carlo probability simulations and Compound Interest projections.

### 🛠️ Setup & Configuration
*   `requirements.txt`: List of all necessary Python libraries for reproduction.
*   `LICENSE`: Legal framework (CC BY-NC-SA 4.0) protecting the work.
*   `.env.example`: Template for optional configuration (AI Keys).
*   `.gitignore`: Safe-list to prevent private financial data or local environments (`venv`) from being uploaded.

> [!NOTE]
> The `/venv` folder is purposefully excluded from the repository. It is a local environment generated during installation to keep the project lightweight and secure.

---

## 🚦 Getting Started
To reproduce this project locally, ensure you have an **eToro Account Statement** (Excel format) exported from your eToro account (Settings > Account > View > Export). 

---

## ⚙️ Installation
Follow these exact steps to set up a functional local copy:

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/Johsac/etoro-portfolio-evolution.git
   cd etoro-portfolio-evolution
   ```

2. **Initialize Environment:**
   ```bash
   python -m venv venv
   # Windows:
   .\venv\Scripts\activate
   # Linux/Mac:
   source venv/bin/activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

## 🔑 Environmental Variables (Optional)
This application includes an **AI Copilot** feature powered by Google Gemini.
*   **Is it mandatory?** No. The dashboard is fully functional for financial analysis without an API key. 
*   **How to enable it:** If you wish to use the AI chat, create a `.env` file and add your key:
    ```env
    GEMINI_API_KEY=your_google_ai_studio_key
    ```

---

## 🔒 Security & Privacy
1.  **Local Isolation:** All analysis is performed on your machine. Your Excel statements are **never** uploaded to a server.
2.  **Data Blindness:** The source code is configured to ignore `.xlsx` and `.env` files via `.gitignore`, ensuring your private data never reaches GitHub.

---

## 📜 License
Licensed under **CC BY-NC-SA 4.0**. 
**Prohibits commercial use.** You may share and adapt the code for personal use, provided you attribute the original author and use the same license.
