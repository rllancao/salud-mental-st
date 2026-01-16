import streamlit as st
from supabase import Client
import json
import time
import base64

# --- DEBES RELLENAR ESTOS DICCIONARIOS ---

# 1. DICCIONARIO DE ALTERNATIVAS
# Rellena esto con las alternativas (en string) para cada pregunta
# El ejemplo de la imagen tiene 6 alternativas, pero puedes poner las que necesites.
D48_QUESTIONS_OPTIONS = {
    1: ["2/1", "2/2", "2/3", "2/4"], 
    2: ["3/3", "3/5", "3/4", "3/2"], 
    3: ["3/3", "6/0", "2/5", "3/1"],
    4: ["6/2", "2/4", "4/2", "1/6"],
    5: ["4/4", "5/5", "6/6", "1/1"],
    6: ["3/3", "1/1", "2/2", "4/4"],
    7: ["4/2", "4/1", "4/4", "2/4"],
    8: ["4/1", "6/4", "5/2", "4/0"],
    9: ["4/1", "3/3", "2/4", "4/2"],        
    10: ["4/4", "2/3", "2/1", "3/3"],
    11: ["1/4", "6/2", "4/0", "1/3"],
    12: ["6/1", "4/5", "5/4", "3/2"],
    13: ["0/2", "1/2", "3/3", "3/4"],
    14: ["2/1", "4/1", "0/2", "4/2"],
    15: ["4/4", "6/4", "4/5", "3/2"],
    16: ["6/1", "6/2", "6/4", "6/3"],
    17: ["5/3", "5/2", "5/1", "5/4"],
    18: ["3/4", "3/3", "3/2", "3/1"],
    19: ["2/1", "2/2", "2/3", "2/4"],
    20: ["3/4", "3/1", "3/2", "3/5"],
    21: ["6/4", "6/5", "3/2", "6/1"],
    22: ["3/1", "3/2", "3/3", "3/4"],
    23: ["4/3", "4/1", "4/2", "4/5"],
    24: ["2/6", "2/4", "2/1", "6/3"],
    25: ["4/1", "6/2", "4/4", "4/0"],
    26: ["5/3", "5/2", "6/1", "5/4"],
    27: ["6/1", "6/2", "6/5", "6/0"],
    28: ["3/2", "4/1", "4/3", "3/1"],
    29: ["1/3", "4/4", "5/3", "0/2"],
    30: ["1/4", "0/3", "0/5", "0/6"],
    31: ["0/5", "4/1", "4/0", "3/0"],
    32: ["2/0", "6/0", "6/1", "6/4"],
    33: ["6/5", "6/6", "4/3", "2/3"],
    34: ["3/2", "3/3", "3/6", "2/3"],
    35: ["1/2", "4/3", "0/2", "0/4"],
    36: ["1/2", "2/2", "2/1", "1/4"],
    37: ["5/4", "2/5", "1/3", "4/5"],  
    38: ["5/4", "2/5", "1/3", "4/5"],
    39: ["2/2", "5/5", "6/6", "6/4"],
    40: ["1/2", "6/5", "6/0", "2/4"],
    41: ["4/1", "4/2", "6/0", "4/3"],
    42: ["5/1", "5/5", "6/2", "4/3"],
    43: ["5/1", "2/4", "2/1", "2/6"],
    # ... Añade las alternativas para las 44 preguntas ...
    44: ["5/1", "2/4", "2/1", "2/6"] # Placeholder
}

