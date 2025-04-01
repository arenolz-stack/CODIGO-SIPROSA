# pages/incidentes.py

import dash
from dash import dcc, html, Input, Output, callback, State, no_update, ctx  # Importar ctx
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta, time, date  # Importar date
import numpy as np
import traceback  # Importar traceback para imprimir errores detallados

# --- Constantes Específicas de Incidentes (Verificar nombres exactos) ---
CSV_FILE = 'RESPONSES_SIPROSA.csv'  # Usar el archivo CSV como referencia para nombres
COLUMNA_TIMESTAMP = 'Timestamp'
COLUMNA_EVENTO = 'TIPO DE EVENTO A REGISTRAR'
# Incidentes
COLUMNA_FECHA_INCID = 'FECHA DEL INCIDENTE o PARADA'
COLUMNA_HORA_INI_INCID = 'HORA DE INICIO DEL INCIDENTE o PARADA'
COLUMNA_HORA_FIN_INCID = 'HORA DE FIN DEL INCIDENTE o PARADA'
COLUMNA_DESC_INCID = 'DESCRIPCIÓN DEL INCIDENTE O PARADA'
COLUMNA_ACCIONES_INCID = 'ACCIONES CORRECTIVAS'
COLUMNA_MAQUINA_INCID = 'MAQUINA ASOCIADA AL INCIDENTE O PARADA'  # Importante para filtrar
VALOR_INCIDENTES = 'Incidentes y Paradas'
# Producción (para gráfico combinado Y MODAL)
COLUMNA_FECHA_PROD = 'FECHA DE LA PRODUCCIÓN'
COLUMNA_MAQUINA_PROD = 'MAQUINA UTILIZADA'
COLUMNA_CANTIDAD = 'CANTIDAD PRODUCIDA'
COLUMNA_UNIDAD = 'UNIDAD DE MEDIDA'
COLUMNA_HUBO_PRODUCCION = '¿HUBO PRODUCCIÓN?'
COLUMNA_PRODUCTO = 'PRODUCTO PRODUCIDO'
VALOR_PRODUCCION = 'Producción'
VALOR_SI_PRODUCCION = 'Sí'
# Mantenimiento (para gráfico combinado)
COLUMNA_FECHA_MANT = 'FECHA DEL MANTENIMIENTO'
COLUMNA_MAQUINA_MANT = 'MÁQUINA BAJO MANTENIMIENTO'
COLUMNA_TIPO_MANT = 'TIPO DE MANTENIMIENTO REALIZADO'
COLUMNA_REALIZO_MANTENIMIENTO = '¿SE REALIZÓ MANTENIMIENTO?'
VALOR_MANTENIMIENTO = 'Mantenimiento'
VALOR_SI_MANTENIMIENTO = 'Sí'
# Valor Común Dropdown
VALOR_TODAS = 'Todas'

# --- Registro de la Página ---
dash.register_page(__name__, path='/incidentes', title='Incidentes y Paradas', name='Incidentes')

# --- Funciones Auxiliares ---
def calcular_duracion(inicio_str, fin_str, fecha_str):
    """Calcula la duración en minutos entre dos horas en formato texto."""
    if pd.isna(inicio_str) or pd.isna(fin_str) or pd.isna(fecha_str):
        return None
    try:
        fecha = pd.to_datetime(fecha_str).date()
        try:
            inicio_dt = datetime.combine(fecha, pd.to_datetime(inicio_str, format='%I:%M %p').time())
            fin_dt = datetime.combine(fecha, pd.to_datetime(fin_str, format='%I:%M %p').time())
        except ValueError:
            inicio_dt = datetime.combine(fecha, pd.to_datetime(inicio_str, format='%H:%M').time())
            fin_dt = datetime.combine(fecha, pd.to_datetime(fin_str, format='%H:%M').time())
        if fin_dt < inicio_dt:
            fin_dt += timedelta(days=1)
        duracion = (fin_dt - inicio_dt).total_seconds() / 60
        return round(duracion)
    except Exception:
        return None

