# pages/home.py

import dash
from dash import dcc, html, Input, Output, callback, State, no_update
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.io as pio
import pandas as pd
import numpy as np
from datetime import date, timedelta
from dash.exceptions import PreventUpdate

# --- Constantes Actualizadas ---
# Siempre utiliza el archivo RESPONSES_SIPROSA.csv
CSV_FILE = 'RESPONSES_SIPROSA.csv' # Nombre de archivo centralizado

COLUMNA_TIMESTAMP = 'Timestamp'
COLUMNA_EVENTO = 'TIPO DE EVENTO A REGISTRAR'
COLUMNA_FECHA_PROD = 'FECHA DE LA PRODUCCIÓN'
COLUMNA_FECHA_MANT = 'FECHA DEL MANTENIMIENTO'
COLUMNA_FECHA_INCID = 'FECHA DEL INCIDENTE o PARADA'
# CORRECCIÓN DE NOMBRE DE COLUMNA (ajustar si el nombre real en CSV es diferente)
# Asumiendo que la columna de máquina para producción es 'MAQUINA UTILIZADA'
# Si es 'MAQUINA UTILIZADA (PRODUCCIÓN)', cambiar abajo donde se usa
COLUMNA_MAQUINA_PROD = 'MAQUINA UTILIZADA' # Asegúrate que este sea el nombre EXACTO en tu CSV para producción
COLUMNA_MAQUINA_MANT = 'MÁQUINA BAJO MANTENIMIENTO'
COLUMNA_MAQUINA_INCID = 'MAQUINA ASOCIADA AL INCIDENTE O PARADA'
COLUMNA_REALIZO_MANTENIMIENTO = '¿SE REALIZÓ MANTENIMIENTO?'
COLUMNA_HUBO_PRODUCCION = '¿HUBO PRODUCCIÓN?' # Asegúrate que este sea el nombre EXACTO en tu CSV
COLUMNA_CANTIDAD = 'CANTIDAD PRODUCIDA'
COLUMNA_UNIDAD = 'UNIDAD DE MEDIDA'
COLUMNA_PRODUCTO = 'PRODUCTO PRODUCIDO'
COLUMNA_HORA_INI_PROD = 'HORA DE INICIO DE LA PRODUCCÓN'
COLUMNA_HORA_FIN_PROD = 'HORA DE FIN DE LA PRODUCCÓN'
COLUMNA_TIPO_MANT = 'TIPO DE MANTENIMIENTO REALIZADO'
COLUMNA_DESC_MANT = 'DESCRIPCIÓN DEL MANTENIMIENTO REALIZADO'
COLUMNA_HORA_INI_MANT = 'HORA DE INICIO DEL MANTENIMIENTO'
COLUMNA_HORA_FIN_MANT = 'HORA DE FIN DEL MANTENIMIENTO'
COLUMNA_HORA_INI_INCID = 'HORA DE INICIO DEL INCIDENTE o PARADA'
COLUMNA_HORA_FIN_INCID = 'HORA DE FIN DEL INCIDENTE o PARADA'
COLUMNA_DESC_INCID = 'DESCRIPCIÓN DEL INCIDENTE O PARADA'
COLUMNA_OBSERVACIONES = 'OBSERVACIONES ADICIONALES'
# Valores clave (originales)
VALOR_PRODUCCION = 'Producción'
VALOR_MANTENIMIENTO = 'Mantenimiento'
VALOR_INCIDENTES = 'Incidentes y Paradas'
VALOR_OBSERVACIONES = 'Observaciones Generales'
VALOR_SI_MANTENIMIENTO = 'Sí'
VALOR_SI_PRODUCCION = 'Sí' # Asegúrate que este sea el valor EXACTO en tu CSV
VALOR_TODAS = 'Todas'

# --- Nombres para mostrar en el gráfico ---
NOMBRE_GRAFICO_PRODUCCION = 'Registro de Producción'
NOMBRE_GRAFICO_MANTENIMIENTO = 'Registro de Mantenimiento'
NOMBRE_GRAFICO_INCIDENTES = 'Registro de Incidentes y Paradas'
NOMBRE_GRAFICO_OBSERVACIONES = 'Registro de Observaciones Generales'

# Mapeo de valores originales a nombres del gráfico
MAPEO_NOMBRES_GRAFICO = {
    VALOR_PRODUCCION: NOMBRE_GRAFICO_PRODUCCION,
    VALOR_MANTENIMIENTO: NOMBRE_GRAFICO_MANTENIMIENTO,
    VALOR_INCIDENTES: NOMBRE_GRAFICO_INCIDENTES,
    VALOR_OBSERVACIONES: NOMBRE_GRAFICO_OBSERVACIONES
}

# Mapeo inverso (de nombres del gráfico a valores originales)
MAPEO_INVERSO_NOMBRES = {v: k for k, v in MAPEO_NOMBRES_GRAFICO.items()}


# Unidades para KPIs (Actualizado)
UNIDAD_COMPRIMIDOS = 'Comprimidos'
UNIDAD_BLISTERS = 'Blisters'
UNIDAD_LITROS = 'Litros'
UNIDAD_KILOGRAMOS = 'Kilogramos' # Podría ser necesario para otros análisis
# Colores semáforo
UMBRAL_POSITIVO = 5.0; UMBRAL_NEGATIVO = -5.0; COLOR_TEXTO_VERDE = 'text-success'; COLOR_TEXTO_ROJO = 'text-danger'; COLOR_TEXTO_AMARILLO = 'text-warning'; COLOR_TEXTO_GRIS = 'text-muted'

pio.templates.default = "plotly_dark"

# --- Funciones Auxiliares ---
# (Sin cambios)
def calcular_variacion(actual, anterior):
    if anterior is None or actual is None or pd.isna(anterior) or pd.isna(actual): return None
    try: anterior = float(anterior); actual = float(actual)
    except (ValueError, TypeError): return None
    if anterior == 0: return 0.0 if actual == 0 else np.inf
    if actual == 0 and anterior != 0: return -100.0
    return ((actual - anterior) / anterior) * 100

