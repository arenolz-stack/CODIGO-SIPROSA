# pages/mantenimiento.py

import dash
from dash import dcc, html, Input, Output, callback, State, no_update
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import pandas as pd
from dash.exceptions import PreventUpdate
from datetime import timedelta
import re
import textwrap

# --- Constantes Mantenimiento ---
# Siempre utiliza el archivo RESPONSES_SIPROSA.csv
CSV_FILE = 'RESPONSES_SIPROSA.csv'

COLUMNA_EVENTO = 'TIPO DE EVENTO A REGISTRAR'
COLUMNA_FECHA_MANT = 'FECHA DEL MANTENIMIENTO'
COLUMNA_REALIZO_MANT = '¿SE REALIZÓ MANTENIMIENTO?'
COLUMNA_MAQUINA_MANT = 'MÁQUINA BAJO MANTENIMIENTO'
COLUMNA_TIPO_MANT = 'TIPO DE MANTENIMIENTO REALIZADO'
COLUMNA_HORA_INI_MANT = 'HORA DE INICIO DEL MANTENIMIENTO'
COLUMNA_HORA_FIN_MANT = 'HORA DE FIN DEL MANTENIMIENTO'
COLUMNA_ANOMALIAS_DETECTADAS_BOOL = '¿SE DETECTARON ANOMALÍAS O IRREGULARIDADES EN EL MANTENIMIENTO?'
COLUMNA_ANOMALIAS_DESC = 'DESCRIBA LAS ANOMALIAS DETECTADAS'
COLUMNA_OBSERVACIONES = 'OBSERVACIONES ADICIONALES'

VALOR_MANTENIMIENTO = 'Mantenimiento'
VALOR_SI = 'Sí'
VALOR_NO = 'No'
VALOR_TODAS = 'Todas'

pio.templates.default = "plotly_dark"

# --- Mapeo para Abreviaturas Específicas ---
# Clave: Nombre después de quitar el código. Valor: Abreviatura deseada.
# Añade más mapeos según necesites.
MAPEO_ABREVIATURAS = {
    "Equipo de Ósmosis Inversa de Doble Paso": "EQ. OSM. INV.",
    "Equipo Auxiliar de Refrigeración de la Emblistadora": "EQ. AUX. REFRIG.",
    "Comprimidora / Tableteadora (Nueva)": "COMP./TAB. (Nueva)",
    "Comprimidora / Tableteadora (Anterior)": "COMP./TAB. (Ant.)",
    "Mezcladora en “V”": "MEZCLADORA (V)", # Ejemplo adicional
    # ... añade más si es necesario
}


# --- Registro de la Página ---
dash.register_page(__name__, path='/mantenimiento', title='Detalle Mantenimiento', name='Mantenimiento')

# --- Funciones Auxiliares ---

# (calcular_duracion_horas_mant y format_duracion sin cambios)
def calcular_duracion_horas_mant(fecha_str, hora_ini_str, hora_fin_str):
    try:
        hora_ini_str = str(hora_ini_str).strip().replace('.', '')
        hora_fin_str = str(hora_fin_str).strip().replace('.', '')
        if not hora_ini_str or not hora_fin_str or ':' not in hora_ini_str or ':' not in hora_fin_str: return None
        fecha_base = pd.to_datetime(fecha_str).date()
        t_ini = pd.to_datetime(hora_ini_str, format='%I:%M %p', errors='coerce').time()
        t_fin = pd.to_datetime(hora_fin_str, format='%I:%M %p', errors='coerce').time()
        if pd.isna(t_ini) or pd.isna(t_fin): return None
        dt_ini = pd.Timestamp.combine(fecha_base, t_ini)
        dt_fin = pd.Timestamp.combine(fecha_base, t_fin)
        if dt_fin < dt_ini: dt_fin += timedelta(days=1)
        duracion = dt_fin - dt_ini
        return duracion.total_seconds() / 3600.0
    except Exception: return None

def format_duracion(total_horas):
    if pd.isna(total_horas) or total_horas < 0: return "N/A"
    if total_horas == 0: return "0 min"
    total_minutos = int(round(total_horas * 60))
    horas = total_minutos // 60
    minutos = total_minutos % 60
    if horas > 0 and minutos > 0: return f"{horas} hr {minutos} min"
    elif horas > 0: return f"{horas} hr"
    else: return f"{minutos} min"

