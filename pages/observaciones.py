# pages/observaciones.py

import dash
from dash import dcc, html, Input, Output, callback, State, no_update
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
import re # Para expresiones regulares (limpieza de texto)
import io # Para manejar bytes de imagen
import base64 # Para codificar imagen para HTML

# Intentar importar WordCloud y stopwords, manejar error si no está instalado
try:
    from wordcloud import WordCloud, STOPWORDS
    import matplotlib.pyplot as plt
    wordcloud_available = True
except ImportError:
    WordCloud = None
    STOPWORDS = set()
    plt = None
    wordcloud_available = False
    print("ADVERTENCIA: Librerías 'wordcloud' y/o 'matplotlib' no encontradas. La nube de palabras no funcionará.")
    print("Instálalas con: pip install wordcloud matplotlib")


# --- Constantes ---
CSV_FILE = 'RESPONSES_SIPROSA.csv'
COLUMNA_TIMESTAMP = 'Timestamp'
COLUMNA_EVENTO = 'TIPO DE EVENTO A REGISTRAR'
COLUMNA_OBSERVACIONES = 'OBSERVACIONES ADICIONALES' # Asegúrate que este sea el nombre exacto
VALOR_OBSERVACIONES = 'Observaciones Generales'

# Lista básica de stopwords en español (puedes expandirla o usar NLTK para una mejor)
# Fuente: https://github.com/stopwords-iso/stopwords-es/blob/master/stopwords-es.txt (adaptada)
STOPWORDS_ES = set([
    'a', 'actualmente', 'acuerdo', 'adelante', 'ademas', 'además', 'afirmó', 'agregó', 'ahi', 'ahora', 'ahí', 'al', 'algo', 'alguna', 'algunas',
    'alguno', 'algunos', 'alla', 'alli', 'allí', 'alrededor', 'ambos', 'ampleamos', 'ante', 'anterior', 'antes', 'apenas', 'aproximadamente',
    'aquel', 'aquella', 'aquellas', 'aquello', 'aquellos', 'aqui', 'aquí', 'arriba', 'aseguró', 'asi', 'así', 'atras', 'aun', 'aunque', 'ayer',
    'añadió', 'aún', 'bajo', 'bastante', 'bien', 'buen', 'buena', 'buenas', 'bueno', 'buenos', 'cada', 'casi', 'cerca', 'cierta', 'ciertas',
    'cierto', 'ciertos', 'cinco', 'comentó', 'como', 'con', 'conocer', 'conseguimos', 'conseguir', 'considera', 'consideró', 'consigo',
    'consigue', 'consiguen', 'consigues', 'contra', 'cosas', 'creo', 'cual', 'cuales', 'cualquier', 'cuando', 'cuanto', 'cuatro', 'cuenta',
    'cómo', 'da', 'dado', 'dan', 'dar', 'de', 'debajo', 'debe', 'deben', 'debido', 'decir', 'dejó', 'del', 'delante', 'demasiado', 'demás',
    'dentro', 'deprisa', 'desde', 'despacio', 'despues', 'después', 'detras', 'detrás', 'dia', 'dias', 'dice', 'dicen', 'dicho', 'dieron',
    'diferente', 'diferentes', 'dijeron', 'dijo', 'dio', 'dispuso', 'disponible', 'disponibles', 'dla', 'dle', 'dlo', 'dos', 'durante', 'día',
    'días', 'e', 'ejemplo', 'el', 'ella', 'ellas', 'ello', 'ellos', 'embargo', 'empleais', 'emplean', 'emplear', 'empleas', 'empleo', 'en',
    'encima', 'encuentra', 'enfrente', 'enseguida', 'entonces', 'entre', 'era', 'erais', 'eramos', 'eran', 'eras', 'eres', 'es', 'esa',
    'esas', 'ese', 'eso', 'esos', 'esta', 'estaba', 'estabais', 'estabamos', 'estaban', 'estabas', 'estad', 'estada', 'estadas', 'estado',
    'estados', 'estais', 'estamos', 'estan', 'estando', 'estar', 'estaremos', 'estará', 'estarán', 'estarás', 'estaré', 'estaréis', 'estaría',
    'estaríais', 'estaríamos', 'estarían', 'estarías', 'estas', 'este', 'esto', 'estos', 'estoy', 'estuvo', 'está', 'estáis', 'están', 'estás',
    'ex', 'excepto', 'existe', 'existen', 'explicó', 'expresó', 'fin', 'fue', 'fuera', 'fuerais', 'fueramos', 'fueran', 'fueras', 'fueron',
    'fuese', 'fueseis', 'fuesen', 'fueses', 'fui', 'fuimos', 'fuiste', 'fuisteis', 'general', 'gran', 'grandes', 'gueno', 'ha', 'haber',
    'habia', 'habida', 'habidas', 'habido', 'habidos', 'habiendo', 'habla', 'hablan', 'habremos', 'habrá', 'habrán', 'habrás', 'habré',
    'habréis', 'habría', 'habríais', 'habríamos', 'habrían', 'habrías', 'habéis', 'había', 'habíais', 'habíamos', 'habían', 'habías', 'hace',
    'haceis', 'hacemos', 'hacen', 'hacer', 'hacerlo', 'haces', 'hacia', 'haciendo', 'hago', 'han', 'has', 'hasta', 'hay', 'haya', 'hayamos',
    'hayan', 'hayas', 'hayáis', 'he', 'hecho', 'hemos', 'hicieron', 'hizo', 'horas', 'hoy', 'hube', 'hubiera', 'hubierais', 'hubieramos',
    'hubieran', 'hubieras', 'hubieron', 'hubiese', 'hubieseis', 'hubiesen', 'hubieses', 'hubimos', 'hubiste', 'hubisteis', 'hubo', 'hubó', 'igual',
    'incluso', 'indicó', 'informo', 'informó', 'intenta', 'intentais', 'intentamos', 'intentan', 'intentar', 'intentas', 'intento', 'ir',
    'junto', 'la', 'lado', 'largo', 'las', 'le', 'lejos', 'les', 'llegó', 'lleva', 'llevar', 'lo', 'los', 'luego', 'lugar', 'manera',
    'manifestó', 'mas', 'mayor', 'me', 'mediante', 'medio', 'mejor', 'mencionó', 'menos', 'menudo', 'mi', 'mia', 'mias', 'mientras', 'mio',
    'mios', 'mis', 'misma', 'mismas', 'mismo', 'mismos', 'modo', 'momento', 'mucha', 'muchas', 'muchisima', 'muchisimas', 'muchisimo',
    'muchisimos', 'mucho', 'muchos', 'muy', 'más', 'mí', 'mía', 'mías', 'mío', 'míos', 'nada', 'nadie', 'ni', 'ninguna', 'ningunas',
    'ninguno', 'ningunos', 'no', 'nos', 'nosotras', 'nosotros', 'nuestra', 'nuestras', 'nuestro', 'nuestros', 'nueva', 'nuevas', 'nuevo',
    'nuevos', 'nunca', 'o', 'ocho', 'os', 'otra', 'otras', 'otro', 'otros', 'pais', 'para', 'parece', 'parte', 'partir', 'pasada', 'pasado',
    'paìs', 'peor', 'pero', 'pesar', 'poca', 'pocas', 'poco', 'pocos', 'podeis', 'podemos', 'poder', 'podria', 'podriais', 'podriamos',
    'podrian', 'podrias', 'podrá', 'podrán', 'podría', 'podrían', 'poner', 'por', 'por qué', 'porque', 'posible', 'primer', 'primera',
    'primeras', 'primero', 'primeros', 'principalmente', 'pronto', 'propia', 'propias', 'propio', 'propios', 'proximo', 'próximo', 'próximos',
    'pudo', 'pueda', 'puede', 'pueden', 'puedo', 'pues', 'punto', 'q', 'qeu', 'que', 'quedó', 'queremos', 'quien', 'quienes', 'quiere', 'quiza',
    'quizas', 'quizá', 'quizás', 'qué', 'quién', 'quiénes', 'realizado', 'realizar', 'realizó', 'repente', 'respecto', 'sal', 'salvo', 'se',
    'sea', 'seamos', 'sean', 'seas', 'segun', 'segunda', 'segundo', 'según', 'seis', 'ser', 'sera', 'seremos', 'será', 'serán', 'serás',
    'seré', 'seréis', 'sería', 'seríais', 'seríamos', 'serían', 'serías', 'seáis', 'señaló', 'si', 'sido', 'siempre', 'siendo', 'siete',
    'sigue', 'siguiente', 'sin', 'sino', 'sobre', 'sois', 'sola', 'solamente', 'solas', 'solo', 'solos', 'somos', 'son', 'soy', 'soyos', 'su',
    'supuesto', 'sus', 'suya', 'suyas', 'suyo', 'suyos', 'sí', 'sólo', 'tal', 'tambien', 'también', 'tampoco', 'tan', 'tanta', 'tantas',
    'tanto', 'tantos', 'tarde', 'te', 'temprano', 'tendremos', 'tendrá', 'tendrán', 'tendrás', 'tendré', 'tendréis', 'tendría', 'tendríais',
    'tendríamos', 'tendrían', 'tendrías', 'tened', 'teneis', 'tenemos', 'tener', 'tenga', 'tengamos', 'tengan', 'tengas', 'tengo', 'tengáis',
    'tenida', 'tenidas', 'tenido', 'tenidos', 'teniendo', 'tenéis', 'tenía', 'teníais', 'teníamos', 'tenían', 'tenías', 'tercera', 'terceros',
    'ti', 'tiempo', 'tiene', 'tienen', 'tienes', 'toda', 'todas', 'todavia', 'todavía', 'todo', 'todos', 'total', 'trabaja', 'trabajais',
    'trabajamos', 'trabajan', 'trabajar', 'trabajas', 'trabajo', 'tras', 'trata', 'través', 'tres', 'tu', 'tus', 'tuya', 'tuyas', 'tuyo',
    'tuyos', 'tú', 'ultima', 'ultimo', 'ultimas', 'ultimos', 'un', 'una', 'unas', 'uno', 'unos', 'usa', 'usais', 'usamos', 'usan', 'usar',
    'usas', 'uso', 'usted', 'ustedes', 'va', 'vais', 'valor', 'vamos', 'van', 'varias', 'varios', 'vaya', 'veces', 'verá', 'verdad',
    'verdadera', 'verdadero', 'vez', 'vosotras', 'vosotros', 'voy', 'vuestra', 'vuestras', 'vuestro', 'vuestros', 'y', 'ya', 'yo', 'él', 'ésa',
    'ésas', 'ése', 'ésos', 'ésta', 'éstas', 'éste', 'éstos', 'última', 'últimas', 'último', 'últimos'
] + list(STOPWORDS)) # Combinar con stopwords de la librería si está disponible