def parse_time_robust(time_str):
    """Intenta parsear formatos de hora comunes."""
    if pd.isna(time_str):
        return None
    try:
        return pd.to_datetime(time_str, format='%I:%M %p').time()
    except ValueError:
        try:
            return pd.to_datetime(time_str, format='%H:%M').time()
        except ValueError:
            return None

# --- Layout Helper ---
def layout():
    return dbc.Container([
        dbc.Row(dbc.Col(html.H1("Análisis de Incidentes y Paradas", className="text-center display-4 my-4"))),
        dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody([
                html.Label('Rango Fechas (Incidentes):', className="card-title mb-2"),
                dcc.RangeSlider(id='incid-slider-fechas', marks=None, step=1, tooltip={"placement": "bottom", "always_visible": True}, className="p-0", disabled=True),
                html.Div(id='incid-output-fechas', className='text-center text-muted small mt-2')
            ])), width=12, md=6, className="mb-3"),
            dbc.Col(dbc.Card(dbc.CardBody([
                html.Label('Filtrar por Máquina (General):', className="card-title mb-2"),
                dcc.Dropdown(id='incid-dropdown-maquina-general', clearable=False, placeholder="Cargando...", value=VALOR_TODAS)
            ])), width=12, md=6, className="mb-3"),
        ], className="align-items-stretch"),
        dbc.Row([
            dbc.Col(dbc.Card(dbc.Spinner(dcc.Graph(id='incid-grafico-frecuencia', config={'displayModeBar': False}, clear_on_unhover=True))), width=12, md=6, className="mb-3"),
            dbc.Col(dbc.Card([
                 dbc.CardHeader("Detalle de Incidentes Filtrados"),
                 dbc.CardBody(dbc.Spinner(html.Div(id='incid-tabla-detalles')), style={'maxHeight': '400px', 'overflowY': 'auto'})
            ]), width=12, md=6, className="mb-3"),
        ], className="align-items-stretch"),
        html.Hr(),
        dbc.Row(dbc.Col(html.H2("Análisis por Máquina: Producción vs. Eventos", className="text-center my-4"))),
        dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody([
                html.Label('Seleccione Máquina para Análisis Detallado:', className="card-title mb-2"),
                dcc.Dropdown(id='incid-dropdown-maquina-especifica', clearable=False, placeholder="Cargando...")
            ])), width=12, className="mb-3"),
        ]),
        dbc.Row([
            dbc.Col(dbc.Card(dbc.Spinner(dcc.Graph(id='incid-grafico-combinado', config={'displayModeBar': True}))), width=12)
        ], className="mb-4"),
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle(id='incid-modal-titulo')),
            dbc.ModalBody(id='incid-modal-contenido')
        ], id="incid-modal-detalle-dia", size="lg", is_open=False, scrollable=True),
    ], fluid=True, className="dbc mt-4")

# --- Callbacks ---

