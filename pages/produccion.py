# pages/produccion.py

import dash
from dash import dcc, html, Input, Output, callback, State, no_update
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import pandas as pd
from dash.exceptions import PreventUpdate
from datetime import timedelta

# --- Constantes (Asegúrate que coincidan con tu CSV y home.py) ---
# Siempre utiliza el archivo RESPONSES_SIPROSA.csv
CSV_FILE = 'RESPONSES_SIPROSA.csv'

COLUMNA_TIMESTAMP = 'Timestamp'
COLUMNA_EVENTO = 'TIPO DE EVENTO A REGISTRAR'
COLUMNA_FECHA_PROD = 'FECHA DE LA PRODUCCIÓN'
COLUMNA_HUBO_PRODUCCION = '¿HUBO PRODUCCIÓN?'
COLUMNA_MAQUINA_PROD = 'MAQUINA UTILIZADA'
COLUMNA_PRODUCTO = 'PRODUCTO PRODUCIDO'
COLUMNA_UNIDAD = 'UNIDAD DE MEDIDA'
COLUMNA_CANTIDAD = 'CANTIDAD PRODUCIDA'
COLUMNA_HORA_INI_PROD = 'HORA DE INICIO DE LA PRODUCCÓN'
COLUMNA_HORA_FIN_PROD = 'HORA DE FIN DE LA PRODUCCÓN'

VALOR_PRODUCCION = 'Producción'
VALOR_SI_PRODUCCION = 'Sí'
VALOR_TODOS = 'Todos'

pio.templates.default = "plotly_dark"

# --- Colores Consistentes para Unidades ---
# Define colores específicos para unidades comunes. Puedes añadir más si es necesario.
# Usando colores de Plotly para buena diferenciación.
MAPA_COLORES_UNIDADES = {
    'Comprimidos': px.colors.qualitative.Plotly[0],
    'Kilogramos': px.colors.qualitative.Plotly[1],
    'Blisters': px.colors.qualitative.Plotly[2],
    'Litros': px.colors.qualitative.Plotly[3],
    # Añade más unidades y colores si aparecen en tus datos
    'Default': px.colors.qualitative.Plotly[9] # Color por defecto para unidades no mapeadas
}

# --- Registro de la Página ---
dash.register_page(__name__, path='/produccion', title='Detalle Producción', name='Producción')

# --- Layout Helper (Reorganizado) ---
def layout():
    return dbc.Container([
        dbc.Row(dbc.Col(html.H1("Detalle de Producción", className="text-center display-4 my-4"))),
        dbc.Row([
             dbc.Col(dbc.Card(dbc.CardBody([
                     html.Label('Producto:', className="card-title mb-2"),
                     dcc.Dropdown(id='prod-dropdown-producto', clearable=False, placeholder="Cargando...")
             ])), width=12, md=6, className="mb-3"),
             dbc.Col(dbc.Card(dbc.CardBody([
                      html.Label('Rango Fechas Producción:', className="card-title mb-2"),
                      dcc.RangeSlider(id='prod-slider-fechas', marks=None, step=1, tooltip={"placement": "bottom", "always_visible": True}, className="p-0", disabled=True),
                      html.Div(id='prod-output-fechas', className='text-center text-muted small mt-2')
             ])), width=12, md=6, className="mb-3")
        ], className="align-items-stretch"),

        # Fila para el Gráfico Comparativo (ancho completo)
        dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody([
                html.H5("Producción Total por Máquina y Unidad", className="card-title text-center mb-3"),
                dbc.Spinner(dcc.Graph(id='prod-grafico-barras-maquinas', config={'displayModeBar': False}))
            ])), width=12, className="mb-3") # Ocupa todo el ancho
        ]),

        # Fila para Gráficos de Serie Temporal por Máquina (cada gráfico ancho completo)
        dbc.Row([
            dbc.Col(html.H4("Evolución Diaria por Máquina", className="text-center my-4"))
        ]),
        dbc.Spinner(dbc.Row(id='prod-contenedor-graficos-linea', className="g-3")), # Se llenará con cols width=12

        # Fila para KPIs de Eficiencia (debajo de los gráficos de línea)
        dbc.Row([
             dbc.Col(html.H4("Eficiencia Promedio por Hora", className="text-center my-4"))
        ]),
        dbc.Row([
            # Envolver los KPIs en una Col para centrar o aplicar estilos si es necesario
            dbc.Col(dbc.Spinner(html.Div(id='prod-kpis-eficiencia', className="d-flex flex-wrap justify-content-center gap-3")), width=12) # flex-wrap y gap para mejor distribución
        ], className="mb-3"),


        # Fila para la Tabla Detallada
        dbc.Row([
            dbc.Col(html.H4("Registros Detallados", className="text-center my-4"))
        ]),
        dbc.Row([
            dbc.Col(dbc.Card(dbc.Spinner(html.Div(id='prod-tabla-detalle'))), width=12)
        ]),

    ], fluid=True, className="dbc mt-4")


