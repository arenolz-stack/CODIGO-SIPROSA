# app.py (Archivo Principal Revisado)

import dash
import dash_bootstrap_components as dbc
from dash import html, dcc # dcc para Store
import pandas as pd
import plotly.io as pio

# --- Carga de Datos Inicial ---
# Cargar datos aquí, fuera de cualquier layout o callback
try:
    df_original = pd.read_csv('RESPONSES_SIPROSA.csv')
    # --- Conversiones de Fecha y Numéricas ---
    df_original['Timestamp'] = pd.to_datetime(df_original['Timestamp'], errors='coerce')
    df_original['FECHA DE LA PRODUCCIÓN'] = pd.to_datetime(df_original.get('FECHA DE LA PRODUCCIÓN'), errors='coerce') # Usar .get para seguridad
    df_original['FECHA DEL SUCESO (INCIDENTE)'] = pd.to_datetime(df_original.get('FECHA DEL SUCESO (INCIDENTE)'), errors='coerce')
    df_original['CANTIDAD PRODUCIDA'] = pd.to_numeric(df_original.get('CANTIDAD PRODUCIDA'), errors='coerce')
    df_original.dropna(subset=['Timestamp'], inplace=True) # Timestamp es vital

    # Calcular fecha máxima una vez
    fecha_maxima_datos = df_original['Timestamp'].max().normalize() if not df_original.empty else pd.Timestamp('now').normalize()
    fecha_maxima_str = fecha_maxima_datos.isoformat() # Guardar como texto ISO para JSON

    # Convertir el DataFrame principal a JSON para el Store
    # Usar 'split' orientation es generalmente eficiente
    data_json = df_original.to_json(date_format='iso', orient='split')
    print(f"Datos cargados. Fecha máx: {fecha_maxima_str}. Tamaño JSON: {len(data_json)} bytes")

except FileNotFoundError:
    print("ERROR CRÍTICO: 'RESPONSES_SIPROSA.csv' no encontrado. Creando datos vacíos.")
    data_json = pd.DataFrame().to_json(date_format='iso', orient='split')
    fecha_maxima_str = pd.Timestamp('now').normalize().isoformat()
except Exception as e:
    print(f"Error cargando datos en app.py: {e}. Creando datos vacíos.")
    data_json = pd.DataFrame().to_json(date_format='iso', orient='split')
    fecha_maxima_str = pd.Timestamp('now').normalize().isoformat()


# --- Configuración de la App ---
BOOTSTRAP_THEME = dbc.themes.CYBORG
pio.templates.default = "plotly_dark"

app = dash.Dash(__name__, external_stylesheets=[BOOTSTRAP_THEME], use_pages=True, suppress_callback_exceptions=True) # suppress_callback_exceptions a veces necesario con stores/pages
server = app.server

# --- Navbar Común ---
navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink(page['name'], href=page["relative_path"]))
        for page in dash.page_registry.values()
    ],
    color="primary",
    dark=True,
    className="mb-4 sticky-top" # Sticky top para que quede fija arriba
)

# --- Layout Principal de la Aplicación ---
app.layout = html.Div([
    # --- Almacenes de Datos (ocultos) ---
    # Almacena el DataFrame principal como JSON
    dcc.Store(id='store-main-data', data=data_json),
    # Almacena la fecha máxima calculada
    dcc.Store(id='store-max-date', data=fecha_maxima_str),
    # Podríamos añadir más stores si fuera necesario para datos pre-calculados

    # --- Elementos Visibles ---
    navbar,
    dash.page_container # Contenedor donde se cargan las páginas
])

# --- Ejecutar la Aplicación ---
if __name__ == '__main__':
    print("Iniciando la aplicación Dash...")
    app.run(debug=True)