# Callback para inicializar controles de esta página
@callback(
    Output('incid-dropdown-maquina-general', 'options'),
    Output('incid-dropdown-maquina-general', 'value'),
    Output('incid-dropdown-maquina-especifica', 'options'),
    Output('incid-dropdown-maquina-especifica', 'value'),
    Output('incid-slider-fechas', 'min'),
    Output('incid-slider-fechas', 'max'),
    Output('incid-slider-fechas', 'value'),
    Output('incid-slider-fechas', 'disabled'),
    Input('store-main-data', 'data')  # Disparado por el store
)
def inicializar_controles_incidentes(data_json):
    if not data_json:
        default_slider = [0, 1, [0, 1], True]
        default_maq_opts = [{'label': VALOR_TODAS, 'value': VALOR_TODAS}]
        return default_maq_opts, VALOR_TODAS, [], None, default_slider[0], default_slider[1], default_slider[2], default_slider[3]
    try:
        df = pd.read_json(data_json, orient='split')
        date_cols = [COLUMNA_TIMESTAMP, COLUMNA_FECHA_PROD, COLUMNA_FECHA_MANT, COLUMNA_FECHA_INCID]
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        if COLUMNA_CANTIDAD in df.columns:
            df[COLUMNA_CANTIDAD] = pd.to_numeric(df[COLUMNA_CANTIDAD], errors='coerce')

        maq_cols = [COLUMNA_MAQUINA_PROD, COLUMNA_MAQUINA_MANT, COLUMNA_MAQUINA_INCID]
        all_maquinas = set()
        for col in maq_cols:
            if col in df.columns:
                all_maquinas.update(df[col].dropna().unique())
        lista_maquinas_sorted = sorted(list(all_maquinas))
        opciones_maquina_general = [{'label': VALOR_TODAS, 'value': VALOR_TODAS}] + [{'label': maq, 'value': maq} for maq in lista_maquinas_sorted]
        opciones_maquina_especifica = [{'label': maq, 'value': maq} for maq in lista_maquinas_sorted]
        valor_inicial_maquina_especifica = lista_maquinas_sorted[0] if lista_maquinas_sorted else None

        fechas_incidentes = df[COLUMNA_FECHA_INCID].dropna() if COLUMNA_FECHA_INCID in df.columns else pd.Series(dtype='datetime64[ns]')
        if not fechas_incidentes.empty:
            min_fecha = fechas_incidentes.min()
            max_fecha = fechas_incidentes.max()
            slider_min = min_fecha.toordinal()
            slider_max = max_fecha.toordinal()
            slider_value = [slider_min, slider_max]
            slider_disabled = False
        else:
            fechas_timestamp = df[COLUMNA_TIMESTAMP].dropna() if COLUMNA_TIMESTAMP in df.columns else pd.Series(dtype='datetime64[ns]')
            if not fechas_timestamp.empty:
                min_fecha = fechas_timestamp.min()
                max_fecha = fechas_timestamp.max()
                slider_min = min_fecha.toordinal()
                slider_max = max_fecha.toordinal()
                slider_value = [slider_min, slider_max]
                slider_disabled = False
            else:
                slider_min, slider_max, slider_value, slider_disabled = 0, 1, [0, 1], True

        return (opciones_maquina_general, VALOR_TODAS,
                opciones_maquina_especifica, valor_inicial_maquina_especifica,
                slider_min, slider_max, slider_value, slider_disabled)
    except Exception as e:
        print(f"!!!!!! ERROR en inicializar_controles_incidentes: {e}")
        traceback.print_exc()
        default_slider = [0, 1, [0, 1], True]
        default_maq_opts = [{'label': VALOR_TODAS, 'value': VALOR_TODAS}]
        return default_maq_opts, VALOR_TODAS, [], None, default_slider[0], default_slider[1], default_slider[2], default_slider[3]