# --- Función acortar_nombre_maquina ACTUALIZADA ---
def acortar_nombre_maquina(nombre):
    """Acorta nombre quitando código y aplicando abreviaturas específicas."""
    if pd.isna(nombre): return nombre
    nombre_str = str(nombre).strip()
    # 1. Quitar código
    match = re.split(r'\s*–\s*COD|\s*-\s*COD', nombre_str, maxsplit=1)
    nombre_sin_codigo = match[0].strip() if match else nombre_str

    # 2. Aplicar abreviatura específica si existe
    return MAPEO_ABREVIATURAS.get(nombre_sin_codigo, nombre_sin_codigo)

# (wrap_text sin cambios)
def wrap_text(text, width=20):
    if pd.isna(text): return text
    wrapped_lines = textwrap.wrap(str(text), width=width, break_long_words=True)
    return '<br>'.join(wrapped_lines)


# --- Layout de la Página (Sin cambios) ---
def layout():
    return dbc.Container([
        dbc.Row(dbc.Col(html.H1("Análisis de Mantenimiento", className="text-center display-4 my-4"))),
        # --- Fila 1: Filtros y KPI ---
        dbc.Row([
             dbc.Col(dbc.Card(dbc.CardBody([
                     html.Label('Máquina:', className="card-title mb-2 small"),
                     dcc.Dropdown(id='mant-dropdown-maquina', options=[{'label': VALOR_TODAS, 'value': VALOR_TODAS}], value=VALOR_TODAS, clearable=False, placeholder="Seleccione Máquina...")
             ])), width=12, md=4, className="mb-3"),
             dbc.Col(dbc.Card(dbc.CardBody([
                      html.Label('Rango Fechas Mantenimiento:', className="card-title mb-2 small"),
                      dcc.RangeSlider(id='mant-slider-fechas', marks=None, step=1, tooltip={"placement": "bottom", "always_visible": True}, className="p-0", disabled=True),
                      html.Div(id='mant-output-fechas', className='text-center text-muted small mt-2')
             ])), width=12, md=4, className="mb-3"),
             dbc.Col(dbc.Card(dbc.CardBody([
                 html.H6("Eficiencia: Mantenimientos Correctamente Realizados", className="card-title text-center small mb-2"),
                 dbc.Spinner(html.H3(id='mant-kpi-eficiencia', className="text-center text-success"))
             ])), width=12, md=4, className="mb-3"),
        ], className="align-items-stretch"),
        # --- Fila 2: Gráfico Barras por Máquina ---
        dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody([
                html.H5("Mantenimientos por Máquina", className="card-title text-center"),
                dbc.Spinner(dcc.Graph(id='mant-grafico-barras-maquina', config={'displayModeBar': False}, style={'height': '400px'}))
            ])), width=12, className="mb-3"),
        ]),
        # --- Fila 3: Gráfico Líneas Duración ---
        dbc.Row([
             dbc.Col(dbc.Card(dbc.CardBody([
                html.H5("Tiempo Total Invertido en Mantenimiento (Diario)", className="card-title text-center"),
                dbc.Spinner(dcc.Graph(id='mant-grafico-linea-duracion', config={'displayModeBar': False}, style={'height': '350px'}))
            ])), width=12, className="mb-3")
        ]),
        # --- Fila 4: Tabla Detallada ---
        dbc.Row([
            dbc.Col(html.H4("Registros Detallados de Mantenimiento", className="text-center my-4"))
        ]),
        dbc.Row([
            dbc.Col(dbc.Card(dbc.Spinner(html.Div(id='mant-tabla-detalle'))), width=12)
        ]),
    ], fluid=True, className="dbc mt-4")


# --- Callbacks ---