# --- Funciones Auxiliares para Cálculo de Duración ---
# (Sin cambios)
def calcular_duracion_horas(fecha_str, hora_ini_str, hora_fin_str):
    try:
        fecha_base = pd.to_datetime(fecha_str).date()
        hora_ini_str_clean = hora_ini_str.replace('.', '')
        hora_fin_str_clean = hora_fin_str.replace('.', '')
        t_ini = pd.to_datetime(hora_ini_str_clean, format='%I:%M %p', errors='coerce').time()
        t_fin = pd.to_datetime(hora_fin_str_clean, format='%I:%M %p', errors='coerce').time()

        if pd.isna(t_ini) or pd.isna(t_fin): return None

        dt_ini = pd.Timestamp.combine(fecha_base, t_ini)
        dt_fin = pd.Timestamp.combine(fecha_base, t_fin)

        if dt_fin < dt_ini: dt_fin += timedelta(days=1)

        duracion = dt_fin - dt_ini
        return duracion.total_seconds() / 3600.0

    except Exception: return None

# --- Callbacks Específicos de esta Página ---

# Callback para inicializar controles (sin cambios)
@callback(
    Output('prod-dropdown-producto', 'options'),
    Output('prod-dropdown-producto', 'value'),
    Output('prod-dropdown-producto', 'placeholder'),
    Output('prod-slider-fechas', 'min'),
    Output('prod-slider-fechas', 'max'),
    Output('prod-slider-fechas', 'value'),
    Output('prod-slider-fechas', 'disabled'),
    Input('store-main-data', 'data') # Disparado por el store
)
def inicializar_controles_produccion(data_json_trigger):
    if not data_json_trigger:
        print("Store vacío, esperando datos para inicializar controles de producción.")
        return [], None, "Esperando datos...", 0, 1, [0, 1], True
    try:
        # Siempre utiliza el archivo RESPONSES_SIPROSA.csv
        df = pd.read_csv(CSV_FILE)
        df[COLUMNA_TIMESTAMP] = pd.to_datetime(df.get(COLUMNA_TIMESTAMP), errors='coerce')
        df[COLUMNA_FECHA_PROD] = pd.to_datetime(df.get(COLUMNA_FECHA_PROD), errors='coerce')
        df[COLUMNA_CANTIDAD] = pd.to_numeric(df.get(COLUMNA_CANTIDAD), errors='coerce')

        df_prod = df[
            (df.get(COLUMNA_EVENTO) == VALOR_PRODUCCION) &
            (df.get(COLUMNA_HUBO_PRODUCCION) == VALOR_SI_PRODUCCION) &
            df[COLUMNA_PRODUCTO].notna() &
            df[COLUMNA_CANTIDAD].notna() &
            df[COLUMNA_FECHA_PROD].notna()
        ].copy()

        if df_prod.empty:
            print("No hay datos de producción válidos para inicializar controles.")
            return [], None, "Sin datos de prod.", 0, 1, [0, 1], True

        lista_productos = sorted(df_prod[COLUMNA_PRODUCTO].astype(str).unique())
        opciones_dropdown = [{'label': 'Todos', 'value': VALOR_TODOS}] + [{'label': prod, 'value': prod} for prod in lista_productos]
        valor_inicial_dropdown = lista_productos[0] if lista_productos else VALOR_TODOS
        placeholder_dropdown = "Seleccione Producto..."

        min_fecha = df_prod[COLUMNA_FECHA_PROD].min()
        max_fecha = df_prod[COLUMNA_FECHA_PROD].max()
        slider_min = min_fecha.toordinal()
        slider_max = max_fecha.toordinal()
        slider_value = [slider_min, slider_max]
        slider_disabled = False

        print(f"Controles de producción inicializados. Productos: {len(lista_productos)}. Rango Fechas: {min_fecha.date()} a {max_fecha.date()}")
        return opciones_dropdown, valor_inicial_dropdown, placeholder_dropdown, slider_min, slider_max, slider_value, slider_disabled
    except FileNotFoundError:
        print(f"ERROR CRÍTICO en producción: Archivo '{CSV_FILE}' no encontrado.")
        return [], VALOR_TODOS, "Error: Archivo", 0, 1, [0, 1], True
    except Exception as e:
        print(f"Error procesando datos para inicializar controles de producción: {e}")
        import traceback
        traceback.print_exc()
        return [], VALOR_TODOS, "Error", 0, 1, [0, 1], True