def obtener_clase_texto_semaforo(variacion, es_produccion):
    if variacion is None: return COLOR_TEXTO_GRIS, "N/A"
    texto_porcentaje="N/A"; clase_texto=COLOR_TEXTO_GRIS
    if variacion == np.inf: clase_texto = COLOR_TEXTO_VERDE if es_produccion else COLOR_TEXTO_ROJO; texto_porcentaje = "+Inf%"
    elif variacion == -np.inf: clase_texto = COLOR_TEXTO_ROJO if es_produccion else COLOR_TEXTO_VERDE; texto_porcentaje = "-Inf%"
    elif variacion == -100.0: clase_texto = COLOR_TEXTO_ROJO if es_produccion else COLOR_TEXTO_VERDE; texto_porcentaje = "-100%"
    else:
        if es_produccion:
            if variacion > UMBRAL_POSITIVO: clase_texto = COLOR_TEXTO_VERDE
            elif variacion < UMBRAL_NEGATIVO: clase_texto = COLOR_TEXTO_ROJO
            else: clase_texto = COLOR_TEXTO_AMARILLO
        else:
            if variacion < UMBRAL_NEGATIVO: clase_texto = COLOR_TEXTO_VERDE
            elif variacion > UMBRAL_POSITIVO: clase_texto = COLOR_TEXTO_ROJO
            else: clase_texto = COLOR_TEXTO_AMARILLO
        texto_porcentaje = f"{variacion:+.1f}%"
    return clase_texto, texto_porcentaje

# --- Registro de la Página ---
dash.register_page(__name__, path='/', title='Resumen Operaciones', name='Resumen')

# --- Layout Helper ---
# (Sin cambios estructurales)
def layout():
    return dbc.Container([
        dbc.Row(dbc.Col(html.H1("Resumen de Operaciones", className="text-center display-4 my-4"))),
        dbc.Row([
            dbc.Col(html.H4("Indicadores Clave (vs Período Anterior)"), md=7, className="d-flex align-items-center"),
            dbc.Col(dbc.Card(dbc.CardBody([
                    dcc.Dropdown(id='home-dropdown-producto-kpi', clearable=False, placeholder="Producto para KPIs...")
                ], className="p-2")), md=5)
        ], className="mt-3 mb-2 align-items-center"),
        dbc.Row(id='home-contenedor-kpis-comparativos', className="g-3 mb-3 align-items-stretch"),
        dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody([
                    html.Label('Máquina (Filtro General):', className="card-title mb-2 small"),
                    dcc.Dropdown(id='home-dropdown-maquina', clearable=False, placeholder="Máquina...")
            ]), className="h-100"), md=6),
            dbc.Col(dbc.Card(dbc.CardBody([
                     html.H5("Registros Filtrados", className="card-title text-center small mb-1"),
                     html.H3(id='home-contador-registros', className="text-center", children="...")
            ]), className="h-100 d-flex flex-column justify-content-center"), md=6),
        ], className="align-items-stretch mb-3"),
        dbc.Row([dbc.Col(html.H4("Resumen del Período Seleccionado"))], className="mt-3"),
        dbc.Row(id='home-contenedor-kpis-generales', className="g-3 mb-3 align-items-stretch"),
        dbc.Row([dbc.Col(dbc.Card([
            dbc.CardHeader("Filtro de Fechas"),
            dbc.CardBody([
                 dcc.RangeSlider(id='home-slider-rango-fechas', marks=None, step=1, tooltip={"placement": "bottom", "always_visible": True}, className="p-0", disabled=True),
                 html.Div(id='home-output-rango-fechas', className='text-center text-muted small mt-2'),
            ])
        ]))], className="mb-3"),
        dbc.Row([dbc.Col(dbc.Card(dbc.Spinner(dcc.Graph(id='home-grafico-tipos-evento', config={'displayModeBar': False}))), width=12)], className="mb-4"),
        dbc.Modal([dbc.ModalHeader(dbc.ModalTitle(id='home-modal-titulo')), dbc.ModalBody(id='home-modal-tabla-contenido')],
                  id="home-modal-detalle", size="xl", is_open=False, scrollable=True),
    ], fluid=True, className="dbc mt-4")

# --- Función Auxiliar para Crear Tarjetas KPI ---
# (Sin cambios)
def crear_kpi_card(titulo, valor):
     valor_formateado = "0";
     if valor is not None and pd.notna(valor):
          try: valor_formateado = f"{int(valor):,}"
          except (ValueError, TypeError): valor_formateado = f"{valor}"
     return dbc.Col(dbc.Card(dbc.CardBody([
                 html.P(titulo, className="card-text text-center small text-muted mb-1"),
                 html.H4(f"{valor_formateado}", className="text-center fw-bold")
             ]), className="h-100"))

# --- Callbacks ---