# Callback de Inicialización (Sin cambios, ya usa acortar_nombre_maquina para labels)
@callback(
    Output('mant-dropdown-maquina', 'options'),
    Output('mant-dropdown-maquina', 'value'),
    Output('mant-slider-fechas', 'min'),
    Output('mant-slider-fechas', 'max'),
    Output('mant-slider-fechas', 'value'),
    Output('mant-slider-fechas', 'disabled'),
    Input('store-main-data', 'data')
)
def inicializar_controles_mantenimiento(data_json_trigger):
    if not data_json_trigger:
        print("Store vacío, esperando datos para inicializar controles de mantenimiento.")
        return [], VALOR_TODAS, 0, 1, [0, 1], True

    default_slider = [0, 1, [0, 1], True]
    default_maq = ([{'label': VALOR_TODAS, 'value': VALOR_TODAS}], VALOR_TODAS)

    try:
        # Siempre utiliza el archivo RESPONSES_SIPROSA.csv
        df = pd.read_csv(CSV_FILE)
        df[COLUMNA_FECHA_MANT] = pd.to_datetime(df.get(COLUMNA_FECHA_MANT), errors='coerce')

        df_mant = df[
            (df[COLUMNA_EVENTO] == VALOR_MANTENIMIENTO) &
            (df.get(COLUMNA_REALIZO_MANT) == VALOR_SI) &
            df[COLUMNA_FECHA_MANT].notna() &
            df[COLUMNA_MAQUINA_MANT].notna() & (df[COLUMNA_MAQUINA_MANT] != '')
        ].copy()

        if df_mant.empty:
            print("No hay datos de mantenimiento válidos para inicializar controles.")
            return default_maq[0], default_maq[1], default_slider[0], default_slider[1], default_slider[2], default_slider[3]

        lista_maquinas = sorted(df_mant[COLUMNA_MAQUINA_MANT].astype(str).str.strip().unique())
        # La función acortar_nombre_maquina ya se aplica aquí para las etiquetas del dropdown
        opciones_maq = [{'label': VALOR_TODAS, 'value': VALOR_TODAS}] + [{'label': acortar_nombre_maquina(maq), 'value': maq} for maq in lista_maquinas]
        valor_maq = VALOR_TODAS

        min_fecha = df_mant[COLUMNA_FECHA_MANT].min()
        max_fecha = df_mant[COLUMNA_FECHA_MANT].max()
        slider_min = min_fecha.toordinal()
        slider_max = max_fecha.toordinal()
        slider_value = [slider_min, slider_max]
        slider_disabled = False

        print(f"Controles de mantenimiento inicializados. Máquinas: {len(lista_maquinas)}. Rango Fechas: {min_fecha.date()} a {max_fecha.date()}")
        return opciones_maq, valor_maq, slider_min, slider_max, slider_value, slider_disabled

    except FileNotFoundError:
        print(f"ERROR CRÍTICO en mantenimiento: Archivo '{CSV_FILE}' no encontrado.")
        return default_maq[0], default_maq[1], default_slider[0], default_slider[1], default_slider[2], default_slider[3]
    except Exception as e:
        print(f"Error inicializando controles de mantenimiento: {e}")
        import traceback
        traceback.print_exc()
        return default_maq[0], default_maq[1], default_slider[0], default_slider[1], default_slider[2], default_slider[3]