# Callback principal para actualizar TODA la página de producción
@callback(
    Output('prod-output-fechas', 'children'),
    Output('prod-contenedor-graficos-linea', 'children'),
    Output('prod-grafico-barras-maquinas', 'figure'),
    Output('prod-kpis-eficiencia', 'children'),
    Output('prod-tabla-detalle', 'children'),
    Input('prod-dropdown-producto', 'value'),
    Input('prod-slider-fechas', 'value'),
)
def update_production_page(producto_seleccionado, rango_fechas_slider):

    # --- Validaciones Iniciales ---
    fig_barras_vacia = go.Figure()
    fig_barras_vacia.update_layout(xaxis = dict(showgrid=False, visible=False), yaxis = dict(showgrid=False, visible=False), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')

    if not producto_seleccionado or not rango_fechas_slider:
        print("Esperando selección de producto y rango de fechas.")
        fig_barras_vacia.update_layout(title_text="Seleccione producto y fechas")
        return "Seleccione producto y fechas", [], fig_barras_vacia, [], html.Div("Seleccione producto y fechas.")

    if producto_seleccionado == VALOR_TODOS:
        print("Selección 'Todos' detectada.")
        alert_msg = dbc.Alert("Por favor, seleccione un producto específico para ver los detalles.", color="info", className="text-center")
        fig_barras_vacia.update_layout(title_text="Seleccione un Producto")
        return "Seleccione un producto", [], fig_barras_vacia, [], alert_msg

    # --- Carga y Filtrado de Datos ---
    try:
        # Siempre utiliza el archivo RESPONSES_SIPROSA.csv
        df_original = pd.read_csv(CSV_FILE)
        df_original[COLUMNA_FECHA_PROD] = pd.to_datetime(df_original.get(COLUMNA_FECHA_PROD), errors='coerce')
        df_original[COLUMNA_CANTIDAD] = pd.to_numeric(df_original.get(COLUMNA_CANTIDAD), errors='coerce')
        df_original[COLUMNA_HORA_INI_PROD] = df_original.get(COLUMNA_HORA_INI_PROD, pd.Series(dtype=str)).astype(str).str.strip()
        df_original[COLUMNA_HORA_FIN_PROD] = df_original.get(COLUMNA_HORA_FIN_PROD, pd.Series(dtype=str)).astype(str).str.strip()
        df_original[COLUMNA_MAQUINA_PROD] = df_original.get(COLUMNA_MAQUINA_PROD, pd.Series(dtype=str)).astype(str).str.strip()
        df_original[COLUMNA_UNIDAD] = df_original.get(COLUMNA_UNIDAD, pd.Series(dtype=str)).astype(str).str.strip()

        df_prod_validos = df_original[
            (df_original[COLUMNA_EVENTO] == VALOR_PRODUCCION) &
            (df_original.get(COLUMNA_HUBO_PRODUCCION) == VALOR_SI_PRODUCCION) &
            df_original[COLUMNA_PRODUCTO].notna() &
            df_original[COLUMNA_CANTIDAD].notna() & (df_original[COLUMNA_CANTIDAD] > 0) &
            df_original[COLUMNA_MAQUINA_PROD].notna() & (df_original[COLUMNA_MAQUINA_PROD] != '') &
            df_original[COLUMNA_UNIDAD].notna() & (df_original[COLUMNA_UNIDAD] != '') &
            df_original[COLUMNA_FECHA_PROD].notna() &
            df_original[COLUMNA_HORA_INI_PROD].notna() & (df_original[COLUMNA_HORA_INI_PROD] != '') & (df_original[COLUMNA_HORA_INI_PROD].str.contains(':')) &
            df_original[COLUMNA_HORA_FIN_PROD].notna() & (df_original[COLUMNA_HORA_FIN_PROD] != '') & (df_original[COLUMNA_HORA_FIN_PROD].str.contains(':'))
        ].copy()

        if df_prod_validos.empty:
             raise PreventUpdate("No hay datos de producción válidos después del filtro inicial.")

        fecha_inicio_dt = pd.Timestamp.fromordinal(rango_fechas_slider[0])
        fecha_fin_dt = pd.Timestamp.fromordinal(rango_fechas_slider[1])
        texto_fechas_slider = f"{fecha_inicio_dt.strftime('%d/%m/%y')} - {fecha_fin_dt.strftime('%d/%m/%y')}"

        df_filtrado = df_prod_validos[
            (df_prod_validos[COLUMNA_FECHA_PROD] >= fecha_inicio_dt) &
            (df_prod_validos[COLUMNA_FECHA_PROD] <= fecha_fin_dt) &
            (df_prod_validos[COLUMNA_PRODUCTO] == producto_seleccionado)
        ].copy()

        if df_filtrado.empty:
            print(f"No hay datos para '{producto_seleccionado}' en el rango seleccionado.")
            alert_msg = dbc.Alert(f"No hay datos para '{producto_seleccionado}' en el rango seleccionado.", color="warning", className="text-center")
            fig_barras_vacia.update_layout(title_text=f"Sin datos para {producto_seleccionado}")
            return texto_fechas_slider, [], fig_barras_vacia, [], alert_msg

    except PreventUpdate as p:
        print(p)
        alert_msg = dbc.Alert(str(p), color="secondary", className="text-center")
        fig_barras_vacia.update_layout(title_text="Datos insuficientes")
        return "...", [], fig_barras_vacia, [], alert_msg
    except Exception as e:
        print(f"Error cargando o filtrando datos en producción: {e}")
        import traceback
        traceback.print_exc()
        alert_msg = dbc.Alert("Error procesando los datos.", color="danger")
        fig_barras_vacia.update_layout(title_text="Error")
        return "Error", [], fig_barras_vacia, [], alert_msg

    # --- Generación de Gráficos y Tabla ---
    graficos_linea_maquina = []
    kpis_eficiencia_cards = []
    tabla_detalle_html = html.Div("No hay registros detallados.")
    fig_barras = go.Figure() # Inicializar figura vacía por defecto
    fig_barras.update_layout(
        xaxis = dict(showgrid=False, visible=False),
        yaxis = dict(showgrid=False, visible=False),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )


    maquinas_en_seleccion = sorted(df_filtrado[COLUMNA_MAQUINA_PROD].unique())
    produccion_agregada = pd.DataFrame()

    if maquinas_en_seleccion:
        df_filtrado['duracion_horas'] = df_filtrado.apply(
            lambda row: calcular_duracion_horas(row[COLUMNA_FECHA_PROD], row[COLUMNA_HORA_INI_PROD], row[COLUMNA_HORA_FIN_PROD]),
            axis=1
        )
        df_calculos = df_filtrado.dropna(subset=['duracion_horas']).copy()
        df_calculos = df_calculos[df_calculos['duracion_horas'] > 0]

        if not df_calculos.empty:
            produccion_agregada = df_calculos.groupby([COLUMNA_MAQUINA_PROD, COLUMNA_UNIDAD]).agg(
                cantidad_total=(COLUMNA_CANTIDAD, 'sum'),
                duracion_total_horas=('duracion_horas', 'sum')
            ).reset_index()

            if not produccion_agregada.empty:
                produccion_agregada['eficiencia_prom_hora'] = (produccion_agregada['cantidad_total'] / produccion_agregada['duracion_total_horas']).fillna(0)

                # --- Gráfico de Barras (Agrupado por Unidad y Colores Consistentes) ---
                fig_barras = px.bar(produccion_agregada.sort_values(['cantidad_total'], ascending=False),
                                    x=COLUMNA_MAQUINA_PROD,
                                    y='cantidad_total',
                                    color=COLUMNA_UNIDAD,
                                    barmode='group',
                                    text='cantidad_total',
                                    labels={COLUMNA_MAQUINA_PROD: 'Máquina',
                                            'cantidad_total': 'Producción Total',
                                            COLUMNA_UNIDAD: 'Unidad'},
                                    hover_data={'cantidad_total':':,.0f', COLUMNA_UNIDAD: True, 'eficiencia_prom_hora': ':.1f'},
                                    color_discrete_map=MAPA_COLORES_UNIDADES # *** APLICAR MAPA DE COLORES ***
                                    )
                fig_barras.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
                fig_barras.update_layout(
                    title=None, # Quitar título, ya está en la card
                    uniformtext_minsize=8, uniformtext_mode='hide',
                    xaxis_tickangle=0,
                    height=350,
                    margin=dict(l=20, r=10, t=10, b=20), # Ajustar b si es necesario
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    legend_title_text='Unidad'
                )

                # --- KPIs de Eficiencia ---
                produccion_agregada_sorted = produccion_agregada.sort_values(['eficiencia_prom_hora'], ascending=False)
                for index, row in produccion_agregada_sorted.iterrows():
                     unidad_kpi = row[COLUMNA_UNIDAD]
                     eficiencia_kpi = row['eficiencia_prom_hora']
                     # Usar un ancho fijo o relativo para las cards para mejor alineación
                     card = dbc.Card([
                         dbc.CardHeader(html.H6(row[COLUMNA_MAQUINA_PROD], className="mb-0 text-center small"), className="p-2"),
                         dbc.CardBody(html.P(f"{eficiencia_kpi:,.1f} {unidad_kpi}/hr", className="card-text text-center fw-bold fs-5"), className="p-2")
                     ], className="mb-2", style={"width": "18rem"}) # Ejemplo de ancho fijo
                     kpis_eficiencia_cards.append(card)
                if not kpis_eficiencia_cards:
                     kpis_eficiencia_cards = [html.P("No se pudo calcular la eficiencia.", className="text-muted text-center")]


            # --- Gráficos de Línea por Máquina (Cada uno ancho completo) ---
            for maquina in maquinas_en_seleccion:
                df_maquina_linea = df_filtrado[df_filtrado[COLUMNA_MAQUINA_PROD] == maquina]
                if not df_maquina_linea.empty:
                    produccion_diaria = df_maquina_linea.groupby(df_maquina_linea[COLUMNA_FECHA_PROD].dt.date)[COLUMNA_CANTIDAD].sum().reset_index()
                    produccion_diaria.rename(columns={COLUMNA_FECHA_PROD: 'Fecha'}, inplace=True)
                    produccion_diaria = produccion_diaria.sort_values(by='Fecha')
                    unidades_maquina = df_maquina_linea[COLUMNA_UNIDAD].unique()
                    titulo_linea = f"{maquina}"
                    label_y_linea = f"Producción Total ({', '.join(unidades_maquina)})" if len(unidades_maquina) > 1 else f"Producción ({unidades_maquina[0]})"

                    fig_linea = px.line(produccion_diaria, x='Fecha', y=COLUMNA_CANTIDAD, markers=True,
                                   labels={'Fecha': 'Fecha', COLUMNA_CANTIDAD: label_y_linea})
                    fig_linea.update_traces(marker=dict(size=8))
                    fig_linea.update_layout(title_text=titulo_linea, title_font_size=14, title_x=0.5, height=300, # Aumentar altura si es necesario
                                      margin=dict(l=20, r=10, t=40, b=20), font_size=12,
                                      paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')

                    # *** ASEGURAR QUE CADA GRÁFICO OCUPE width=12 ***
                    graficos_linea_maquina.append(
                        dbc.Col(dbc.Card(dcc.Graph(figure=fig_linea, config={'displayModeBar': False})), width=12, className="mb-3") # Añadir margen inferior
                    )

        # --- Tabla Detallada ---
        if not df_filtrado.empty:
            columnas_tabla = [COLUMNA_FECHA_PROD, COLUMNA_MAQUINA_PROD, COLUMNA_PRODUCTO, COLUMNA_UNIDAD, COLUMNA_CANTIDAD, COLUMNA_HORA_INI_PROD, COLUMNA_HORA_FIN_PROD]
            columnas_tabla_existentes = [col for col in columnas_tabla if col in df_filtrado.columns]
            df_tabla = df_filtrado[columnas_tabla_existentes].copy()
            df_tabla[COLUMNA_FECHA_PROD] = df_tabla[COLUMNA_FECHA_PROD].dt.strftime('%d/%m/%Y')
            if COLUMNA_CANTIDAD in df_tabla.columns:
                 df_tabla[COLUMNA_CANTIDAD] = df_tabla[COLUMNA_CANTIDAD].apply(lambda x: f"{int(x):,}" if pd.notna(x) else '')
            try: # Ordenar tabla
                df_tabla[COLUMNA_HORA_INI_PROD + '_time'] = pd.to_datetime(df_tabla[COLUMNA_HORA_INI_PROD].astype(str).str.replace('.', '', regex=False), format='%I:%M %p', errors='coerce').dt.time
                # Crear datetime para ordenar combinando fecha y hora de inicio
                df_tabla['datetime_sort'] = pd.to_datetime(df_filtrado[COLUMNA_FECHA_PROD].dt.strftime('%Y-%m-%d') + ' ' + df_tabla[COLUMNA_HORA_INI_PROD + '_time'].astype(str), errors='coerce')
                df_tabla = df_tabla.sort_values(by='datetime_sort', ascending=True, na_position='last')
                df_tabla = df_tabla.drop(columns=[COLUMNA_HORA_INI_PROD + '_time', 'datetime_sort'], errors='ignore') # Ignorar error si no existen
            except Exception as e_sort_tabla:
                print(f"Advertencia: No se pudo ordenar la tabla detallada: {e_sort_tabla}")

            tabla_detalle_html = dbc.Table.from_dataframe(df_tabla, striped=True, bordered=True, hover=True, responsive=True, class_name="align-middle")
        else:
             tabla_detalle_html = dbc.Alert("No hay registros detallados para mostrar.", color="secondary", className="text-center")

    else: # Si no hay máquinas en la selección inicial
        alert_msg = dbc.Alert(f"No se encontraron máquinas que produjeran '{producto_seleccionado}' en el rango seleccionado.", color="warning", className="text-center")
        kpis_eficiencia_cards = [html.P("Sin datos de máquinas.", className="text-muted text-center")]
        tabla_detalle_html = alert_msg
        fig_barras.update_layout(title_text=f"Sin datos para {producto_seleccionado}")

    if not graficos_linea_maquina and not df_filtrado.empty :
         graficos_linea_maquina = [dbc.Col(dbc.Alert("No se pudo generar la evolución diaria.", color="secondary"), width=12)]


    return texto_fechas_slider, graficos_linea_maquina, fig_barras, kpis_eficiencia_cards, tabla_detalle_html