# 2. DICCIONARIO DE RESPUESTAS CORRECTAS
D48_CORRECT_ANSWERS = {
    1: "1/2",
    2: "3/5", 
    3: "3/1", 
    4: "4/2",
    5: "5/5",
    6: "1/1",
    7: "4/1",
    8: "6/4",
    9: "4/2",
    10: "4/4",
    11: "4/0",
    12: "3/2",
    13: "3/4",
    14: "4/2",
    15: "6/4",
    16: "6/2",
    17: "5/4",
    18: "3/4",
    19: "2/3",
    20: "3/5",
    21: "6/5",
    22: "3/3",
    23: "4/2",
    24: "2/4",
    25: "4/0",
    26: "5/3",
    27: "6/0",
    28: "4/3",
    29: "0/2",
    30: "0/6",
    31: "3/0",
    32: "6/0",
    33: "6/6",
    34: "3/6",
    35: "0/2",
    36: "2/1",
    37: "5/4",
    38: "4/5",
    39: "6/6",
    40: "6/0",
    41: "4/3",
    42: "5/5",
    43: "2/6",
    44: "2/4" # Placeholder
}

# --- Tablas de Puntuación (sin cambios) ---
D48_PERCENTIL_TABLE = {
    "12-13": {95: 38, 90: 35, 75: 32, 50: 27, 25: 22, 10: 14, 5: 9},
    "14-15": {95: 39, 90: 37, 75: 33, 50: 28, 25: 23, 10: 15, 5: 11},
    "16-17": {95: 41, 90: 39, 75: 34, 50: 29, 25: 24, 10: 16, 5: 12},
    "18-65": {95: 41, 90: 40, 75: 36, 50: 31, 25: 25, 10: 20, 5: 16}
}
D48_INTERPRETATION_MAP = {
    (95, 100): "Superior",
    (90, 94): "Superior",
    (75, 89): "Superior al promedio",
    (26, 74): "Promedio",
    (10, 25): "Inferior al promedio",
    (5, 9): "Inferior",
    (0, 4): "Deficiente"
}

def get_age_group(edad):
    if not isinstance(edad, (int, float)): return "18-65"
    if 12 <= edad <= 13: return "12-13"
    if 14 <= edad <= 15: return "14-15"
    if 16 <= edad <= 17: return "16-17"
    if 18 <= edad <= 65: return "18-65"
    return "18-65"

def get_interpretation_from_percentile(percentil):
    for (min_p, max_p), interpretation in D48_INTERPRETATION_MAP.items():
        if min_p <= percentil <= max_p:
            return interpretation
    return "N/A"

