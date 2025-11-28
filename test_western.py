import streamlit as st
from supabase import Client
import time
import base64

# --- DEBES RELLENAR ESTOS DICCIONARIOS ---
# Diccionario con las 24 preguntas y sus 5 alternativas
WESTERN_QUESTIONS = {
    1: {"pregunta": " GUERRA, significa lo opuesto de:", 
        "opciones": ["PAZ", "LUCHA", "BATALLA", "ESTRATEGIA", "SITIO"]},
    2: {"pregunta": "El día de la Independencia cae en el mes de:", 
        "opciones": ["ENERO", "SEPTIEMBRE", "JULIO", "DICIEMBRE", "MAYO"]},
    3: {"pregunta": "Si 1 litro de gasolina = \\$30, ¿cuántos litros se pueden comprar con \\$450?", 
        "opciones": ["10", "15", "20", "25", "30"]},
    4: {"pregunta": "¿Cuál es el número que NO pertenece a la serie de abajo ?",
        "opciones": ["27","24", "21", "18","14"]},
    5: {"pregunta": "PARTE significa lo opuesto de:", 
        "opciones": ["PEDAZO", "DETALLE", "SEGMENTO", "TROZO", "TOTAL"]},
    6: {"pregunta": "¿Cuántos pares de nombres aquí abajo son iguales?", 
        "opciones": ["1", "2", "3", "4"]},
    7: {"pregunta": "Los dos refranes: \"Cuando el río suena, agua lleva\" y \"A río revuelto, ganancia de pescadores\", quieren decir:", 
        "opciones": ["LO MISMO", "LO CONTRARIO", "NI LO MISMO NI LO CONTRARIO"]},
    8: {"pregunta": "Por favor, lea la siguiente imagen y responda la pregunta:", 
        "opciones": ["1", "2", "3", "4"]},
    9: {"pregunta": "Acomoda las siguientes palabras para formar una oración: \"COMIDA Y USAMOS CON LA PAN MANTEQUILLA\" y diga si es:", 
        "opciones": ["VERDAD", "FALSA", "DUDOSA"]},
    10: {"pregunta": "¿Cuál palabra es diferente de otras?", 
         "opciones": ["INGENIERO", "PLOMERO", "MEDICO", "FISICO", "FISIOLOGO"]},
    11: {"pregunta": "ESCÉPTICO - ASÉPTICO significan:", 
         "opciones": ["LO MISMO", "LO OPUESTO", "NI LO MISMO NI LO OPUESTO"]},
    12: {"pregunta": "¿Cuál palabra es diferente de otras?", 
         "opciones": ["REVISTA", "RADIO", "PERIÓDICO", "AUTOMÓVIL", "TELEVISIÓN"]},
    13: {"pregunta": "INVIERNO es lo opuesto de:", 
         "opciones": ["ESTIO", "PRIMAVERA", "VERANO", "OTOÑO", "FRÍO"]},
    14: {"pregunta": "Si de las siguientes afirmaciones: \"1.- La mayoría de las perras son inteligentes\", \"2.- Esta es una perra\" y \"3.- Esta perra es inteligente\" las primeras dos son ciertas, ¿qué es la última afirmación?", 
         "opciones": ["FALSA", "DUDOSA", "VERDADERA"]},
    15: {"pregunta": "GASTO - AHORRO significan:", 
         "opciones": ["LO MISMO", "LO CONTRARIO", "NI LO MISMO NI LO CONTRARIO"]},
    16: {"pregunta": "Un avión vuela 450 kilómetros en 50 minutos. A esa velocidad, ¿ cuántos kilómetros volaría en una hora?", 
         "opciones": ["500", "540", "580", "580", "600"]},
    17: {"pregunta": "ACEPTAR - RECHAZAR significan:", 
         "opciones": ["LO MISMO", "LO CONTRARIO", "NI LO MISMO NI LO CONTRARIO"]},
    18: {"pregunta": "Un tirador da en el blanco el 90% de las veces ¿cuántos tiros tendrá que hacer para dar en el blanco 27 veces?", 
         "opciones": ["15", "20", "25", "30"]},
    19: {"pregunta": "Los dos siguientes refranes: \"No por mucho madrugar amanece más temprano\" y \"Al que madruga dios le ayuda\", quieren decir:", 
         "opciones": ["LO MISMO", "LO OPUESTO", "NI LO MISMO NI LO OPUESTO"]},
    20: {"pregunta": "En la siguiente secuencia: 256 - 64 - 4 - 1 ¿Cuál es el número que sigue?", 
         "opciones": ["1/3", "1/4", "1/8", "1/2"]},
    21: {"pregunta": "El mes que tiene menos días es:", 
         "opciones": ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO"]},
    22: {"pregunta": "En la siguiente secuencia: 130 - 122 - 113 - ... - 92 - 80 ¿Cuál es el número que debe ir en el lugar de los puntos?", 
         "opciones": ["120", "118", "110", "103"]},
    23: {"pregunta": "Un negociante compró unas máquinas por \\$16.000 pesos. Las vendió en \\$19.000 pesos obteniendo una ganancia de \\$150 pesos en cada maquina vendida. ¿Cuántas máquinas compró?", 
         "opciones": ["10", "15", "20", "25"]},
    24: {"pregunta": "Un reloj se retrasa 2 minutos y 10 segundos en 2 horas. ¿Cuántos segundos se atrasará en 3 horas?", 
         "opciones": ["190", "180", "185", "170", "195"]},
}

# Diccionario con las respuestas correctas para cada pregunta
WESTERN_CORRECT_ANSWERS = {
    1: "PAZ",
    2: "SEPTIEMBRE",
    3: "15",
    4: "14",
    5: "TOTAL",
    6: "2",
    7: "NI LO MISMO NI LO CONTRARIO",
    8: "4",
    9: "DUDOSA",
    10: "PLOMERO",
    11: "NI LO MISMO NI LO OPUESTO",
    12: "AUTOMÓVIL",
    13: "VERANO",
    14: "DUDOSA",
    15: "LO CONTRARIO",
    16: "540",
    17: "LO CONTRARIO",
    18: "30",
    19: "LO OPUESTO",
    20: "1/4",
    21: "FEBRERO",
    22: "103",
    23: "20",
    24: "195",
}

# Diccionario de interpretación
INTERPRETACION_MAP = {
    (0, 2): "DEFICIENTE",
    (3, 5): "NORMAL LENTO",
    (6, 14): "NORMAL PROMEDIO",
    (15, 24): "NORMAL SUPERIOR",
}

def get_interpretation(score):
    for (min_score, max_score), interpretation in INTERPRETACION_MAP.items():
        if min_score <= score <= max_score:
            return interpretation
    return "DEFICIENTE" # Default por si acaso

def get_image_as_base64(path):
    """Encodes an image file to a base64 string for embedding in HTML."""
    try:
        with open(path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
    except FileNotFoundError:
        st.warning(f"Advertencia: No se encontró el archivo del temporizador '{path}'.")
        return None

def crear_interfaz_western(supabase: Client):
    # --- CONTROL DE ESTADO Y SCROLL ---
    
    # Inicializar estado si no existe
    if 'western_started' not in st.session_state:
        st.session_state.western_started = False
        
    # --- SCROLL TO TOP ROBUSTO ---
    # Inyectamos el estado 'western_started' en el script para que cambie cuando
    # el usuario presiona "Empezar Test", forzando la re-ejecución del scroll.
    st.components.v1.html(
        f"""
        <script>
            // Status: {st.session_state.western_started} (Fuerza actualización al cambiar estado)
            
            // Intentar hacer scroll al elemento con ID 'inicio_pagina' (definido en maestro.py)
            var topElement = window.parent.document.getElementById('inicio_pagina');
            if (topElement) {{
                topElement.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
            }} else {{
                // Fallback: scroll al top del contenedor principal si no encuentra el ID
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

    st.title("Test de Aptitudes Mentales (Western)")
    st.markdown("---")

    # --- Estado 1: Instrucciones ---
    if not st.session_state.western_started:
        st.info(
            """
            **LO QUE USTED VA A HACER:** Esta prueba toma muy poco tiempo, pero usted debe leerla
            atentamente y contestar lo mejor que pueda. \n
            **NO PRESIONE EL BOTÓN DE "EMPEZAR" HASTA QUE SE LE ORDENE.**\n
            USTED VA A CONTESTAR ALGUNAS PREGUNTAS Y A RESOLVER UNOS
            PROBLEMAS. Aquí tiene algunos ejemplos para que los conteste:
            """
        )
        st.markdown(
            """
            **Ejemplos:**\n
            **Nº 1:** \n
            TRISTEZA es lo opuesto de...............................\n
            1- ADORMECIMIENTO 2- MISERIA 3- ENFERMEDAD 4- PERMISIVO 5- ALEGRIA\n
            *(La respuesta correcta es ALEGRIA)*
            
            **Nº 2:**\n
            ¿Cuál es el número que falta abajo?\n
            66 62 58 ....... 50 46\n
            *(La respuesta correcta es 54)*

            **Nº 3:**\n
            IRSE – PARTIR, quiere decir...............................\n
            1- LO MISMO 2- LO CONTRARIO 3- NI LO MISMO NI LO CONTRARIO\n
            *(La respuesta correcta es LO MISMO)*
            """
        )
        st.warning(
            """
            HAY 24 PREGUNTAS O PROBLEMAS, USTED TIENE **SOLO 5 MINUTOS** PARA
            CONTESTAR. HÁGALO LO MEJOR QUE PUEDA, TRABAJE RÁPIDO. \n
            CUANDO EL EXAMINADOR LO INDIQUE, PRESIONE "EMPEZAR" Y CONTESTE LAS
            PREGUNTAS.
            """
        )
        
        st.markdown("---")
        comprende = st.checkbox("Sí, comprendo las instrucciones.", key="comprende_western")
        st.markdown("---")

        if st.button("Empezar Test", type="primary"):
            st.session_state.western_started = True
            st.session_state.western_comprende = comprende
            st.session_state.western_start_time = time.time()
            st.session_state.western_submitted = False
            st.rerun()

    # --- Estado 2: El Test ---
    else:
        if 'western_start_time' not in st.session_state:
            st.session_state.western_start_time = time.time()
        if 'western_submitted' not in st.session_state:
            st.session_state.western_submitted = False

        elapsed_time = time.time() - st.session_state.western_start_time
        remaining_time = 300 - elapsed_time # 5 minutos = 300 segundos
        is_time_up = remaining_time <= 0

        # --- Temporizador GIF ---
        if not st.session_state.get('western_submitted', False):
            gif_base64 = get_image_as_base64("western_images/5-minute.gif")
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
                    }}
                </style>
                <div class="fixed-gif-timer">
                    <h5 style='margin-bottom: 5px; color: #555;'>Tiempo Restante</h5>
                    <img src="data:image/gif;base64,{gif_base64}" width="100%">
                </div>
                """
                st.markdown(timer_html, unsafe_allow_html=True)
        
        respuestas_usuario = {}

        # --- Bucle de Preguntas ---
        with st.form(key="western_questions_form"):
            for i in range(1, 25): 
                question_data = WESTERN_QUESTIONS.get(i)
                if not question_data:
                    st.warning(f"Datos para la pregunta {i} no encontrados.")
                    continue

                st.write(f"**{i}.- {question_data['pregunta']}**")

                # --- MEJORA: Añadir imagen para preguntas 6 y 8 ---
                if i == 6:
                    try:
                        st.image("western_images/pregunta_6.png", width=400)
                    except Exception:
                        st.warning("Imagen 'western_images/pregunta_6.png' no encontrada.")
                elif i == 8:
                    try:
                        st.image("western_images/pregunta_8.png", width=600)
                    except Exception:
                        st.warning("Imagen 'western_images/pregunta_8.png' no encontrada.")

                respuestas_usuario[f"pregunta_{i}"] = st.radio(
                    f"Alternativas para la pregunta {i}",
                    question_data['opciones'],
                    key=f"q_{i}",
                    horizontal=True, 
                    index=None,
                    label_visibility="collapsed"
                )
                if i < 24: 
                     st.markdown("---")
            
            siguiente_button = st.form_submit_button("Finalizar y Guardar")

        if siguiente_button or is_time_up:
            if not st.session_state.western_submitted:
                st.session_state.western_submitted = True
                
                if 'ficha_id' not in st.session_state:
                    st.error("Error crítico: No se encontró el ID de la ficha de ingreso.")
                    return

                if is_time_up:
                    st.warning("El tiempo se ha acabado. Se enviarán las respuestas.")
                
                with st.spinner("Calculando y guardando resultados..."):
                    
                    # 1. Calcular puntaje
                    puntaje_total = 0
                    respuestas_correctas_db = {}
                    for i in range(1, 25):
                        pregunta_key = f"pregunta_{i}"
                        respuesta_dada = respuestas_usuario.get(pregunta_key)
                        respuesta_correcta = WESTERN_CORRECT_ANSWERS.get(i)
                        
                        if respuesta_dada == respuesta_correcta:
                            respuestas_correctas_db[pregunta_key] = 1
                            puntaje_total += 1
                        else:
                            respuestas_correctas_db[pregunta_key] = 0 # Guardar 0 para incorrecta

                    # 2. Obtener interpretación
                    interpretacion = get_interpretation(puntaje_total)

                    # 3. Preparar datos para Supabase
                    western_data_to_save = {
                        "id": st.session_state.ficha_id,
                        "comprende": st.session_state.get("western_comprende", False),
                        **respuestas_correctas_db, # Guardar 1 o 0
                        "puntaje": puntaje_total,
                        "interpretacion": interpretacion
                    }
                    
                    try:
                        # 4. Enviar a Supabase
                        response = supabase.from_('test_western').insert(western_data_to_save).execute()
                        if response.data:
                            # 5. Guardar datos para el PDF en session_state
                            if 'form_data' not in st.session_state:
                                st.session_state.form_data = {}
                            st.session_state.form_data['test_western'] = {
                                "puntaje": puntaje_total,
                                "interpretacion": interpretacion
                            }
                            
                            # Limpiar estado del test
                            for key in ['western_started', 'western_comprende', 'western_start_time', 'western_submitted']:
                                if key in st.session_state:
                                    del st.session_state[key]
                            
                            st.session_state.current_test_index += 1
                            st.rerun()
                        else:
                            st.error(f"Error al guardar los resultados: {response.error.message if response.error else 'Error desconocido'}")
                    except Exception as e:
                        st.error(f"Ocurrió una excepción al intentar guardar los resultados: {e}")

        elif not st.session_state.western_submitted:
            time.sleep(1) # Actualizar cada segundo para el timer
            st.rerun()