# Callback Principal (Aplica acortar_nombre_maquina al gráfico y tabla)
@callback(
    Output('mant-output-fechas', 'children'),
    Output('mant-kpi-eficiencia', 'children'),
    Output('mant-kpi-eficiencia', 'className'),
    Output('mant-grafico-barras-maquina', 'figure'),
    Output('mant-grafico-linea-duracion', 'figure'),
    Output('mant-tabla-detalle', 'children'),
    Input('mant-dropdown-maquina', 'value'),
    Input('mant-slider-fechas', 'value'),
)
def update_maintenance_page(maquina_seleccionada, rango_fechas_slider):

    fig_barras_vacia = go.Figure()
    fig_barras_vacia.update_layout(title_text="Sin datos", xaxis=dict(visible=False), yaxis=dict(visible=False), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=400)
    fig_linea_vacia = go.Figure()
    fig_linea_vacia.update_layout(title_text="Sin datos", xaxis=dict(visible=False), yaxis=dict(visible=False), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=350)
    default_kpi_text = "N/A"
    default_kpi_class = "text-center text-muted" # Clase por defecto gris

    if not rango_fechas_slider or not maquina_seleccionada:
        print("Esperando selección de máquina y/o fechas de mantenimiento.")
        return "Seleccione filtros", default_kpi_text, default_kpi_class, fig_barras_vacia, fig_linea_vacia, html.Div("Seleccione filtros.")

    try:
        # Siempre utiliza el archivo RESPONSES_SIPROSA.csv
        df_original = pd.read_csv(CSV_FILE)
        # (Conversiones...)
        df_original[COLUMNA_FECHA_MANT] = pd.to_datetime(df_original.get(COLUMNA_FECHA_MANT), errors='coerce')
        df_original[COLUMNA_HORA_INI_MANT] = df_original.get(COLUMNA_HORA_INI_MANT, pd.Series(dtype=str)).astype(str).str.strip()
        df_original[COLUMNA_HORA_FIN_MANT] = df_original.get(COLUMNA_HORA_FIN_MANT, pd.Series(dtype=str)).astype(str).str.strip()
        df_original[COLUMNA_MAQUINA_MANT] = df_original.get(COLUMNA_MAQUINA_MANT, pd.Series(dtype=str)).astype(str).str.strip()
        df_original[COLUMNA_ANOMALIAS_DETECTADAS_BOOL] = df_original.get(COLUMNA_ANOMALIAS_DETECTADAS_BOOL, pd.Series(dtype=str)).astype(str).str.strip()

        # (Filtrado...)
        fecha_inicio_dt = pd.Timestamp.fromordinal(rango_fechas_slider[0])
        fecha_fin_dt = pd.Timestamp.fromordinal(rango_fechas_slider[1])
        texto_fechas_slider = f"{fecha_inicio_dt.strftime('%d/%m/%y')} - {fecha_fin_dt.strftime('%d/%m/%y')}"

        df_mant_base = df_original[
            (df_original[COLUMNA_EVENTO] == VALOR_MANTENIMIENTO) &
            (df_original.get(COLUMNA_REALIZO_MANT) == VALOR_SI) &
            (df_original[COLUMNA_FECHA_MANT] >= fecha_inicio_dt) &
            (df_original[COLUMNA_FECHA_MANT] <= fecha_fin_dt)
        ].copy()

        if maquina_seleccionada != VALOR_TODAS:
            df_filtrado = df_mant_base[df_mant_base[COLUMNA_MAQUINA_MANT] == maquina_seleccionada].copy()
        else:
            df_filtrado = df_mant_base.copy()

        if df_filtrado.empty:
            print("No hay datos de mantenimiento para los filtros seleccionados.")
            alert_msg = dbc.Alert("No hay datos de mantenimiento para los filtros seleccionados.", color="warning", className="text-center")
            return texto_fechas_slider, default_kpi_text, default_kpi_class, fig_barras_vacia, fig_linea_vacia, alert_msg

        # (Cálculo y formato duración...)
        df_filtrado['duracion_horas'] = df_filtrado.apply(
            lambda row: calcular_duracion_horas_mant(row[COLUMNA_FECHA_MANT], row[COLUMNA_HORA_INI_MANT], row[COLUMNA_HORA_FIN_MANT]),
            axis=1
        )
        df_filtrado['Duración'] = df_filtrado['duracion_horas'].apply(format_duracion)
        df_calculos = df_filtrado.dropna(subset=['duracion_horas']).copy()
        df_calculos = df_calculos[df_calculos['duracion_horas'] >= 0]

    except FileNotFoundError:
        print(f"ERROR CRÍTICO en mantenimiento: Archivo '{CSV_FILE}' no encontrado.")
        alert_msg = dbc.Alert(f"Error: Archivo '{CSV_FILE}' no encontrado.", color="danger")
        return "Error Archivo", default_kpi_text, default_kpi_class, fig_barras_vacia, fig_linea_vacia, alert_msg
    except Exception as e:
        print(f"Error cargando o filtrando datos de mantenimiento: {e}")
        import traceback
        traceback.print_exc()
        alert_msg = dbc.Alert("Error procesando los datos de mantenimiento.", color="danger")
        return "Error", default_kpi_text, default_kpi_class, fig_barras_vacia, fig_linea_vacia, alert_msg

    # --- Cálculos y Generación de Componentes ---

    # KPI Eficiencia (con lógica de color)
    total_mantenimientos = len(df_filtrado)
    anomalias_si_count = len(df_filtrado[df_filtrado[COLUMNA_ANOMALIAS_DETECTADAS_BOOL] == VALOR_SI])
    if total_mantenimientos > 0:
        porcentaje_sin_anomalias = ((total_mantenimientos - anomalias_si_count) / total_mantenimientos) * 100
        kpi_text = f"{porcentaje_sin_anomalias:.1f}%"
        if porcentaje_sin_anomalias >= 75: kpi_class = "text-center text-success"
        elif porcentaje_sin_anomalias >= 60: kpi_class = "text-center text-warning"
        else: kpi_class = "text-center text-danger"
    else:
        kpi_text = "N/A"
        kpi_class = default_kpi_class

    # Gráfico Barras por Máquina (con nombres acortados y divididos)
    if not df_filtrado.empty:
        conteo_maquina = df_filtrado[COLUMNA_MAQUINA_MANT].value_counts().reset_index()
        conteo_maquina.columns = ['Maquina Original', 'Cantidad']
        # *** Aplicar acortar_nombre_maquina (que ahora incluye abreviaturas) ***
        conteo_maquina['Máquina_Acortada'] = conteo_maquina['Maquina Original'].apply(acortar_nombre_maquina)
        conteo_maquina['Máquina_EjeX'] = conteo_maquina['Máquina_Acortada'].apply(lambda x: wrap_text(x, width=25)) # Ajusta width si es necesario

        fig_barras = px.bar(conteo_maquina.sort_values('Cantidad', ascending=False),
                           x='Máquina_EjeX', y='Cantidad', text='Cantidad',
                           labels={'Máquina_EjeX': 'Máquina', 'Cantidad': 'Nº Mantenimientos'},
                           hover_data={'Máquina_Acortada': True} # Mostrar nombre acortado/abreviado en hover
                           )
        fig_barras.update_xaxes(title_text='')
        fig_barras.update_traces(textposition='outside')
        fig_barras.update_layout(title=None, xaxis_tickangle=0, height=400,
                                 margin=dict(t=10, b=100, l=20, r=10), # Margen inferior aumentado
                                 paper_bgcolor='rgba(0,0,0,0)',
                                 plot_bgcolor='rgba(0,0,0,0)')
    else:
        fig_barras = fig_barras_vacia

    # Gráfico Línea Duración Diaria (sin cambios)
    if not df_calculos.empty:
        duracion_diaria = df_calculos.groupby(df_calculos[COLUMNA_FECHA_MANT].dt.date)['duracion_horas'].sum().reset_index()
        duracion_diaria.rename(columns={COLUMNA_FECHA_MANT: 'Fecha'}, inplace=True)
        fig_linea = px.line(duracion_diaria.sort_values('Fecha'), x='Fecha', y='duracion_horas', markers=True,
                           labels={'Fecha': 'Fecha', 'duracion_horas': 'Horas Totales Mantenimiento'})
        fig_linea.update_traces(marker=dict(size=8))
        fig_linea.update_layout(title=None, height=350, margin=dict(t=10, b=20, l=20, r=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    else:
        fig_linea = fig_linea_vacia

    # Tabla Detallada (aplica acortar_nombre_maquina)
    if not df_filtrado.empty:
        columnas_tabla = [COLUMNA_FECHA_MANT, COLUMNA_MAQUINA_MANT, COLUMNA_TIPO_MANT, COLUMNA_HORA_INI_MANT, COLUMNA_HORA_FIN_MANT, 'Duración', COLUMNA_ANOMALIAS_DETECTADAS_BOOL, COLUMNA_ANOMALIAS_DESC]
        columnas_tabla_existentes = [col for col in columnas_tabla if col in df_filtrado.columns]
        df_tabla = df_filtrado[columnas_tabla_existentes].copy()
        df_tabla.rename(columns={COLUMNA_ANOMALIAS_DETECTADAS_BOOL: 'Anomalías Detectadas?', COLUMNA_ANOMALIAS_DESC: 'Descripción Anomalía'}, inplace=True)
        df_tabla[COLUMNA_FECHA_MANT] = df_tabla[COLUMNA_FECHA_MANT].dt.strftime('%d/%m/%Y')
        # *** Aplicar acortamiento/abreviatura a la columna de máquina en la tabla ***
        if COLUMNA_MAQUINA_MANT in df_tabla.columns:
             df_tabla[COLUMNA_MAQUINA_MANT] = df_tabla[COLUMNA_MAQUINA_MANT].apply(acortar_nombre_maquina)

        try: # Ordenar tabla
             df_tabla[COLUMNA_HORA_INI_MANT + '_time'] = pd.to_datetime(df_tabla[COLUMNA_HORA_INI_MANT].astype(str).str.replace('.', '', regex=False), format='%I:%M %p', errors='coerce').dt.time
             df_tabla['datetime_sort'] = pd.to_datetime(df_filtrado[COLUMNA_FECHA_MANT].dt.strftime('%Y-%m-%d') + ' ' + df_tabla[COLUMNA_HORA_INI_MANT + '_time'].astype(str), errors='coerce')
             df_tabla = df_tabla.sort_values(by='datetime_sort', ascending=True, na_position='last')
             df_tabla = df_tabla.drop(columns=[COLUMNA_HORA_INI_MANT + '_time', 'datetime_sort'], errors='ignore')
        except Exception as e_sort_tabla:
            print(f"Advertencia: No se pudo ordenar la tabla de mantenimiento: {e_sort_tabla}")
        tabla_html = dbc.Table.from_dataframe(df_tabla, striped=True, bordered=True, hover=True, responsive=True, class_name="align-middle")
    else:
        tabla_html = dbc.Alert("No hay registros detallados para mostrar.", color="secondary", className="text-center")

    return texto_fechas_slider, kpi_text, kpi_class, fig_barras, fig_linea, tabla_html