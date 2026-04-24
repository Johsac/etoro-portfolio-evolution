# 📈 eToro Portfolio Evolution

[![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://etoro-portfolio-evolution.streamlit.app/)
[![License: CC BY-NC-SA 4.0](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc-sa/4.0/)

## 📝 Overview
**eToro Portfolio Evolution** is a high-performance financial analytics dashboard designed for eToro investors who demand professional-grade insights into their historical performance. 

Standard brokerage interfaces often mask true performance due to deposits and withdrawals. This tool solves that by reconstructing your entire portfolio history day-by-day, calculating the **Time-Weighted Rate of Return (TWRR)**, and providing an AI-powered Copilot for deep forensic analysis of your assets.

---

## 📂 Project Structure
The project is built with a modular architecture to ensure scalability and ease of maintenance:

```text
eToro-Portfolio-Evolution/
├── app.py                     # Entry point: Streamlit UI orquestration & layout
├── data_loader.py             # Excel Parser: Processes eToro Account Statements
├── portfolio_reconstructor.py  # Core Engine: Rebuilds daily holding & cash flows
├── financial_metrics.py        # Analytics: TWRR, CAGR, Sharpe, Sortino, Drawdown
├── forecasting.py              # Statistics: Monte Carlo price simulations
├── requirements.txt            # Dependency manifest
├── .env.example                # Template for environment variables (API Keys)
├── .gitignore                  # Protection for sensitive data (.env, .xlsx)
└── README.md                   # Project documentation
```

---

## 🚦 Getting Started
Before running the application, ensure you have:
1.  **eToro Account Statement:** Exported from your eToro account (Settings > Account > View > Export to Excel). Ensure you select the maximum possible timeframe.
2.  **Google Gemini API Key:** Obtain a free key from the [Google AI Studio](https://aistudio.google.com/).

---

## ⚙️ Installation
Follow these steps to set up the environment locally:

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/tu-usuario/etoro-portfolio-evolution.git
   cd etoro-portfolio-evolution
   ```

2. **Setup Virtual Environment:**
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

4. **Environmental Variables:**
   Create a `.env` file in the root directory:
   ```env
   GEMINI_API_KEY=your_api_key_here
   ```

---

## 📖 Usage Guide
1. Run the app: `streamlit run app.py`.
2. Expand the **"Carga de Datos"** (Data Loading) panel in the sidebar.
3. Upload your `.xlsx` statement. The system will automatically fetch historical prices and adjust for splits.
4. Toggle **"Preguntar a la IA"** (Ask AI) at the bottom left to enable the dedicated AI Sidebar for asset analysis.

---

## 🔒 Security & Privacy
*   **Local Processing:** All Excel data parsing and financial calculations are performed **locally** in your machine or hosting environment.
*   **Data Protection:** Your financial statements are **never** uploaded to external servers (except for the anonymized portfolio context sent to Gemini API if you use the AI chat).
*   **Secret Management:** Your API Keys are stored in `.env` and excluded from git via `.gitignore` to prevent leaks.

---

## 🤝 Contribution & Support
Contributions are welcome! If you find a bug or have a feature request, please:
1.  Open an **Issue** describing the problem.
2.  Submit a **Pull Request** for enhancements.

For support, you can reach out via GitHub Issues or contact the project maintainers.

---

## 📜 License
This project is licensed under the **Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)**.

**You are free to:**
*   **Share** — copy and redistribute the material in any medium or format.
*   **Adapt** — remix, transform, and build upon the material.

**Under the following terms:**
*   **Attribution** — You must give appropriate credit.
*   **NonCommercial** — You may **NOT** use the material for commercial purposes.
*   **ShareAlike** — If you remix, transform, or build upon the material, you must distribute your contributions under the same license as the original.

---
*Created with ❤️ for the eToro investor community.*