# --- Registro de la Página ---
dash.register_page(__name__, path='/observaciones', title='Observaciones', name='Observaciones')

# --- Layout Helper ---
def layout():
    children = [
        dbc.Row(dbc.Col(html.H1("Observaciones y Feedback", className="text-center display-4 my-4"))),
        dbc.Row([
             dbc.Col(dbc.Card(dbc.CardBody([
                      html.Label('Rango Fechas Observaciones:', className="card-title mb-2"),
                      dcc.RangeSlider(id='obs-slider-fechas', marks=None, step=1, tooltip={"placement": "bottom", "always_visible": True}, className="p-0", disabled=True), # Deshabilitado inicial
                      html.Div(id='obs-output-fechas', className='text-center text-muted small mt-2')
             ])), width=12, className="mb-3")
        ]),
        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardHeader("Listado de Observaciones"),
                dbc.CardBody(dbc.Spinner(html.Div(id='obs-tabla-observaciones')), style={'maxHeight': '500px', 'overflowY': 'auto'})
            ]), width=12, md=6, className="mb-3"),
            dbc.Col(dbc.Card([
                dbc.CardHeader("Nube de Palabras Clave"),
                dbc.CardBody(dbc.Spinner(dcc.Graph(id='obs-wordcloud', config={'displayModeBar': False})))
            ]), width=12, md=6, className="mb-3")
        ], className="align-items-stretch"),
    ]

    # Mensaje si wordcloud no está disponible
    if not wordcloud_available:
        children.insert(1, dbc.Row(dbc.Col(dbc.Alert("Advertencia: Instala 'wordcloud' y 'matplotlib' para ver la nube de palabras.", color="warning"))))

    return dbc.Container(children, fluid=True, className="dbc mt-4")