def get_image_as_base64(path):
    """Encodes an image file to a base64 string for embedding in HTML."""
    try:
        with open(path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
    except FileNotFoundError:
        return None

def calcular_d48(respuestas_usuario, edad_paciente):
    # 1. Calcular puntaje total
    puntaje_total = 0
    respuestas_correctas_db = {}
    for i in range(1, 45):
        pregunta_key = f"pregunta_{i}"
        respuesta_dada = respuestas_usuario.get(pregunta_key)
        respuesta_correcta = D48_CORRECT_ANSWERS.get(i)
        
        if respuesta_dada == respuesta_correcta:
            respuestas_correctas_db[pregunta_key] = 1
            puntaje_total += 1
        else:
            respuestas_correctas_db[pregunta_key] = 0

    # 2. Determinar Percentil
    age_group = get_age_group(edad_paciente)
    score_table = D48_PERCENTIL_TABLE[age_group]
    
    table_scores = list(score_table.values())
    closest_score = min(table_scores, key=lambda x: abs(x - puntaje_total))
    
    percentil = 0
    for p, score in sorted(score_table.items(), reverse=True):
        if score == closest_score:
            percentil = p
            break
            
    # 3. Determinar Interpretación
    interpretacion = get_interpretation_from_percentile(percentil)

    return puntaje_total, percentil, interpretacion, respuestas_correctas_db


def crear_interfaz_d48(supabase: Client):
    # --- CONTROL DE ESTADO Y SCROLL ---
    
    # Inicializar estado si no existe
    if 'd48_started' not in st.session_state:
        st.session_state.d48_started = False
        
    # --- SCROLL TO TOP ROBUSTO ---
    # Inyectamos el estado 'd48_started' en el script para que cambie cuando
    # el usuario presiona "Empezar Test", forzando la re-ejecución del scroll.
    st.components.v1.html(
        f"""
        <script>
            // Status: {st.session_state.d48_started} (Fuerza actualización al cambiar estado)
            
            var topElement = window.parent.document.getElementById('inicio_pagina');
            if (topElement) {{
                topElement.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
            }} else {{
                var main = window.parent.document.querySelector('section.main');
                if (main) {{
                    main.scrollTo(0, 0);
                }} else {{
                    window.scrollTo(0, 0);
                }}
            }}
        </script>
        """, 
        height=0
    )

    st.title("Test de Dominós (D-48)")
    st.markdown("---")

    # --- Estado 1: Instrucciones (Pantalla Previa) ---
    if not st.session_state.d48_started:
        st.info(
            """
            **LO QUE USTED VA A HACER:** Esta prueba mide su capacidad lógica utilizando fichas de dominó.
            Debe identificar la lógica de la secuencia y seleccionar la ficha que continúa la serie.
            \n**NO PRESIONE EL BOTÓN DE "EMPEZAR" HASTA QUE SE LE ORDENE.**
            """
        )
        
        # --- EJEMPLO ---
        st.write("**EJEMPLO:**")
        st.write("""Indique el valor de la figura que falta: En este caso, la respuesta correcta es 2/4, ya que como vemos en la imagen,
        la secuencia sigue un patrón donde el número de puntos en cada mitad de las fichas se mantiene. El 2 indica el valor que va arriba del dominó faltante,
        y el 4 el valor que va abajo. Por lo tanto, la ficha que completa la secuencia es 2/4.
                 """)
        try:
            st.image("d48_images/ejemplo2.png", width=400)
        except Exception:
            st.warning("Imagen de ejemplo 'd48_images/ejemplo2.png' no encontrada.")
            
        opciones_ejemplo = D48_QUESTIONS_OPTIONS.get(0, ["1/1", "2/2", "3/3", "2/4"]) 
        st.radio(
            "Alternativas para el ejemplo",
            opciones_ejemplo,
            key="ejemplo_intro",
            horizontal=True,
            index=None,
            label_visibility="collapsed"
        )

        st.warning(
            """
            **TIEMPO LÍMITE:**
            HAY 44 PREGUNTAS Y USTED TIENE **SOLO 30 MINUTOS** PARA CONTESTAR.
            TRABAJE RÁPIDO Y CONTESTE LO MEJOR QUE PUEDA.
            """
        )
        
        st.markdown("---")
        comprende = st.checkbox("Sí, comprendo las instrucciones.", key="comprende_d48")
        st.markdown("---")

        if st.button("Empezar Test", type="primary"):
            st.session_state.d48_started = True
            st.session_state.d48_comprende = comprende
            st.session_state.d48_start_time = time.time()
            st.session_state.d48_submitted = False
            st.rerun()

    # --- Estado 2: El Test (Con Temporizador) ---
    else:
        # Inicializar tiempos si se recarga la página
        if 'd48_start_time' not in st.session_state:
            st.session_state.d48_start_time = time.time()
        if 'd48_submitted' not in st.session_state:
            st.session_state.d48_submitted = False

        # Cálculo del tiempo
        elapsed_time = time.time() - st.session_state.d48_start_time
        remaining_time = 1800 - elapsed_time # 30 minutos = 1800 segundos
        is_time_up = remaining_time <= 0

        # --- Mostrar Temporizador GIF ---
        if not st.session_state.get('d48_submitted', False):
            gif_base64 = get_image_as_base64("30-minute.gif")
            if gif_base64:
                timer_html = f"""
                <style>
                    .fixed-gif-timer {{
                        position: fixed;
                        top: 80px;
                        right: 2rem;
                        width: 150px;
                        padding: 10px;
                        background-color: #ffffff;
                        border: 2px solid #e6e6e6;
                        border-radius: 0.5rem;
                        z-index: 999;
                        text-align: center;
                        box-shadow: 0px 2px 5px rgba(0,0,0,0.1);
                    }}
                </style>
                <div class="fixed-gif-timer">
                    <h5 style='margin-bottom: 5px; color: #555; font-size: 0.9rem;'>Tiempo Restante</h5>
                    <img src="data:image/gif;base64,{gif_base64}" width="100%">
                </div>
                """
                st.markdown(timer_html, unsafe_allow_html=True)

        respuestas_usuario = {}

        with st.form(key="d48_form"):
            # --- BUCLE PARA LAS 44 PREGUNTAS ---
            for i in range(1, 45):
                st.write(f"**{i}.- Indique el valor de la figura que falta:**")
                
                try:
                    st.image(f"d48_images/pregunta_{i}.png", width=400)
                except Exception:
                    st.warning(f"Imagen 'd48_images/pregunta_{i}.png' no encontrada.")

                opciones = D48_QUESTIONS_OPTIONS.get(i, [])
                if not opciones:
                    st.error(f"Error: No se encontraron alternativas para la pregunta {i}.")
                    continue

                respuestas_usuario[f"pregunta_{i}"] = st.radio(
                    f"Alternativas para la pregunta {i}",
                    opciones,
                    key=f"q_{i}",
                    horizontal=True,
                    index=None,
                    label_visibility="collapsed"
                )
                if i < 44:
                    st.markdown("---")

            siguiente_button = st.form_submit_button("Finalizar y Guardar")

        # --- Lógica de Envío (Manual o Automática) ---
        if siguiente_button or is_time_up:
            if not st.session_state.d48_submitted:
                st.session_state.d48_submitted = True

                if 'ficha_id' not in st.session_state:
                    st.error("Error crítico: No se encontró el ID de la ficha de ingreso.")
                    return
                    
                if 'datos_paciente' not in st.session_state or 'edad' not in st.session_state.datos_paciente:
                     st.error("Error crítico: No se encontraron los datos del paciente (edad).")
                     return
                edad_paciente = st.session_state.datos_paciente.get('edad') or 18 

                if is_time_up:
                    st.warning("⏳ El tiempo se ha acabado. Se enviarán las respuestas registradas hasta ahora.")

                # Verificar preguntas solo si el tiempo NO se ha acabado
                errores = []
                if not is_time_up:
                    errores = [f"Pregunta {i}" for i in range(1, 45) if respuestas_usuario.get(f"pregunta_{i}") is None]
                
                if errores:
                    st.error("Por favor, responda todas las preguntas antes de finalizar: " + ", ".join(errores))
                    st.session_state.d48_submitted = False # Permitir reintentar
                else:
                    with st.spinner("Calculando y guardando resultados..."):
                        
                        # Calcular resultados
                        puntaje_total, percentil, interpretacion, respuestas_db = calcular_d48(respuestas_usuario, edad_paciente)

                        # Guardar datos
                        d48_data_to_save = {
                            "id": st.session_state.ficha_id,
                            "comprende": st.session_state.get("d48_comprende", False),
                            **respuestas_db, 
                            "percentil": percentil,
                            "puntaje": puntaje_total,
                            "interpretacion": interpretacion
                        }
                        
                        try:
                            response = supabase.from_('test_d48').insert(d48_data_to_save).execute()
                            if response.data:
                                # Guardar datos para el PDF
                                if 'form_data' not in st.session_state:
                                    st.session_state.form_data = {}
                                st.session_state.form_data['test_d48'] = {
                                    "puntaje": puntaje_total,
                                    "percentil": percentil,
                                    "interpretacion": interpretacion
                                }
                                
                                # Limpiar variables de sesión
                                for key in ['d48_started', 'd48_comprende', 'd48_start_time', 'd48_submitted']:
                                    if key in st.session_state:
                                        del st.session_state[key]

                                st.session_state.current_test_index += 1
                                st.rerun()
                            else:
                                st.error(f"Error al guardar los resultados: {response.error.message if response.error else 'Error desconocido'}")
                        except Exception as e:
                            st.error(f"Ocurrió una excepción al intentar guardar los resultados: {e}")

        # Actualizar el reloj
        elif not st.session_state.d48_submitted:
            time.sleep(1)
            st.rerun()