# Callback para actualizar gráficos y tabla general de incidentes
@callback(
    Output('incid-grafico-frecuencia', 'figure'),
    Output('incid-tabla-detalles', 'children'),
    Output('incid-output-fechas', 'children'),
    Input('incid-slider-fechas', 'value'),
    Input('incid-dropdown-maquina-general', 'value'),
    Input('incid-grafico-frecuencia', 'clickData'),
    State('store-main-data', 'data')
)
def update_incidentes_generales(rango_fechas_slider, maquina_seleccionada, clickData, data_json):
    trigger_id = ctx.triggered_id if ctx.triggered else 'N/A'
    print(f"\n--- update_incidentes_generales triggered by: {trigger_id} ---")

    if not data_json or rango_fechas_slider is None:
        return px.bar(title="Esperando datos..."), html.Div("Cargando..."), "..."
    try:
        df_original = pd.read_json(data_json, orient='split')
        date_cols = [COLUMNA_TIMESTAMP, COLUMNA_FECHA_PROD, COLUMNA_FECHA_MANT, COLUMNA_FECHA_INCID]
        for col in date_cols:
            if col in df_original.columns:
                df_original[col] = pd.to_datetime(df_original[col], errors='coerce')
        if COLUMNA_FECHA_INCID not in df_original.columns:
             return px.bar(title=f"Error: Falta columna '{COLUMNA_FECHA_INCID}'"), html.Div(f"Error: Falta columna '{COLUMNA_FECHA_INCID}'"), "Error"
        df_incidentes = df_original[df_original[COLUMNA_FECHA_INCID].notna()].copy()
    except Exception as e:
        print(f"!!!!!! ERROR leyendo/parseando datos del store en update_incidentes_generales: {e}")
        traceback.print_exc()
        return px.bar(title="Error al cargar datos"), html.Div("Error al cargar datos."), "Error"

    df_filtrado_base = pd.DataFrame(columns=df_incidentes.columns)
    texto_fechas_slider = "..."
    try:
        fecha_inicio_dt = pd.Timestamp.fromordinal(rango_fechas_slider[0])
        fecha_fin_dt = pd.Timestamp.fromordinal(rango_fechas_slider[1])
        texto_fechas_slider = f"{fecha_inicio_dt.strftime('%d/%m/%y')} - {fecha_fin_dt.strftime('%d/%m/%y')}"
        df_filtrado_base = df_incidentes[
            (df_incidentes[COLUMNA_FECHA_INCID] >= fecha_inicio_dt) &
            (df_incidentes[COLUMNA_FECHA_INCID] <= fecha_fin_dt)
        ].copy()
        if maquina_seleccionada and maquina_seleccionada != VALOR_TODAS:
             if COLUMNA_MAQUINA_INCID in df_filtrado_base.columns:
                  df_filtrado_base = df_filtrado_base[df_filtrado_base[COLUMNA_MAQUINA_INCID] == maquina_seleccionada].copy()
             else:
                  df_filtrado_base = pd.DataFrame(columns=df_incidentes.columns)
    except Exception as e:
        print(f"!!!!!! ERROR durante el filtrado base: {e}")
        traceback.print_exc()
        return px.bar(title="Error en filtros"), html.Div("Error al aplicar filtros."), "Error"

    fig_frecuencia = px.bar(title="No hay incidentes en el período/máquina seleccionada")
    fig_frecuencia.update_layout(height=400, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    if not df_filtrado_base.empty:
        incidentes_por_dia = df_filtrado_base.groupby(df_filtrado_base[COLUMNA_FECHA_INCID].dt.date).size().reset_index(name='Cantidad Incidentes')
        incidentes_por_dia.rename(columns={COLUMNA_FECHA_INCID: 'Fecha'}, inplace=True)
        incidentes_por_dia = incidentes_por_dia.sort_values(by='Fecha')
        fig_frecuencia = px.bar(incidentes_por_dia, x='Fecha', y='Cantidad Incidentes',
                                title="Frecuencia de Incidentes por Día",
                                labels={'Fecha': 'Fecha', 'Cantidad Incidentes': 'Nº Incidentes'})
        fig_frecuencia.update_layout(height=400, title_x=0.5, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        fig_frecuencia.update_traces(marker_color='#FF6347')

    df_para_tabla = df_filtrado_base.copy()
    clicked_date = None

    if trigger_id == 'incid-grafico-frecuencia' and clickData:
        try:
            clicked_date_str = clickData['points'][0]['x']
            clicked_date = datetime.strptime(clicked_date_str, '%Y-%m-%d').date()
            print(f"   Click detectado en gráfico. Fecha clickeada: {clicked_date}")
            df_para_tabla = df_filtrado_base[df_filtrado_base[COLUMNA_FECHA_INCID].dt.date == clicked_date].copy()
            print(f"   df_para_tabla (después de click) shape: {df_para_tabla.shape}")
        except (KeyError, IndexError, ValueError, TypeError) as e:
            print(f"   WARN: No se pudo extraer la fecha del clickData: {e}. Mostrando tabla sin filtro de click.")

    # Separar la parte condicional de la f-string
    date_str = f" para la fecha {clicked_date.strftime('%d/%m/%Y')}" if clicked_date else ""
    tabla_html = html.Div(f"No hay detalles de incidentes para mostrar{date_str}.")
    if not df_para_tabla.empty:
        if COLUMNA_HORA_INI_INCID in df_para_tabla.columns and COLUMNA_HORA_FIN_INCID in df_para_tabla.columns:
            df_para_tabla['Duración (min)'] = df_para_tabla.apply(
                lambda row: calcular_duracion(row.get(COLUMNA_HORA_INI_INCID), row.get(COLUMNA_HORA_FIN_INCID), row.get(COLUMNA_FECHA_INCID)),
                axis=1
            )
            df_para_tabla['Duración (min)'] = df_para_tabla['Duración (min)'].apply(lambda x: f"{int(x)}" if pd.notna(x) else "N/A")
        columnas_tabla = {
            COLUMNA_FECHA_INCID: 'Fecha', COLUMNA_MAQUINA_INCID: 'Máquina',
            COLUMNA_DESC_INCID: 'Descripción', 'Duración (min)': 'Duración (min)',
            COLUMNA_ACCIONES_INCID: 'Acciones Correctivas'
        }
        columnas_existentes = {k: v for k, v in columnas_tabla.items() if k in df_para_tabla.columns}
        df_display = df_para_tabla[list(columnas_existentes.keys())].copy()
        df_display.rename(columns=columnas_existentes, inplace=True)
        if 'Fecha' in df_display.columns:
             df_display['Fecha'] = pd.to_datetime(df_display['Fecha']).dt.strftime('%d/%m/%Y')
        try:
            df_display = df_display.sort_values(by='Fecha')
        except Exception as e_sort:
                 print(f"WARN: Error al ordenar tabla: {e_sort}")

        tabla_html = dbc.Table.from_dataframe(df_display, striped=True, bordered=True, hover=True, responsive=True, class_name="align-middle small")

    return fig_frecuencia, tabla_html, texto_fechas_slider

# Callback para actualizar el gráfico combinado por máquina
@callback(
    Output('incid-grafico-combinado', 'figure'),
    Input('incid-slider-fechas', 'value'),
    Input('incid-dropdown-maquina-especifica', 'value'),
    State('store-main-data', 'data')
)
def update_grafico_combinado_maquina(rango_fechas_slider, maquina_seleccionada, data_json):
    if not data_json or not maquina_seleccionada or rango_fechas_slider is None:
        fig = go.Figure()
        fig.update_layout(title="Seleccione una máquina y rango de fechas", title_x=0.5, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        return fig
    try:
        df_original = pd.read_json(data_json, orient='split')
        date_cols = [COLUMNA_TIMESTAMP, COLUMNA_FECHA_PROD, COLUMNA_FECHA_MANT, COLUMNA_FECHA_INCID]
        for col in date_cols:
            if col in df_original.columns:
                df_original[col] = pd.to_datetime(df_original[col], errors='coerce')
        if COLUMNA_CANTIDAD in df_original.columns:
            df_original[COLUMNA_CANTIDAD] = pd.to_numeric(df_original[COLUMNA_CANTIDAD], errors='coerce')

        fecha_inicio_dt = pd.Timestamp.fromordinal(rango_fechas_slider[0])
        fecha_fin_dt = pd.Timestamp.fromordinal(rango_fechas_slider[1])
        rango_completo_fechas = pd.date_range(start=fecha_inicio_dt, end=fecha_fin_dt, freq='D')

        # --- 1. Datos de Producción ---
        df_prod = pd.DataFrame()
        prod_cols_req = [COLUMNA_EVENTO, COLUMNA_HUBO_PRODUCCION, COLUMNA_MAQUINA_PROD, COLUMNA_FECHA_PROD, COLUMNA_CANTIDAD, COLUMNA_UNIDAD]
        if all(col in df_original.columns for col in prod_cols_req):
            df_prod = df_original[
                (df_original[COLUMNA_EVENTO] == VALOR_PRODUCCION) &
                (df_original[COLUMNA_HUBO_PRODUCCION] == VALOR_SI_PRODUCCION) &
                (df_original[COLUMNA_MAQUINA_PROD] == maquina_seleccionada) &
                (df_original[COLUMNA_FECHA_PROD].notna()) &
                (df_original[COLUMNA_CANTIDAD].notna()) &
                (df_original[COLUMNA_FECHA_PROD] >= fecha_inicio_dt) &
                (df_original[COLUMNA_FECHA_PROD] <= fecha_fin_dt)
            ].copy()

        produccion_diaria = pd.DataFrame({'Fecha': rango_completo_fechas, 'Produccion': 0.0})
        if not df_prod.empty:
             df_prod[COLUMNA_CANTIDAD] = pd.to_numeric(df_prod[COLUMNA_CANTIDAD], errors='coerce')
             df_prod.dropna(subset=[COLUMNA_CANTIDAD], inplace=True)
             if not df_prod.empty:
                 prod_agrupada = df_prod.groupby(df_prod[COLUMNA_FECHA_PROD].dt.normalize())[COLUMNA_CANTIDAD].sum().reset_index()
                 prod_agrupada.rename(columns={COLUMNA_FECHA_PROD: 'Fecha', COLUMNA_CANTIDAD: 'Produccion'}, inplace=True)
                 produccion_diaria = pd.merge(produccion_diaria[['Fecha']], prod_agrupada, on='Fecha', how='left').fillna(0.0)
        unidad_prod = df_prod[COLUMNA_UNIDAD].iloc[0] if not df_prod.empty and not df_prod[COLUMNA_UNIDAD].dropna().empty else "Unidades"

        # --- 2. Datos de Incidentes ---
        df_incid = pd.DataFrame()
        incid_cols_req = [COLUMNA_FECHA_INCID, COLUMNA_MAQUINA_INCID]
        if all(col in df_original.columns for col in incid_cols_req):
             df_incid = df_original[
                  (df_original[COLUMNA_FECHA_INCID].notna()) &
                  (df_original[COLUMNA_MAQUINA_INCID] == maquina_seleccionada) &
                  (df_original[COLUMNA_FECHA_INCID] >= fecha_inicio_dt) &
                  (df_original[COLUMNA_FECHA_INCID] <= fecha_fin_dt)
             ].copy()
        fechas_con_incidentes = df_incid[COLUMNA_FECHA_INCID].dt.normalize().unique() if not df_incid.empty else []

        # --- 3. Datos de Mantenimiento ---
        df_mant = pd.DataFrame()
        mant_cols_req = [COLUMNA_EVENTO, COLUMNA_REALIZO_MANTENIMIENTO, COLUMNA_MAQUINA_MANT, COLUMNA_FECHA_MANT]
        if all(col in df_original.columns for col in mant_cols_req):
            df_mant = df_original[
                (df_original[COLUMNA_EVENTO] == VALOR_MANTENIMIENTO) &
                (df_original[COLUMNA_REALIZO_MANTENIMIENTO] == VALOR_SI_MANTENIMIENTO) &
                (df_original[COLUMNA_MAQUINA_MANT] == maquina_seleccionada) &
                (df_original[COLUMNA_FECHA_MANT].notna()) &
                (df_original[COLUMNA_FECHA_MANT] >= fecha_inicio_dt) &
                (df_original[COLUMNA_FECHA_MANT] <= fecha_fin_dt)
            ].copy()
        fechas_con_mantenimiento = df_mant[COLUMNA_FECHA_MANT].dt.normalize().unique() if not df_mant.empty else []

        # --- Creación del Gráfico ---
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=produccion_diaria['Fecha'], y=produccion_diaria['Produccion'],
            mode='lines+markers', name=f'Producción ({unidad_prod})',
            line=dict(color='green', width=2), marker=dict(size=5), yaxis='y1'
        ))
        incid_y_val = 1
        fechas_incidentes_plot = [fecha for fecha in fechas_con_incidentes if fecha in produccion_diaria['Fecha'].values]
        if fechas_incidentes_plot:
             fig.add_trace(go.Scatter(
                  x=fechas_incidentes_plot, y=[incid_y_val] * len(fechas_incidentes_plot),
                  mode='markers', name='Incidentes',
                  marker=dict(color='red', size=10, symbol='x'), yaxis='y2'
             ))
        maint_y_val = 0.5
        fechas_mantenimiento_plot = [fecha for fecha in fechas_con_mantenimiento if fecha in produccion_diaria['Fecha'].values]
        if fechas_mantenimiento_plot:
             fig.add_trace(go.Scatter(
                  x=fechas_mantenimiento_plot, y=[maint_y_val] * len(fechas_mantenimiento_plot),
                  mode='markers', name='Mantenimiento',
                  marker=dict(color='orange', size=10, symbol='triangle-up'), yaxis='y2'
             ))

        fig.update_layout(
            title=f"Producción vs. Eventos - Máquina: {maquina_seleccionada}",
            title_x=0.5,
            xaxis_title="Fecha",
            yaxis=dict(
                title=dict(text=f"Producción ({unidad_prod})", font=dict(color="green")),
                tickfont=dict(color="green"),
                side='left',
                rangemode='tozero'
            ),
            yaxis2=dict(
                title=dict(text="Eventos", font=dict(color="gray")),
                tickfont=dict(color="gray"),
                overlaying='y',
                side='right',
                range=[-0.1, 1.5],
                showgrid=False,
                showticklabels=False
            ),
            legend_title_text='Leyenda',
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
            height=500,
            hovermode='x unified',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(
                range=[rango_completo_fechas.min() - timedelta(days=1), rango_completo_fechas.max() + timedelta(days=1)]
            )
        )
        return fig

    except Exception as e:
        print(f"!!!!!! ERROR generando gráfico combinado: {e}")
        traceback.print_exc()
        fig = go.Figure()
        fig.update_layout(title=f"Error al generar gráfico para {maquina_seleccionada}", title_x=0.5, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        return fig

# Callback para mostrar el resumen diario en el modal
@callback(
    Output('incid-modal-detalle-dia', 'is_open'),
    Output('incid-modal-titulo', 'children'),
    Output('incid-modal-contenido', 'children'),
    Input('incid-grafico-combinado', 'clickData'),
    State('incid-dropdown-maquina-especifica', 'value'),
    State('store-main-data', 'data'),
    prevent_initial_call=True
)
def mostrar_resumen_diario_modal(clickData, maquina_seleccionada, data_json):
    if clickData is None or not maquina_seleccionada or not data_json:
        raise dash.exceptions.PreventUpdate
    try:
        fecha_click_str = clickData['points'][0]['x']
        fecha_click = pd.to_datetime(fecha_click_str).normalize()
        df_original = pd.read_json(data_json, orient='split')
        date_cols = [COLUMNA_TIMESTAMP, COLUMNA_FECHA_PROD, COLUMNA_FECHA_MANT, COLUMNA_FECHA_INCID]
        for col in date_cols:
            if col in df_original.columns:
                df_original[col] = pd.to_datetime(df_original[col], errors='coerce')
        if COLUMNA_CANTIDAD in df_original.columns:
            df_original[COLUMNA_CANTIDAD] = pd.to_numeric(df_original[COLUMNA_CANTIDAD], errors='coerce')

        resumen_elementos = []
        modal_titulo = f"Resumen del {fecha_click.strftime('%d/%m/%Y')} - Máquina: {maquina_seleccionada}"

        # 1. Producción del día
        df_prod_dia = pd.DataFrame()
        prod_cols_req_modal = [COLUMNA_EVENTO, COLUMNA_HUBO_PRODUCCION, COLUMNA_MAQUINA_PROD, COLUMNA_FECHA_PROD, COLUMNA_PRODUCTO, COLUMNA_CANTIDAD, COLUMNA_UNIDAD]
        if all(col in df_original.columns for col in prod_cols_req_modal):
            df_prod_dia = df_original[
                (df_original[COLUMNA_EVENTO] == VALOR_PRODUCCION) &
                (df_original[COLUMNA_HUBO_PRODUCCION] == VALOR_SI_PRODUCCION) &
                (df_original[COLUMNA_MAQUINA_PROD] == maquina_seleccionada) &
                (df_original[COLUMNA_FECHA_PROD].notna()) &
                (df_original[COLUMNA_FECHA_PROD].dt.normalize() == fecha_click)
            ]
        if not df_prod_dia.empty:
            resumen_elementos.append(html.H5("Producción", className="mt-3"))
            for idx, row in df_prod_dia.iterrows():
                 cantidad_fmt = f"{row.get(COLUMNA_CANTIDAD, 0):,}" if pd.notna(row.get(COLUMNA_CANTIDAD)) else 'N/A'
                 prod_info = f"- {row.get(COLUMNA_PRODUCTO, 'N/A')}: {cantidad_fmt} {row.get(COLUMNA_UNIDAD, 'Unid.')}"
                 resumen_elementos.append(html.P(prod_info))
        else:
             resumen_elementos.append(html.P("No hubo producción registrada para esta máquina este día."))

        # 2. Incidentes del día
        df_incid_dia = pd.DataFrame()
        incid_cols_req_modal = [COLUMNA_FECHA_INCID, COLUMNA_MAQUINA_INCID, COLUMNA_HORA_INI_INCID, COLUMNA_HORA_FIN_INCID, COLUMNA_DESC_INCID, COLUMNA_ACCIONES_INCID]
        if all(col in df_original.columns for col in incid_cols_req_modal):
             df_incid_dia = df_original[
                (df_original[COLUMNA_FECHA_INCID].notna()) &
                (df_original[COLUMNA_MAQUINA_INCID] == maquina_seleccionada) &
                (df_original[COLUMNA_FECHA_INCID].dt.normalize() == fecha_click)
             ]
        if not df_incid_dia.empty:
            resumen_elementos.append(html.H5("Incidentes/Paradas", className="mt-3"))
            for idx, row in df_incid_dia.iterrows():
                hora_ini = row.get(COLUMNA_HORA_INI_INCID, 'N/A')
                hora_fin = row.get(COLUMNA_HORA_FIN_INCID, 'N/A')
                desc = row.get(COLUMNA_DESC_INCID, 'Sin descripción')
                acc = row.get(COLUMNA_ACCIONES_INCID, 'N/A')
                duracion = calcular_duracion(hora_ini, hora_fin, fecha_click)
                dur_str = f"({int(duracion)} min)" if duracion is not None else ""
                incid_info = [ html.Strong(f"- {hora_ini} a {hora_fin} {dur_str}: "), f"{desc}", html.Br(), html.Em(f"  Acciones: {acc}") if pd.notna(acc) else "" ]
                resumen_elementos.append(html.P(incid_info))
        else:
            resumen_elementos.append(html.P("No se registraron incidentes para esta máquina este día."))

        # 3. Mantenimientos del día
        df_mant_dia = pd.DataFrame()
        mant_cols_req_modal = [COLUMNA_EVENTO, COLUMNA_REALIZO_MANTENIMIENTO, COLUMNA_MAQUINA_MANT, COLUMNA_FECHA_MANT, COLUMNA_TIPO_MANT, 'DESCRIPCIÓN DEL MANTENIMIENTO REALIZADO']
        if all(col in df_original.columns for col in mant_cols_req_modal):
             df_mant_dia = df_original[
                (df_original[COLUMNA_EVENTO] == VALOR_MANTENIMIENTO) &
                (df_original[COLUMNA_REALIZO_MANTENIMIENTO] == VALOR_SI_MANTENIMIENTO) &
                (df_original[COLUMNA_MAQUINA_MANT] == maquina_seleccionada) &
                (df_original[COLUMNA_FECHA_MANT].notna()) &
                (df_original[COLUMNA_FECHA_MANT].dt.normalize() == fecha_click)
             ]
        if not df_mant_dia.empty:
            resumen_elementos.append(html.H5("Mantenimiento", className="mt-3"))
            for idx, row in df_mant_dia.iterrows():
                 tipo = row.get(COLUMNA_TIPO_MANT, 'N/A')
                 desc_mant = row.get('DESCRIPCIÓN DEL MANTENIMIENTO REALIZADO', 'Sin descripción')
                 mant_info = f"- Tipo: {tipo} | Descripción: {desc_mant}"
                 resumen_elementos.append(html.P(mant_info))
        else:
            resumen_elementos.append(html.P("No se realizó mantenimiento registrado para esta máquina este día."))

        modal_contenido = html.Div(resumen_elementos)
        return True, modal_titulo, modal_contenido

    except Exception as e:
        print(f"!!!!!! ERROR al procesar click para modal: {e}")
        traceback.print_exc()
        modal_titulo = "Error"
        modal_contenido = html.Div(f"No se pudo cargar el resumen para {fecha_click_str}. Error: {e}")
        return True, modal_titulo, modal_contenido