# --- Callbacks ---

# Callback para inicializar controles de esta página
@callback(
    Output('obs-slider-fechas', 'min'),
    Output('obs-slider-fechas', 'max'),
    Output('obs-slider-fechas', 'value'),
    Output('obs-slider-fechas', 'disabled'),
    Input('store-main-data', 'data') # Disparado por el store
)
def inicializar_controles_observaciones(data_json):
    if not data_json:
        return 0, 1, [0, 1], True
    try:
        df = pd.read_json(data_json, orient='split')
        if COLUMNA_TIMESTAMP not in df.columns or COLUMNA_EVENTO not in df.columns:
            print("Error: Faltan columnas Timestamp o Evento en inicializar_controles_observaciones")
            return 0, 1, [0, 1], True

        df[COLUMNA_TIMESTAMP] = pd.to_datetime(df[COLUMNA_TIMESTAMP], errors='coerce')

        # Filtrar por observaciones
        df_obs = df[df[COLUMNA_EVENTO] == VALOR_OBSERVACIONES].copy()

        if df_obs.empty or df_obs[COLUMNA_TIMESTAMP].isna().all():
            print("No hay observaciones con fechas válidas.")
            return 0, 1, [0, 1], True # Deshabilitar slider si no hay datos

        min_fecha = df_obs[COLUMNA_TIMESTAMP].min()
        max_fecha = df_obs[COLUMNA_TIMESTAMP].max()
        slider_min = min_fecha.toordinal()
        slider_max = max_fecha.toordinal()
        slider_value = [slider_min, slider_max]
        slider_disabled = False

        return slider_min, slider_max, slider_value, slider_disabled

    except Exception as e:
        print(f"Error procesando datos del store en inicializar_controles_observaciones: {e}")
        traceback.print_exc()
        return 0, 1, [0, 1], True