# Callback de inicialización (Usa CSV_FILE)
@callback(
    Output('home-dropdown-producto-kpi', 'options'), Output('home-dropdown-producto-kpi', 'value'), Output('home-dropdown-producto-kpi', 'placeholder'),
    Output('home-dropdown-maquina', 'options'), Output('home-dropdown-maquina', 'value'), Output('home-dropdown-maquina', 'placeholder'),
    Output('home-slider-rango-fechas', 'min'), Output('home-slider-rango-fechas', 'max'), Output('home-slider-rango-fechas', 'value'), Output('home-slider-rango-fechas', 'disabled'),
    Input('store-main-data', 'data') # Usa store solo como trigger inicial
)
def inicializar_controles_home(data_json_trigger): # Renombrado para claridad
    default_slider = [0, 1, [0, 1], True]; default_prod = ([], None, "Error carga"); default_maq = ([], VALOR_TODAS, "Error carga")
    try:
        # Siempre utiliza el archivo RESPONSES_SIPROSA.csv
        df = pd.read_csv(CSV_FILE) # Cargar desde el archivo especificado
        # Conversiones (incluir todas las fechas usadas)
        date_cols = [COLUMNA_TIMESTAMP, COLUMNA_FECHA_PROD, COLUMNA_FECHA_MANT, COLUMNA_FECHA_INCID]
        for col in date_cols:
            if col in df.columns:
                 df[col] = pd.to_datetime(df[col], errors='coerce')
            else:
                 print(f"Advertencia: Columna de fecha '{col}' no encontrada en {CSV_FILE}")
        if COLUMNA_CANTIDAD in df.columns:
            df[COLUMNA_CANTIDAD] = pd.to_numeric(df[COLUMNA_CANTIDAD], errors='coerce')
        else:
             print(f"Advertencia: Columna '{COLUMNA_CANTIDAD}' no encontrada en {CSV_FILE}")

        # Opciones Dropdown Producto
        # Asegurarse de usar el nombre correcto de la columna ¿HUBO PRODUCCIÓN?
        df_prod = df[ (df.get(COLUMNA_EVENTO) == VALOR_PRODUCCION) & (df.get(COLUMNA_HUBO_PRODUCCION) == VALOR_SI_PRODUCCION) & df.get(COLUMNA_PRODUCTO, pd.Series(dtype=str)).notna() & df.get(COLUMNA_CANTIDAD, pd.Series(dtype=float)).notna() & df.get(COLUMNA_FECHA_PROD, pd.Series(dtype='datetime64[ns]')).notna() ].copy()
        lista_productos = sorted(df_prod[COLUMNA_PRODUCTO].unique()) if not df_prod.empty else []; opciones_dropdown_prod = [{'label': prod, 'value': prod} for prod in lista_productos]; valor_inicial_prod = lista_productos[0] if lista_productos else None; placeholder_prod = "Producto para KPIs..." if lista_productos else "No hay productos"

        # Opciones Dropdown Máquina
        # Asegurarse de usar el nombre correcto de la columna de máquina de producción
        maq_cols = [COLUMNA_MAQUINA_PROD, COLUMNA_MAQUINA_MANT, COLUMNA_MAQUINA_INCID]
        all_maquinas = set()
        for col in maq_cols:
            if col in df.columns:
                # Limpiar posibles espacios extra en los nombres de máquinas
                all_maquinas.update(df[col].dropna().astype(str).str.strip().unique())
            else:
                 print(f"Advertencia: Columna de máquina '{col}' no encontrada en {CSV_FILE}")
        # Filtrar cadenas vacías si existen después del strip
        all_maquinas = {maq for maq in all_maquinas if maq}
        lista_maquinas = sorted(list(all_maquinas)); opciones_dropdown_maq = [{'label': VALOR_TODAS, 'value': VALOR_TODAS}] + [{'label': maq, 'value': maq} for maq in lista_maquinas]; valor_inicial_maq = VALOR_TODAS; placeholder_maq = "Seleccione Máquina..." if lista_maquinas else "No hay máquinas"

        # Slider Fechas
        all_dates = pd.concat([df.get(c, pd.Series(dtype='datetime64[ns]')) for c in date_cols], ignore_index=True).dropna(); min_fecha = all_dates.min() if not all_dates.empty else pd.Timestamp('now') - timedelta(days=30); max_fecha = all_dates.max() if not all_dates.empty else pd.Timestamp('now'); slider_min = min_fecha.toordinal(); slider_max = max_fecha.toordinal(); slider_value = [slider_min, slider_max]; slider_disabled = all_dates.empty; current_slider = [slider_min, slider_max, slider_value, slider_disabled]
        return opciones_dropdown_prod, valor_inicial_prod, placeholder_prod, opciones_dropdown_maq, valor_inicial_maq, placeholder_maq, current_slider[0], current_slider[1], current_slider[2], current_slider[3]
    except FileNotFoundError:
        print(f"ERROR CRÍTICO: Archivo '{CSV_FILE}' no encontrado.")
        # Siempre utiliza el archivo RESPONSES_SIPROSA.csv
        # En caso de error, también debe referenciarlo
        return default_prod[0], default_prod[1], f"'{CSV_FILE}' no encontrado", default_maq[0], default_maq[1], f"'{CSV_FILE}' no encontrado", default_slider[0], default_slider[1], default_slider[2], default_slider[3]
    except Exception as e: print(f"Error inicializando: {e}"); import traceback; traceback.print_exc(); return default_prod[0], default_prod[1], "Error", default_maq[0], default_maq[1], "Error", default_slider[0], default_slider[1], default_slider[2], default_slider[3]


# --- Función para aplicar filtro de máquina CORRECTAMENTE ---
def aplicar_filtro_maquina(df_filtrado_fecha, maquina_seleccionada):
    if maquina_seleccionada == VALOR_TODAS or df_filtrado_fecha.empty:
        return df_filtrado_fecha.copy()

    # Crear máscaras específicas por tipo de evento y máquina relevante
    mask_prod = pd.Series(False, index=df_filtrado_fecha.index)
    if COLUMNA_MAQUINA_PROD in df_filtrado_fecha.columns:
        mask_prod = (df_filtrado_fecha[COLUMNA_EVENTO] == VALOR_PRODUCCION) & \
                    (df_filtrado_fecha[COLUMNA_MAQUINA_PROD].astype(str).str.strip() == maquina_seleccionada)

    mask_mant = pd.Series(False, index=df_filtrado_fecha.index)
    if COLUMNA_MAQUINA_MANT in df_filtrado_fecha.columns:
        mask_mant = (df_filtrado_fecha[COLUMNA_EVENTO] == VALOR_MANTENIMIENTO) & \
                    (df_filtrado_fecha[COLUMNA_MAQUINA_MANT].astype(str).str.strip() == maquina_seleccionada)

    mask_incid = pd.Series(False, index=df_filtrado_fecha.index)
    if COLUMNA_MAQUINA_INCID in df_filtrado_fecha.columns:
        # Incluir filas cuyo TIPO DE EVENTO sea Incidente Y la máquina asociada coincida
        # O incluir filas de OTRO tipo de evento si SU máquina asociada coincide (esto incluye incidentes asociados a producción/mantenimiento en esa máquina)
        mask_incid = (df_filtrado_fecha[COLUMNA_MAQUINA_INCID].astype(str).str.strip() == maquina_seleccionada)
        # Ajuste: Para el *conteo* de incidentes en el gráfico/KPI, queremos contar CUALQUIER fila con fecha de incidente y máquina asociada correcta.
        # Para *mostrar* detalles, la lógica podría variar.
        # PERO, para la consistencia entre gráfico y modal, filtremos primero por la máquina PRIMARIA del evento.
        # Si el usuario hace clic en "Registro de Incidentes", ya mostraremos todos los asociados a esa máquina.

        # Lógica revisada y simplificada: filtrar por la máquina principal del evento
        mask_incid_primario = (df_filtrado_fecha[COLUMNA_EVENTO] == VALOR_INCIDENTES) & \
                              (df_filtrado_fecha[COLUMNA_MAQUINA_INCID].astype(str).str.strip() == maquina_seleccionada)
        mask_incid = mask_incid_primario # Usamos esta por ahora para la consistencia inicial

    # Combinar máscaras: una fila pasa si CUALQUIERA de sus condiciones de máquina relevante se cumple
    # CORRECCIÓN: Una fila pasa si SU tipo de evento corresponde a la máquina seleccionada.
    mask_final = mask_prod | mask_mant | mask_incid

    # Incluir observaciones si se seleccionó una máquina? Generalmente no.
    # Si se quisiera, se añadiría: | (df_filtrado_fecha[COLUMNA_EVENTO] == VALOR_OBSERVACIONES)

    return df_filtrado_fecha[mask_final].copy()


