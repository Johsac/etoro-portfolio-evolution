import pandas as pd
import numpy as np

def load_etoro_data(file):
    """
    Carga y procesa un archivo Excel de eToro (.xlsx)
    Requiere las pestañas: 'Resumen de la cuenta', 'Posiciones cerradas', 
    'Actividad de la cuenta', 'Dividendos', 'Resumen financiero'
    """
    try:
        xls = pd.ExcelFile(file)
        
        # Load sheets directly by their Spanish names
        activity = pd.read_excel(xls, 'Actividad de la cuenta')
        closed_positions = pd.read_excel(xls, 'Posiciones cerradas')
        dividends = pd.read_excel(xls, 'Dividendos')
        summary = pd.read_excel(xls, 'Resumen de la cuenta')
        financial_summary = pd.read_excel(xls, 'Resumen financiero')
        
    except ValueError as e:
        raise Exception(f"File loading error: One or more required sheets were not found. {e}")
    except Exception as e:
        raise Exception(f"General exception loading file: {e}")
        
    return clean_data(activity, closed_positions, dividends, summary, financial_summary)


def fetch_summary_attributes(summary_df):
    """
    Extrae la fecha de inicio y finalización del resumen de la cuenta.
    """
    attrs = {}
    try:
        # eToro usually places 'Fecha de inicio' and 'Fecha final' in the first column
        # and the actual date in the second column (Unnamed: 1)
        for _, row in summary_df.iterrows():
            key = str(row.iloc[0]).lower()
            val = row.iloc[1]
            if 'fecha de inicio' in key:
                attrs['start_date'] = pd.to_datetime(val, dayfirst=True)
            elif 'fecha final' in key or 'fecha de finalización' in key:
                attrs['end_date'] = pd.to_datetime(val, dayfirst=True)
    except Exception as e:
        print(f"Error extracting dates from summary: {e}")
    return attrs

def clean_data(activity, closed_positions, dividends, summary, financial_summary):
    # ==========================
    # 1. ACTIVIDAD DE LA CUENTA
    # ==========================
    # Standard date format in eToro: DD/MM/YYYY HH:MM:SS
    if 'Fecha' in activity.columns:
        activity['Fecha'] = pd.to_datetime(activity['Fecha'], format='%d/%m/%Y %H:%M:%S', errors='coerce')
        activity = activity.dropna(subset=['Fecha'])
        activity = activity.sort_values('Fecha').reset_index(drop=True)
        # Create a date-only column for daily grouping
        activity['Date'] = activity['Fecha'].dt.date
    else:
        # Fallback if different translation
        date_cols = [c for c in activity.columns if 'date' in c.lower() or 'fecha' in c.lower()]
        if date_cols:
            activity[date_cols[0]] = pd.to_datetime(activity[date_cols[0]], errors='coerce')

    # Ensure numerical columns are floats
    numeric_cols = ['Importe', 'Saldo', 'Variación del capital realizado']
    for col in numeric_cols:
        if col in activity.columns:
            # Eliminar posibles símbolos de moneda o comas
            if activity[col].dtype == 'object':
                activity[col] = activity[col].astype(str).str.replace('$', '').str.replace(',', '').astype(float)
            else:
                activity[col] = activity[col].astype(float)


    # ==========================
    # 2. POSICIONES CERRADAS
    # ==========================
    date_cols_pos = ['Fecha de apertura', 'Fecha de cierre']
    for col in date_cols_pos:
        if col in closed_positions.columns:
            closed_positions[col] = pd.to_datetime(closed_positions[col], format='%d/%m/%Y %H:%M:%S', errors='coerce')

    numeric_cols_pos = ['Importe', 'Ganancias(USD)', 'Comisiones nocturnas', 'Comisiones diarias']
    for col in numeric_cols_pos:
        # eToro might use "Ganancias" or "Ganancias (USD)" due to spaces
        actual_col = [c for c in closed_positions.columns if col.replace(" ", "").lower() in c.replace(" ", "").lower()]
        for ac in actual_col:
            if closed_positions[ac].dtype == 'object':
                 closed_positions[ac] = closed_positions[ac].astype(str).str.replace('$', '').str.replace(',', '').astype(float)
            else:
                 closed_positions[ac] = closed_positions[ac].astype(float)

    # ==========================
    # 3. DIVIDENDOS
    # ==========================
    if 'Fecha de pago' in dividends.columns:
        dividends['Fecha de pago'] = pd.to_datetime(dividends['Fecha de pago'], format='%d/%m/%Y %H:%M:%S', errors='coerce')

    attrs = fetch_summary_attributes(summary)

    return {
        'activity': activity,
        'closed_positions': closed_positions,
        'dividends': dividends,
        'summary': summary,
        'financial_summary': financial_summary,
        'summary_attrs': attrs
    }