# Callback para actualizar la tabla y la nube de palabras
@callback(
    Output('obs-tabla-observaciones', 'children'),
    Output('obs-wordcloud', 'figure'),
    Output('obs-output-fechas', 'children'),
    Input('obs-slider-fechas', 'value'),
    State('store-main-data', 'data') # Leer datos del store
)
def update_observaciones_page(rango_fechas_slider, data_json):
    if not data_json or rango_fechas_slider is None:
        empty_fig = go.Figure()
        empty_fig.update_layout(title="Esperando datos...", title_x=0.5, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis={'showticklabels': False, 'zeroline': False}, yaxis={'showticklabels': False, 'zeroline': False})
        return html.Div("Cargando..."), empty_fig, "..."

    # --- Carga y Filtro Base ---
    try:
        df_original = pd.read_json(data_json, orient='split')
        if COLUMNA_TIMESTAMP not in df_original.columns or COLUMNA_EVENTO not in df_original.columns or COLUMNA_OBSERVACIONES not in df_original.columns:
             print("Error: Faltan columnas esenciales en update_observaciones_page")
             empty_fig = go.Figure()
             empty_fig.update_layout(title="Error: Faltan columnas", title_x=0.5, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis={'showticklabels': False, 'zeroline': False}, yaxis={'showticklabels': False, 'zeroline': False})
             return html.Div("Error al cargar datos (faltan columnas)."), empty_fig, "Error"

        df_original[COLUMNA_TIMESTAMP] = pd.to_datetime(df_original[COLUMNA_TIMESTAMP], errors='coerce')

        # Filtrar por observaciones Y que la observación no sea nula/vacía
        df_obs_base = df_original[
            (df_original[COLUMNA_EVENTO] == VALOR_OBSERVACIONES) &
            (df_original[COLUMNA_OBSERVACIONES].notna()) &
            (df_original[COLUMNA_OBSERVACIONES].str.strip() != '')
        ].copy()

    except Exception as e:
        print(f"Error leyendo/parseando datos del store en update_observaciones_page: {e}")
        traceback.print_exc()
        empty_fig = go.Figure()
        empty_fig.update_layout(title="Error al cargar datos", title_x=0.5, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis={'showticklabels': False, 'zeroline': False}, yaxis={'showticklabels': False, 'zeroline': False})
        return html.Div("Error al cargar datos."), empty_fig, "Error"

    # --- Filtrado por Slider ---
    df_filtrado = pd.DataFrame(columns=df_obs_base.columns)
    texto_fechas_slider = "..."
    try:
        fecha_inicio_dt = pd.Timestamp.fromordinal(rango_fechas_slider[0])
        fecha_fin_dt = pd.Timestamp.fromordinal(rango_fechas_slider[1])
        texto_fechas_slider = f"{fecha_inicio_dt.strftime('%d/%m/%y')} - {fecha_fin_dt.strftime('%d/%m/%y')}"

        # Filtrar observaciones base por fecha y que tengan timestamp válido
        df_filtrado = df_obs_base[
            (df_obs_base[COLUMNA_TIMESTAMP].notna()) &
            (df_obs_base[COLUMNA_TIMESTAMP] >= fecha_inicio_dt) &
            (df_obs_base[COLUMNA_TIMESTAMP] <= fecha_fin_dt)
        ].copy()

    except Exception as e:
        print(f"Error durante el filtrado por fecha: {e}")
        traceback.print_exc()
        # Continuar con df_filtrado vacío

    # --- Generación de Tabla ---
    tabla_html = html.Div("No hay observaciones en el período seleccionado.")
    if not df_filtrado.empty:
        df_display_tabla = df_filtrado[[COLUMNA_TIMESTAMP, COLUMNA_OBSERVACIONES]].copy()
        df_display_tabla.rename(columns={COLUMNA_TIMESTAMP: 'Fecha', COLUMNA_OBSERVACIONES: 'Observación'}, inplace=True)
        df_display_tabla['Fecha'] = df_display_tabla['Fecha'].dt.strftime('%d/%m/%Y %H:%M') # Incluir hora puede ser útil
        df_display_tabla = df_display_tabla.sort_values(by='Fecha', ascending=False) # Más recientes primero
        tabla_html = dbc.Table.from_dataframe(df_display_tabla, striped=True, bordered=True, hover=True, responsive=True, class_name="align-middle small")

    # --- Generación de Nube de Palabras ---
    wordcloud_fig = go.Figure()
    wordcloud_fig.update_layout(title="No hay datos para generar nube de palabras", title_x=0.5, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis={'showticklabels': False, 'zeroline': False}, yaxis={'showticklabels': False, 'zeroline': False})

    # Solo intentar generar si la librería está disponible y hay datos filtrados
    if wordcloud_available and not df_filtrado.empty:
        try:
            # 1. Concatenar todas las observaciones en un solo texto
            # Asegurarse que sean strings y manejar NaN
            text = df_filtrado[COLUMNA_OBSERVACIONES].astype(str).str.cat(sep=' ')

            if text.strip(): # Procesar solo si hay texto
                # 2. Limpieza básica del texto
                text = text.lower() # Convertir a minúsculas
                text = re.sub(r'[^\w\s]', '', text) # Quitar puntuación
                text = re.sub(r'\d+', '', text) # Quitar números (opcional)

                # 3. Crear objeto WordCloud
                wc = WordCloud(
                    background_color="rgba(0, 0, 0, 0)", # Fondo transparente
                    mode="RGBA", # Necesario para fondo transparente
                    width=800,
                    height=400,
                    stopwords=STOPWORDS_ES, # Usar la lista de stopwords
                    max_words=100,          # Limitar el número de palabras
                    colormap='viridis',     # Paleta de colores (puedes cambiarla)
                    contour_width=1,
                    contour_color='steelblue', # Color del contorno de las palabras
                    prefer_horizontal=0.9 # Preferir palabras horizontales
                ).generate(text)

                # 4. Convertir a imagen para Dash
                img_bytes = io.BytesIO()
                wc.to_image().save(img_bytes, format='PNG')
                img_base64 = base64.b64encode(img_bytes.getvalue()).decode('utf-8')
                img_data_uri = f'data:image/png;base64,{img_base64}'

                # 5. Crear figura Plotly con la imagen
                wordcloud_fig = go.Figure(go.Image(source=img_data_uri))
                wordcloud_fig.update_layout(
                    margin=dict(l=0, r=0, t=0, b=0), # Sin márgenes
                    xaxis={'showgrid': False, 'showticklabels': False, 'zeroline': False},
                    yaxis={'showgrid': False, 'showticklabels': False, 'zeroline': False},
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                )

        except Exception as e_wc:
            print(f"!!!!!! ERROR generando nube de palabras: {e_wc}")
            traceback.print_exc()
            wordcloud_fig.update_layout(title="Error al generar nube de palabras", title_x=0.5)


    return tabla_html, wordcloud_fig, texto_fechas_slider