# Callback principal (Usa la nueva función de filtro)
@callback(
    Output('home-contador-registros', 'children'), Output('home-grafico-tipos-evento', 'figure'), Output('home-output-rango-fechas', 'children'),
    Output('home-contenedor-kpis-comparativos', 'children'), Output('home-contenedor-kpis-generales', 'children'),
    Input('home-slider-rango-fechas', 'value'), Input('home-dropdown-producto-kpi', 'value'), Input('home-dropdown-maquina', 'value'),
    State('store-max-date', 'data') # Solo usamos fecha máxima, no el dataframe del store
)
def update_home_page(rango_fechas_slider, producto_seleccionado_kpi, maquina_seleccionada, fecha_maxima_str):
    if rango_fechas_slider is None: return no_update, no_update, no_update, no_update, no_update
    try:
        # Siempre utiliza el archivo RESPONSES_SIPROSA.csv
        df_original = pd.read_csv(CSV_FILE)
        date_cols = [COLUMNA_TIMESTAMP, COLUMNA_FECHA_PROD, COLUMNA_FECHA_MANT, COLUMNA_FECHA_INCID]
        for col in date_cols:
            if col in df_original.columns: df_original[col] = pd.to_datetime(df_original[col], errors='coerce')
        if COLUMNA_CANTIDAD in df_original.columns: df_original[COLUMNA_CANTIDAD] = pd.to_numeric(df_original[COLUMNA_CANTIDAD], errors='coerce')

        all_event_dates = pd.concat([df_original.get(c, pd.Series(dtype='datetime64[ns]')) for c in [COLUMNA_FECHA_PROD, COLUMNA_FECHA_MANT, COLUMNA_FECHA_INCID]], ignore_index=True).dropna(); fecha_maxima_datos = all_event_dates.max().normalize() if not all_event_dates.empty else pd.Timestamp('now').normalize()
        df_prod_validos_kpi = df_original[ (df_original.get(COLUMNA_EVENTO) == VALOR_PRODUCCION) & (df_original.get(COLUMNA_HUBO_PRODUCCION) == VALOR_SI_PRODUCCION) & df_original.get(COLUMNA_PRODUCTO, pd.Series(dtype=str)).notna() & df_original.get(COLUMNA_CANTIDAD, pd.Series(dtype=float)).notna() & df_original.get(COLUMNA_MAQUINA_PROD, pd.Series(dtype=str)).notna() & df_original.get(COLUMNA_UNIDAD, pd.Series(dtype=str)).notna() & df_original[COLUMNA_FECHA_PROD].notna() ].copy()
        df_incidentes_kpi = df_original[df_original[COLUMNA_FECHA_INCID].notna()].copy()

    except FileNotFoundError: print(f"ERROR: Archivo '{CSV_FILE}' no encontrado."); return "Error Archivo", px.bar(title="Error"), "Error", [], []
    except Exception as e: print(f"Error cargando/procesando: {e}"); return "Error", px.bar(title="Error"), "Error", [], []

    # --- Filtrado por Fecha y Máquina (Usando nueva lógica) ---
    try:
        fecha_inicio_dt = pd.Timestamp.fromordinal(rango_fechas_slider[0]); fecha_fin_dt = pd.Timestamp.fromordinal(rango_fechas_slider[1]); texto_fechas_slider = f"{fecha_inicio_dt.strftime('%d/%m/%y')} - {fecha_fin_dt.strftime('%d/%m/%y')}"

        # 1. Filtrar por Fecha (igual que antes)
        df_filtrado_fecha = pd.DataFrame()
        dfs_filtrados_por_fecha = []
        if COLUMNA_FECHA_PROD in df_original.columns: dfs_filtrados_por_fecha.append(df_original[(df_original[COLUMNA_EVENTO] == VALOR_PRODUCCION) & (df_original[COLUMNA_FECHA_PROD] >= fecha_inicio_dt) & (df_original[COLUMNA_FECHA_PROD] <= fecha_fin_dt)])
        if COLUMNA_FECHA_MANT in df_original.columns: dfs_filtrados_por_fecha.append(df_original[(df_original[COLUMNA_EVENTO] == VALOR_MANTENIMIENTO) & (df_original[COLUMNA_FECHA_MANT] >= fecha_inicio_dt) & (df_original[COLUMNA_FECHA_MANT] <= fecha_fin_dt)])
        if COLUMNA_FECHA_INCID in df_original.columns: dfs_filtrados_por_fecha.append(df_original[(df_original[COLUMNA_FECHA_INCID] >= fecha_inicio_dt) & (df_original[COLUMNA_FECHA_INCID] <= fecha_fin_dt)])
        if COLUMNA_TIMESTAMP in df_original.columns: dfs_filtrados_por_fecha.append(df_original[(df_original[COLUMNA_EVENTO] == VALOR_OBSERVACIONES) & (df_original[COLUMNA_TIMESTAMP] >= fecha_inicio_dt) & (df_original[COLUMNA_TIMESTAMP] <= fecha_fin_dt)])
        if dfs_filtrados_por_fecha: df_filtrado_fecha = pd.concat(dfs_filtrados_por_fecha, ignore_index=True).drop_duplicates()

        # 2. Filtrar por Máquina (usando la función corregida)
        df_filtrado_final = aplicar_filtro_maquina(df_filtrado_fecha, maquina_seleccionada)

        num_registros_filtrados = len(df_filtrado_final); texto_contador = f"{num_registros_filtrados:,}"

    except Exception as e: print(f"Error filtrado: {e}"); texto_contador = "Error"; texto_fechas_slider = "Error"; df_filtrado_final = pd.DataFrame()

    # --- KPIs Generales (Se calculan ANTES del gráfico) ---
    kpi_generales_cards = []; incidentes_paradas_count_kpi = 0
    if not df_filtrado_final.empty:
        # Asegurarse que las columnas existen antes de usarlas
        df_prod_general = df_filtrado_final[(df_filtrado_final[COLUMNA_EVENTO] == VALOR_PRODUCCION) & (df_filtrado_final.get(COLUMNA_HUBO_PRODUCCION) == VALOR_SI_PRODUCCION) & df_filtrado_final[COLUMNA_CANTIDAD].notna() & df_filtrado_final[COLUMNA_UNIDAD].notna()].copy() if COLUMNA_HUBO_PRODUCCION in df_filtrado_final.columns and COLUMNA_CANTIDAD in df_filtrado_final.columns and COLUMNA_UNIDAD in df_filtrado_final.columns else pd.DataFrame()
        mantenimientos_si = df_filtrado_final[(df_filtrado_final[COLUMNA_EVENTO] == VALOR_MANTENIMIENTO) & (df_filtrado_final.get(COLUMNA_REALIZO_MANTENIMIENTO) == VALOR_SI_MANTENIMIENTO)].shape[0] if COLUMNA_REALIZO_MANTENIMIENTO in df_filtrado_final.columns else 0

        # Contar incidentes CON FECHA en el dataframe YA filtrado por fecha Y MÁQUINA (df_filtrado_final)
        incidentes_paradas_count_kpi = df_filtrado_final[df_filtrado_final[COLUMNA_FECHA_INCID].notna()].shape[0] if COLUMNA_FECHA_INCID in df_filtrado_final.columns else 0

        prod_comprimidos = df_prod_general[df_prod_general[COLUMNA_UNIDAD] == UNIDAD_COMPRIMIDOS][COLUMNA_CANTIDAD].sum() if not df_prod_general.empty and COLUMNA_UNIDAD in df_prod_general.columns and COLUMNA_CANTIDAD in df_prod_general.columns else 0
        prod_blisters = df_prod_general[df_prod_general[COLUMNA_UNIDAD] == UNIDAD_BLISTERS][COLUMNA_CANTIDAD].sum() if not df_prod_general.empty and COLUMNA_UNIDAD in df_prod_general.columns and COLUMNA_CANTIDAD in df_prod_general.columns else 0
        prod_litros = df_prod_general[df_prod_general[COLUMNA_UNIDAD] == UNIDAD_LITROS][COLUMNA_CANTIDAD].sum() if not df_prod_general.empty and COLUMNA_UNIDAD in df_prod_general.columns and COLUMNA_CANTIDAD in df_prod_general.columns else 0
        kpis_gen_data = [("Prod. Comprimidos", prod_comprimidos), ("Prod. Blisters", prod_blisters), ("Prod. Litros", prod_litros), ("Mantenimiento efectivo", mantenimientos_si), ("Incidentes/Paradas Reg.", incidentes_paradas_count_kpi)];
        for titulo, valor in kpis_gen_data: card_col = crear_kpi_card(titulo, valor); card_col.md = 2; kpi_generales_cards.append(card_col)
    else: kpi_generales_cards = [dbc.Col(dbc.Alert("No hay datos para filtros seleccionados", color="info"), width=12)]


    # --- Gráfico de Eventos ---
    # (Misma lógica que antes para contar y mapear nombres, usa df_filtrado_final)
    fig_barras_eventos = px.bar(title="Registros por Tipo (Sin datos en filtros)"); fig_barras_eventos.add_annotation(text="Seleccione filtros con datos", showarrow=False); fig_barras_eventos.update_layout(margin=dict(l=20, r=20, t=30, b=20), height=300, title_x=0.5, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    if not df_filtrado_final.empty:
        # 1. Contar otros eventos
        df_para_conteo_otros = df_filtrado_final[
            (df_filtrado_final[COLUMNA_EVENTO] == VALOR_PRODUCCION) |
            (df_filtrado_final[COLUMNA_EVENTO] == VALOR_OBSERVACIONES) |
            ((df_filtrado_final[COLUMNA_EVENTO] == VALOR_MANTENIMIENTO) & (df_filtrado_final.get(COLUMNA_REALIZO_MANTENIMIENTO) == VALOR_SI_MANTENIMIENTO))
        ].copy() if COLUMNA_REALIZO_MANTENIMIENTO in df_filtrado_final.columns else df_filtrado_final[ (df_filtrado_final[COLUMNA_EVENTO] == VALOR_PRODUCCION) | (df_filtrado_final[COLUMNA_EVENTO] == VALOR_OBSERVACIONES) ].copy()

        conteo_eventos_df = pd.DataFrame({'Tipo de Evento Original': [], 'Cantidad': []}) # Especificar dtype si es necesario
        if not df_para_conteo_otros.empty:
             conteo_inicial = df_para_conteo_otros[COLUMNA_EVENTO].value_counts().reset_index()
             conteo_inicial.columns = ['Tipo de Evento Original', 'Cantidad']
             conteo_eventos_df = conteo_inicial.astype({'Tipo de Evento Original': str, 'Cantidad': int}) # Asegurar tipos

        # 2. Añadir/Actualizar conteo de Incidentes (usando incidentes_paradas_count_kpi que viene de df_filtrado_final)
        if incidentes_paradas_count_kpi > 0:
             incidente_row = pd.DataFrame([{'Tipo de Evento Original': VALOR_INCIDENTES, 'Cantidad': incidentes_paradas_count_kpi}])
             # Convertir a los mismos tipos que conteo_eventos_df antes de concatenar o actualizar
             incidente_row = incidente_row.astype(conteo_eventos_df.dtypes.to_dict())

             if VALOR_INCIDENTES in conteo_eventos_df['Tipo de Evento Original'].values:
                  conteo_eventos_df.loc[conteo_eventos_df['Tipo de Evento Original'] == VALOR_INCIDENTES, 'Cantidad'] = incidentes_paradas_count_kpi
             else:
                  # Verificar si el DataFrame está vacío antes de concatenar
                  if conteo_eventos_df.empty:
                      conteo_eventos_df = incidente_row
                  else:
                      conteo_eventos_df = pd.concat([conteo_eventos_df, incidente_row], ignore_index=True)


        # 3. Mapear a los nombres del gráfico y generar gráfico si hay datos
        if not conteo_eventos_df.empty and conteo_eventos_df['Cantidad'].sum() > 0:
             conteo_eventos_df['Registro de'] = conteo_eventos_df['Tipo de Evento Original'].map(MAPEO_NOMBRES_GRAFICO)
             order_grafico = [NOMBRE_GRAFICO_PRODUCCION, NOMBRE_GRAFICO_MANTENIMIENTO, NOMBRE_GRAFICO_INCIDENTES, NOMBRE_GRAFICO_OBSERVACIONES]
             conteo_eventos_df = conteo_eventos_df[conteo_eventos_df['Registro de'].isin(order_grafico)]
             conteo_eventos_df['Registro de'] = pd.Categorical(conteo_eventos_df['Registro de'], categories=order_grafico, ordered=True)
             conteo_eventos_df = conteo_eventos_df.sort_values('Registro de')
             fig_barras_eventos = px.bar(conteo_eventos_df, x='Registro de', y='Cantidad', text='Cantidad', title=None);
             fig_barras_eventos.update_traces(textfont_size=14, textangle=0, textposition="outside", cliponaxis=False);
             fig_barras_eventos.update_layout(xaxis_title=None, margin=dict(l=20, r=20, t=10, b=20), height=300, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', uniformtext_minsize=8, uniformtext_mode='hide')


    # --- KPIs Comparativos ---
    # (Lógica sin cambios)
    kpi_comparativos_cards = []; periodos = { 'Semana': timedelta(weeks=1), '2 Semanas': timedelta(weeks=2), 'Mes': timedelta(days=30), '3 Meses': timedelta(days=90) }; fecha_referencia_kpi = fecha_maxima_datos if isinstance(fecha_maxima_datos, pd.Timestamp) else pd.Timestamp('now').normalize()
    if producto_seleccionado_kpi is not None and not df_prod_validos_kpi.empty:
        df_prod_kpi_seleccionado = df_prod_validos_kpi[df_prod_validos_kpi[COLUMNA_PRODUCTO] == producto_seleccionado_kpi].copy()
        if not df_prod_kpi_seleccionado.empty and COLUMNA_UNIDAD in df_prod_kpi_seleccionado.columns and COLUMNA_FECHA_PROD in df_prod_kpi_seleccionado.columns:
             unidad_kpi_prod = df_prod_kpi_seleccionado[COLUMNA_UNIDAD].iloc[0] if not df_prod_kpi_seleccionado[COLUMNA_UNIDAD].empty else 'Unid.'; df_prod_kpi = df_prod_kpi_seleccionado; df_prod_kpi['fecha_ref'] = pd.to_datetime(df_prod_kpi[COLUMNA_FECHA_PROD]).dt.normalize()
             for nombre_periodo, delta in periodos.items(): fin_actual=fecha_referencia_kpi; inicio_actual=fin_actual-delta+timedelta(days=1); fin_anterior=inicio_actual-timedelta(days=1); inicio_anterior=fin_anterior-delta+timedelta(days=1); df_prod_kpi['fecha_ref'] = pd.to_datetime(df_prod_kpi['fecha_ref']); actual_val = df_prod_kpi[(df_prod_kpi['fecha_ref'] >= inicio_actual) & (df_prod_kpi['fecha_ref'] <= fin_actual)][COLUMNA_CANTIDAD].sum(); anterior_val = df_prod_kpi[(df_prod_kpi['fecha_ref'] >= inicio_anterior) & (df_prod_kpi['fecha_ref'] <= fin_anterior)][COLUMNA_CANTIDAD].sum(); var = calcular_variacion(actual_val, anterior_val); clase_texto, texto_var = obtener_clase_texto_semaforo(var, es_produccion=True); card = crear_kpi_card(f"Prod ({unidad_kpi_prod}): {nombre_periodo}", texto_var); card.md = 3; card.children.children.children[1].className = f"{clase_texto} text-center fw-bold"; kpi_comparativos_cards.append(card)
        else:
             for nombre_periodo in periodos: card = crear_kpi_card(f"Prod: {nombre_periodo}", "Sin Datos Prod."); card.md = 3; card.children.children.children[1].className = f"{COLOR_TEXTO_GRIS} text-center fw-bold"; kpi_comparativos_cards.append(card)
    else:
        mensaje = "Selec. Prod." if producto_seleccionado_kpi is None else "Sin Datos Prod.";
        for nombre_periodo in periodos: card = crear_kpi_card(f"Prod: {nombre_periodo}", mensaje); card.md = 3; card.children.children.children[1].className = f"{COLOR_TEXTO_GRIS} text-center fw-bold"; kpi_comparativos_cards.append(card)
    if not df_incidentes_kpi.empty and COLUMNA_FECHA_INCID in df_incidentes_kpi.columns:
         if 'fecha_ref' not in df_incidentes_kpi.columns: df_incidentes_kpi['fecha_ref'] = pd.to_datetime(df_incidentes_kpi[COLUMNA_FECHA_INCID]).dt.normalize()
         df_inc_kpi_calc = df_incidentes_kpi.copy(); df_inc_kpi_calc['fecha_ref'] = pd.to_datetime(df_inc_kpi_calc['fecha_ref'])
         for nombre_periodo, delta in periodos.items():
             try: fin_actual=fecha_referencia_kpi; inicio_actual=fin_actual-delta+timedelta(days=1); fin_anterior=inicio_actual-timedelta(days=1); inicio_anterior=fin_anterior-delta+timedelta(days=1); actual_val = len(df_inc_kpi_calc[(df_inc_kpi_calc['fecha_ref'] >= inicio_actual) & (df_inc_kpi_calc['fecha_ref'] <= fin_actual)]); anterior_val = len(df_inc_kpi_calc[(df_inc_kpi_calc['fecha_ref'] >= inicio_anterior) & (df_inc_kpi_calc['fecha_ref'] <= fin_anterior)]); var = calcular_variacion(actual_val, anterior_val); clase_texto, texto_var = obtener_clase_texto_semaforo(var, es_produccion=False); card = crear_kpi_card(f"Incid: {nombre_periodo}", texto_var); card.md = 3; card.children.children.children[1].className = f"{clase_texto} text-center fw-bold"; kpi_comparativos_cards.append(card)
             except Exception as e_kpi_inc: print(f"Error KPI incidente {nombre_periodo}: {e_kpi_inc}"); card = crear_kpi_card(f"Incid: {nombre_periodo}", "Error Cálculo"); card.md = 3; card.children.children.children[1].className = f"{COLOR_TEXTO_GRIS} text-center fw-bold"; kpi_comparativos_cards.append(card)
    else:
         for nombre_periodo in periodos: card = crear_kpi_card(f"Incid: {nombre_periodo}", "Sin Datos Inc."); card.md = 3; card.children.children.children[1].className = f"{COLOR_TEXTO_GRIS} text-center fw-bold"; kpi_comparativos_cards.append(card)

    return texto_contador, fig_barras_eventos, texto_fechas_slider, kpi_comparativos_cards, kpi_generales_cards


# --- Callback para el Modal de Detalles (Usa la nueva función de filtro) ---
@callback(
    Output('home-modal-detalle', 'is_open'), Output('home-modal-titulo', 'children'), Output('home-modal-tabla-contenido', 'children'),
    Input('home-grafico-tipos-evento', 'clickData'),
    State('home-slider-rango-fechas', 'value'), State('home-dropdown-maquina', 'value'),
    prevent_initial_call=True
)
def mostrar_tabla_detalle(clickData, rango_fechas_slider, maquina_seleccionada):
    if clickData is None: raise PreventUpdate
    try:
        clicked_event_type_grafico = clickData['points'][0]['x']
        clicked_event_type_original = MAPEO_INVERSO_NOMBRES.get(clicked_event_type_grafico)
        if clicked_event_type_original is None: raise PreventUpdate
    except (KeyError, IndexError, TypeError): print("Error al extraer datos del click"); raise PreventUpdate

    # --- Cargar y Filtrar Datos (Usando nueva lógica) ---
    try:
        # Siempre utiliza el archivo RESPONSES_SIPROSA.csv
        df_original = pd.read_csv(CSV_FILE);
        date_cols = [COLUMNA_TIMESTAMP, COLUMNA_FECHA_PROD, COLUMNA_FECHA_MANT, COLUMNA_FECHA_INCID];
        for col in date_cols:
            if col in df_original.columns: df_original[col] = pd.to_datetime(df_original[col], errors='coerce')
        if COLUMNA_CANTIDAD in df_original.columns: df_original[COLUMNA_CANTIDAD] = pd.to_numeric(df_original[COLUMNA_CANTIDAD], errors='coerce')

        fecha_inicio_dt = pd.Timestamp.fromordinal(rango_fechas_slider[0]); fecha_fin_dt = pd.Timestamp.fromordinal(rango_fechas_slider[1])

        # 1. Filtrar por Fecha (igual que en update_home_page)
        df_filtrado_fecha = pd.DataFrame(); dfs_filtrados_por_fecha = []
        if COLUMNA_FECHA_PROD in df_original.columns: dfs_filtrados_por_fecha.append(df_original[(df_original[COLUMNA_EVENTO] == VALOR_PRODUCCION) & (df_original[COLUMNA_FECHA_PROD] >= fecha_inicio_dt) & (df_original[COLUMNA_FECHA_PROD] <= fecha_fin_dt)])
        if COLUMNA_FECHA_MANT in df_original.columns: dfs_filtrados_por_fecha.append(df_original[(df_original[COLUMNA_EVENTO] == VALOR_MANTENIMIENTO) & (df_original[COLUMNA_FECHA_MANT] >= fecha_inicio_dt) & (df_original[COLUMNA_FECHA_MANT] <= fecha_fin_dt)])
        # Ajuste importante: Para el modal, SIEMPRE incluimos filas con fecha de incidente en rango, sin importar el evento principal,
        # porque el filtro de máquina y tipo de evento se aplicará DESPUÉS.
        if COLUMNA_FECHA_INCID in df_original.columns: dfs_filtrados_por_fecha.append(df_original[(df_original[COLUMNA_FECHA_INCID] >= fecha_inicio_dt) & (df_original[COLUMNA_FECHA_INCID] <= fecha_fin_dt)])
        if COLUMNA_TIMESTAMP in df_original.columns: dfs_filtrados_por_fecha.append(df_original[(df_original[COLUMNA_EVENTO] == VALOR_OBSERVACIONES) & (df_original[COLUMNA_TIMESTAMP] >= fecha_inicio_dt) & (df_original[COLUMNA_TIMESTAMP] <= fecha_fin_dt)])
        if dfs_filtrados_por_fecha: df_filtrado_fecha = pd.concat(dfs_filtrados_por_fecha, ignore_index=True).drop_duplicates()


        # 2. Filtrar por Máquina (usando la función corregida)
        # PERO para el modal de INCIDENTES, queremos ver *todos* los asociados a la máquina
        if clicked_event_type_original == VALOR_INCIDENTES and maquina_seleccionada != VALOR_TODAS:
             # Filtro especial para modal de incidentes: incluir si la máquina de incidente coincide
             df_filtrado_final = df_filtrado_fecha[
                 (df_filtrado_fecha[COLUMNA_MAQUINA_INCID].astype(str).str.strip() == maquina_seleccionada) &
                 (df_filtrado_fecha[COLUMNA_FECHA_INCID].notna()) # Asegurar que realmente sea un incidente registrado
            ].copy() if COLUMNA_MAQUINA_INCID in df_filtrado_fecha.columns and COLUMNA_FECHA_INCID in df_filtrado_fecha.columns else pd.DataFrame()

        else:
             # Para otros tipos de evento o si es 'Todas', usar el filtro estándar
             df_filtrado_final = aplicar_filtro_maquina(df_filtrado_fecha, maquina_seleccionada)


        # --- Filtrar para la tabla específica del modal (Usar el valor *original*) ---
        if clicked_event_type_original == VALOR_INCIDENTES:
             # Ya hemos filtrado por máquina de incidente (si aplica) y fecha de incidente
             # Ahora solo nos aseguramos de tener el df filtrado
             df_tabla = df_filtrado_final.copy() # df_filtrado_final ya tiene los incidentes correctos
        elif clicked_event_type_original == VALOR_MANTENIMIENTO:
             # df_filtrado_final ya está filtrado por la máquina de mantenimiento correcta
             df_tabla = df_filtrado_final[(df_filtrado_final[COLUMNA_EVENTO] == VALOR_MANTENIMIENTO) & (df_filtrado_final.get(COLUMNA_REALIZO_MANTENIMIENTO) == VALOR_SI_MANTENIMIENTO)].copy() if COLUMNA_REALIZO_MANTENIMIENTO in df_filtrado_final.columns else df_filtrado_final[df_filtrado_final[COLUMNA_EVENTO] == VALOR_MANTENIMIENTO].copy()
        else: # Producción u Observaciones
             # df_filtrado_final ya está filtrado por la máquina de producción correcta (si aplica)
             df_tabla = df_filtrado_final[df_filtrado_final[COLUMNA_EVENTO] == clicked_event_type_original].copy()

    # Siempre utiliza el archivo RESPONSES_SIPROSA.csv
    except FileNotFoundError: return True, f"Error", html.Div(f"Archivo '{CSV_FILE}' no encontrado.")
    except Exception as e: print(f"Error al filtrar para tabla modal: {e}"); import traceback; traceback.print_exc(); return True, f"Error al cargar datos", html.Div("No se pudieron cargar los detalles.")

    # --- Preparar Tabla ---
    if df_tabla.empty: tabla_html = html.Div("No hay registros detallados para mostrar con los filtros actuales.")
    else:
        # Selección dinámica de columnas (Usar el valor *original*)
        columnas_mostrar = []; fecha_col_principal = None
        if clicked_event_type_original == VALOR_PRODUCCION:
            columnas_mostrar = [COLUMNA_FECHA_PROD, COLUMNA_HORA_INI_PROD, COLUMNA_HORA_FIN_PROD, COLUMNA_MAQUINA_PROD, COLUMNA_PRODUCTO, COLUMNA_CANTIDAD, COLUMNA_UNIDAD, COLUMNA_OBSERVACIONES]; fecha_col_principal = COLUMNA_FECHA_PROD
        elif clicked_event_type_original == VALOR_MANTENIMIENTO:
            columnas_mostrar = [COLUMNA_FECHA_MANT, COLUMNA_HORA_INI_MANT, COLUMNA_HORA_FIN_MANT, COLUMNA_MAQUINA_MANT, COLUMNA_TIPO_MANT, COLUMNA_DESC_MANT, COLUMNA_OBSERVACIONES]; fecha_col_principal = COLUMNA_FECHA_MANT
        elif clicked_event_type_original == VALOR_INCIDENTES:
            # Mostrar columnas relevantes para incidentes, incluyendo la máquina asociada
            columnas_mostrar = [COLUMNA_FECHA_INCID, COLUMNA_HORA_INI_INCID, COLUMNA_HORA_FIN_INCID, COLUMNA_MAQUINA_INCID, COLUMNA_DESC_INCID, COLUMNA_OBSERVACIONES, COLUMNA_EVENTO]; fecha_col_principal = COLUMNA_FECHA_INCID
        elif clicked_event_type_original == VALOR_OBSERVACIONES:
            columnas_mostrar = [COLUMNA_TIMESTAMP, COLUMNA_OBSERVACIONES]; fecha_col_principal = COLUMNA_TIMESTAMP
        else: columnas_mostrar = df_tabla.columns.tolist()

        # Ordenar por fecha principal y hora de inicio si existen
        if fecha_col_principal and fecha_col_principal in df_tabla.columns:
            hora_col_inicio = None
            if clicked_event_type_original == VALOR_PRODUCCION and COLUMNA_HORA_INI_PROD in df_tabla.columns: hora_col_inicio = COLUMNA_HORA_INI_PROD
            elif clicked_event_type_original == VALOR_MANTENIMIENTO and COLUMNA_HORA_INI_MANT in df_tabla.columns: hora_col_inicio = COLUMNA_HORA_INI_MANT
            elif clicked_event_type_original == VALOR_INCIDENTES and COLUMNA_HORA_INI_INCID in df_tabla.columns: hora_col_inicio = COLUMNA_HORA_INI_INCID

            sort_cols = [fecha_col_principal]
            if hora_col_inicio:
                # Convertir hora a objeto time para ordenar correctamente
                 try:
                     # Manejar 'a.m.' y 'p.m.' con puntos
                     df_tabla[hora_col_inicio + '_time'] = pd.to_datetime(df_tabla[hora_col_inicio].astype(str).str.replace('.', '', regex=False), format='%I:%M %p', errors='coerce').dt.time
                     sort_cols.append(hora_col_inicio + '_time')
                 except Exception as e_time:
                     print(f"Advertencia: No se pudo convertir la columna de hora '{hora_col_inicio}' para ordenar: {e_time}")
                     # Intentar ordenar solo por fecha si falla la conversión de hora
                     if len(sort_cols) > 1: sort_cols.pop()


            try:
                 df_tabla = df_tabla.sort_values(by=sort_cols, ascending=True, na_position='last')
                 # Eliminar columna temporal si se creó
                 if hora_col_inicio and hora_col_inicio + '_time' in df_tabla.columns:
                     df_tabla = df_tabla.drop(columns=[hora_col_inicio + '_time'])

            except Exception as e_sort: print(f"Error al ordenar tabla: {e_sort}")


        # Filtrar columnas existentes y formatear
        columnas_existentes = [col for col in columnas_mostrar if col in df_tabla.columns]; df_display = df_tabla[columnas_existentes].copy()
        for col_fecha in [COLUMNA_TIMESTAMP, COLUMNA_FECHA_PROD, COLUMNA_FECHA_MANT, COLUMNA_FECHA_INCID]:
            if col_fecha in df_display.columns:
                 df_display[col_fecha] = pd.to_datetime(df_display[col_fecha], errors='coerce')
                 # Evitar mostrar NaT si la conversión falla o la fecha es nula
                 df_display[col_fecha] = df_display[col_fecha].dt.strftime('%d/%m/%Y').fillna('')
        if COLUMNA_CANTIDAD in df_display.columns:
             # Formatear solo si no es nulo, luego convertir a string
             df_display[COLUMNA_CANTIDAD] = df_display[COLUMNA_CANTIDAD].apply(lambda x: f"{int(x):,}" if pd.notna(x) else '')

        tabla_html = dbc.Table.from_dataframe(df_display, striped=True, bordered=True, hover=True, responsive=True, class_name="align-middle")

    # Usar el nombre del gráfico para el título del modal
    modal_titulo = f"Detalle de: {clicked_event_type_grafico}"
    if clicked_event_type_original == VALOR_INCIDENTES:
         modal_titulo += " (Asociados a la Máquina Seleccionada)" if maquina_seleccionada != VALOR_TODAS else " (Todos)"


    return True, modal_titulo, tabla_html