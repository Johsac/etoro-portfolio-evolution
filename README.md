# 📈 eToro Portfolio Evolution

**eToro Portfolio Evolution** es una plataforma de análisis financiero avanzada diseñada para inversores de eToro que buscan una comprensión profunda y técnica de su desempeño histórico. A diferencia de la interfaz estándar, esta herramienta reconstruye tu portafolio día a día, calcula métricas profesionales de riesgo y ofrece un Copiloto de IA integrado para análisis en tiempo real.

---

## 🚀 Características Principales

- **Reconstrucción Histórica:** Genera la evolución de tu Net Value basándose en cada operación, depósito y retiro realizado desde el primer día.
- **Métricas Profesionales:** 
    - **TWRR (Time-Weighted Rate of Return):** Elimina el ruido de los depósitos/retiros para medir tu habilidad real como inversor.
    - **Ratio Sharpe & Sortino:** Evaluación de rendimiento ajustado al riesgo.
    - **Drawdown Máximo:** Visualización de las mayores caídas históricas.
- **Copiloto IA (Powered by Gemini):** Un asistente financiero que "lee" tu portafolio y responde preguntas sobre métricas, diversificación y precios de mercado actuales (sincronizado con Yahoo Finance).
- **Proyecciones Monte Carlo:** Simula miles de escenarios futuros basados en tu volatilidad histórica.
- **Diseño Dinámico:** Dashboard expansible con modo de pantalla completa y panel de IA colapsable.

---

## 🛠 Estructura del Proyecto

```text
eToro-Portfolio-Evolution/
├── app.py                # Interfaz principal (Streamlit) y orquestación.
├── data_loader.py         # Lógica de parsing para archivos Excel de eToro.
├── portfolio_reconstructor.py # Motor de reconstrucción temporal de activos.
├── financial_metrics.py   # Cálculos de CAGR, TWRR, Sharpe y volatilidad.
├── forecasting.py         # Modelos de simulación Monte Carlo.
├── requirements.txt       # Dependencias necesarias.
├── .env                  # (Debes crearlo) Almacena tu API Key de Gemini.
└── README.md              # Documentación del proyecto.
```

---

## 📥 Instalación Paso a Paso

### 1. Clonar el repositorio
```bash
git clone https://github.com/tu-usuario/etoro-portfolio-evolution.git
cd etoro-portfolio-evolution
```

### 2. Crear un entorno virtual (Recomendado)
```bash
python -m venv venv
# En Windows:
.\venv\Scripts\activate
# En Mac/Linux:
source venv/bin/activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar la API Key de Google Gemini
Crea un archivo llamado `.env` en la carpeta raíz y añade tu clave:
```env
GEMINI_API_KEY=tu_clave_aqui_sin_comillas
```

---

## 📖 Cómo Funciona

1. **Exporta tus datos:** Ve a eToro > Configuración > Cuenta > Estado de Cuenta. Selecciona el rango completo de fechas y expórtalo a **Excel (.xlsx)**.
2. **Carga el archivo:** Usa el panel lateral "Carga de Datos" para subir tu Excel.
3. **Analiza:** Explora las pestañas de Resumen, Composición, Riesgo y Predicciones.
4. **Consulta a la IA:** Activa el interruptor gigante abajo a la izquierda ("Preguntar a la IA") para abrir el chat y realizar consultas complejas sobre tus datos.

---

## 🛡 Requisitos Técnicos

- Python 3.9+
- Streamlit
- Pandas & Plotly
- yfinance (para sincronización de precios reales)
- Google Generative AI SDK

---

## ✒️ Autor
Desarrollado con ❤️ para la comunidad de inversores de eToro.
