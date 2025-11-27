import streamlit as st
from supabase import Client
import json

# --- DEBES RELLENAR ESTOS DICCIONARIOS ---

# 1. DICCIONARIO DE ALTERNATIVAS
# Rellena esto con las alternativas (en string) para cada pregunta
# El ejemplo de la imagen tiene 6 alternativas, pero puedes poner las que necesites.
D48_QUESTIONS_OPTIONS = {
    1: ["2/1", "2/2", "2/3", "2/4"], # Ejemplo de 6 alternativas
    2: ["3/3", "3/5", "3/4", "3/2"], # Ejemplo de 4 alternativas
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
# Rellena esto con la alternativa de texto correcta para cada pregunta
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

# --- FUNCIÓN DE CÁLCULO MODIFICADA ---
def calcular_d48(respuestas_usuario, edad_paciente):
    
    # 1. Calcular puntaje total (respuestas correctas 1/0)
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

    # 2. Determinar Percentil (LÓGICA DEL MÁS CERCANO)
    age_group = get_age_group(edad_paciente)
    score_table = D48_PERCENTIL_TABLE[age_group]
    
    # Encontrar el puntaje de la tabla más cercano al puntaje del usuario
    table_scores = list(score_table.values())
    closest_score = min(table_scores, key=lambda x: abs(x - puntaje_total))
    
    # Encontrar el percentil más alto que corresponde a ese puntaje cercano
    percentil = 0
    # Iterar en orden descendente de percentil para asignar el más alto en caso de empate
    for p, score in sorted(score_table.items(), reverse=True):
        if score == closest_score:
            percentil = p
            break
            
    # 3. Determinar Interpretación
    interpretacion = get_interpretation_from_percentile(percentil)

    return puntaje_total, percentil, interpretacion, respuestas_correctas_db


def crear_interfaz_d48(supabase: Client):
    st.components.v1.html("<script>window.top.scrollTo(0, 0);</script>", height=0)
    st.title("Test de Dominós (D-48)")
    # ... (Instrucciones) ...
    st.info(
        """
        **Instrucciones:** A continuación, se le presentarán 44 problemas.
        Cada problema consiste en un grupo de fichas de dominó. 
        Deberá identificar la lógica de la secuencia e indicar el valor de la figura que falta.
        """
    )

    with st.form(key="d48_form"):
        st.markdown("---")
        comprende = st.checkbox("Sí, comprendo las instrucciones.", key="comprende_d48")
        st.markdown("---")
        
        respuestas_usuario = {}
        
        # --- EJEMPLO ---
        st.write("""EJEMPLO: Indique el valor de la figura que falta: En este caso, la respuesta correcta es 2/4, ya que como vemos en la imagen,
        la secuencia sigue un patrón donde el número de puntos en cada mitad de las fichas se mantiene. El 2 indica el valor que va arriba del dominó faltante,
        y el 4 el valor que va abajo. Por lo tanto, la ficha que completa la secuencia es 2/4.
                 """)
        try:
            st.image("d48_images/ejemplo2.png", width=400)
        except Exception:
            st.warning("Imagen de ejemplo 'd48_images/ejemplo2.png' no encontrada.")
            
        
        opciones_ejemplo = D48_QUESTIONS_OPTIONS.get(0, ["1/1", "2/2", "3/3", "2/4"]) # Alternativas de ejemplo
        respuesta_ejemplo = st.radio(
            "Alternativas para el ejemplo",
            opciones_ejemplo,
            key="ejemplo",
            horizontal=True,
            index=None,
            label_visibility="collapsed"
        )
        st.markdown("---")


        # --- BUCLE PARA LAS 44 PREGUNTAS (MODIFICADO) ---
        for i in range(1, 45):
            st.write(f"**{i}.- Indique el valor de la figura que falta:**")
            
            try:
                st.image(f"d48_images/pregunta_{i}.png", width=400)
            except Exception:
                st.warning(f"Imagen 'd48_images/pregunta_{i}.png' no encontrada.")

            # Obtener las opciones específicas para esta pregunta
            opciones = D48_QUESTIONS_OPTIONS.get(i, [])
            if not opciones:
                st.error(f"Error: No se encontraron alternativas para la pregunta {i}. Por favor, rellene el diccionario D48_QUESTIONS_OPTIONS.")
                continue

            respuestas_usuario[f"pregunta_{i}"] = st.radio(
                f"Alternativas para la pregunta {i}",
                opciones, # <-- Se usan las alternativas del diccionario
                key=f"q_{i}",
                horizontal=True,
                index=None,
                label_visibility="collapsed"
            )
            if i < 44:
                st.markdown("---")

        siguiente_button = st.form_submit_button("Siguiente")

        if siguiente_button:
            if 'ficha_id' not in st.session_state:
                st.error("Error crítico: No se encontró el ID de la ficha de ingreso.")
                return
                
            if 'datos_paciente' not in st.session_state or 'edad' not in st.session_state.datos_paciente:
                 st.error("Error crítico: No se encontraron los datos del paciente (edad) para calcular el percentil.")
                 return
            edad_paciente = st.session_state.datos_paciente.get('edad') or 18 

            # Verificar que todas las preguntas hayan sido respondidas
            errores = [f"Pregunta {i}" for i in range(1, 45) if respuestas_usuario.get(f"pregunta_{i}") is None]
            
            if errores:
                st.error("Por favor, responda todas las preguntas. Faltan: " + ", ".join(errores))
            else:
                with st.spinner("Calculando y guardando resultados..."):
                    
                    # --- LÓGICA DE CÁLCULO ACTUALIZADA ---
                    puntaje_total, percentil, interpretacion, respuestas_db = calcular_d48(respuestas_usuario, edad_paciente)

                    # --- Guardar datos calculados ---
                    d48_data_to_save = {
                        "id": st.session_state.ficha_id,
                        "comprende": comprende,
                        **respuestas_db, # Guardar 1 (correcta) o 0 (incorrecta)
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
                            
                            st.session_state.current_test_index += 1
                            st.rerun()
                        else:
                            st.error(f"Error al guardar los resultados: {response.error.message if response.error else 'Error desconocido'}")
                    except Exception as e:
                        st.error(f"Ocurrió una excepción al intentar guardar los resultados: {e}")

