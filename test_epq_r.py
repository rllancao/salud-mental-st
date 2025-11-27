import streamlit as st
from supabase import Client

# --- LISTA COMPLETA DE PREGUNTAS EPQ-R ---
PREGUNTAS_EPQ_R = [
    "¿Se detiene a pensar las cosas antes de hacerlas?",
    "¿Su estado de animo sufre altibajos con frecuencia?",
    "¿Es una persona conversadora?",
    "¿Se siente a veces desdichado sin motivo?",
    "¿Algunas veces ha querido llevarse más de lo que le corresponde en su reparto?",
    "¿Es usted una persona bien animada o vital?",
    "Si usted asegura que hará un cosa, ¿siempre mantiene su promesa, sin importarle las molestias que ello le puede ocasionar?",
    "¿Es una persona irritable?",
    "¿Le tiene sin cuidado lo que piensa los demás?",
    "¿Alguna vez a culpado a alguien por algo que había hecho usted?",
    "¿Son todos tus hábitos buenos y deseables?",
    "¿Tiende a mantenerse apartado(a) en las situaciones sociales?",
    "¿A menudo se siente harto(a)?",
    "¿Ha cogido alguna vez alguna cosa (aunque no fuese más que un alfiler o botón) que perteneciese a otra persona?",
    "¿Para usted los limites de lo que está bien y lo que esta mal son menos claros que para la mayoria de la gente?",
    "¿Le gusta salir a menudo?",
    "¿Es mejor actuar como uno quiera que seguir las normas sociales?",
    "¿Tiene a menudo sentimientos de culpabilidad?",
    "¿Diría de si mismo que es una persona nerviosa?",
    "¿Es usted una persona sufridora?",
    "¿Alguna vez ha roto o perdido algo que le perteneciese a otra persona?",
    "¿Generalmente tomo la iniciativa al hacer nuevas amistades?",
    "¿Los deseos personales están por encima de las normas sociales?",
    "¿Diría de si mismo que es una persona tensa o muy nerviosa?",
    "Por lo general ¿suele estar callado(a) cuando esta con otras personas?",
    "¿Cree que el matrimonio está anticuado o debería abolirse?",
    "¿Puede animar facilmente una fiesta aburrida?",
    "¿Le gusta contar chistes o historias divertidas a sus amigos?",
    "¿La mayoría de las cosas le son indiferentes?",
    "De niño, ¿fue alguna vez descarado con sus padres?",
    "¿Le gusta mezclarse con la gente?",
    "¿Se siente a menudo ápatico/a y cansado/a sin motivo?",
    "¿Ha hecho alguna vez trampa en el juego?",
    "¿A menudo toma decisiones sin pararse a reflexionar?",
    "¿A menudo siente que la vida es muy monótoma?",
    "¿Alguna vez se ha aprovechado de alguien?",
    "¿Cree que la gente pierde el tiempo al proteger su futuro con ahorros y seguros?",
    "¿Evadiria impuestos si tuviera seguro de que nunca sería descubierto?",
    "¿Puede organizar y conducir una fiesta?",
    "Generalmente, ¿reflexiona antes de actuar?",
    "¿Sufre de los nervios?",
    "¿A menudo se siente solo?",
    "¿Hace siempre lo que predice?",
    "¿Es mejor las normas de la sociedad que ir a su aire?",
    "¿Alguna vez ha llegado tarde a una cita o trabajo?",
    "¿Le gusta el bullicio y la agitación a su alrededor?",
    "¿La gente piensa que usted es una persona animada?",
    "¿Cree que los planes de seguros son una buena idea?",
    "¿Realiza muchas actividades a tiempo libre?",
    "¿Daría dinero para fines caritativos?",
    "¿Le afectaría mucho ver sufrir a un niño o animal?",
    "¿Se preocupa a menudo por cosas que no deberia haber hecho o dicho?",
    "¿Habitualmente es capaz de liberarse y disfrutar en una fiesta animada?",
    "¿Se siente facilmente herido en sus sentimientos?",
    "¿Disfruta hiriendo a las personas que ama?",
    "¿Habla a veces de cosas de la que no sabe nada?",
    "¿Preferiria leer a conocer gente?",
    "¿Tiene muchos amigos?",
    "¿Se ha enfrentado constantemente a sus padres?",
    "Cuándo era niño, ¿hacia enseguida las cosas que le pedian y sin refunfuñar?",
    "¿Se ha opuesto frecuentemente a los deseos de sus padres?",
    "¿Se inquieta por las cosas terribles que podrian suceder?",
    "¿Es más indulgente que la mayoria de las personas acerca del bien y del mal?",
    "¿Se siente intranquilo por su salud?",
    "¿Alguna vez ha dicho algo malo o desagradable acerca de otra persona?",
    "¿Le gusta cooperar con los demás?",
    "¿Se preocupa si sabe que hay errores en su trabajo?",
    "¿Se lava siempre las manos antes de comer?",
    "¿Casi siempre tiene una respuesta \"a punto\" cuando le hablan?",
    "¿Le gusta hacer cosas en la que tiene que actuar rápidamente?",
    "¿Es (o era) su madre una buena mujer?",
    "¿Le preocupa mucho su aspecto?",
    "¿Alguna vez ha deseado morir?",
    "¿Trata de no ser grosero con la gente?",
    "Después de un experiencia embarazosa, ¿se siente preocupado durante mucho tiempo?",
    "¿Se siente fácilmente herido cuando la gente encuentra defectos en usted o en su trabajo?",
    "¿Frecuentemente improvisa decisiones en función de la situación?",
    "¿Se siente a veces desbordante de energia y otras muy decaído?",
    "¿A veces deja para mañana lo que debería hacer hoy?",
    "¿La gente le cuenta muchas mentiras?",
    "¿Se afecta fácilmente por según qué cosas?",
    "Cuando ha cometido una equivocación, ¿está siempre dispuesto a admitirlo?",
    "Cuando tiene mal humor, ¿le cuesta controlarse?",
]


# --- MAPA DE PERSONALIDADES POR PREGUNTA ---
PERSONALITY_MAP = {
    # Dureza (D)
    1: 'D', 9: 'D', 15: 'D', 17: 'D', 23: 'D', 26: 'D', 29: 'D', 34: 'D', 37: 'D', 40: 'D', 44: 'D', 48: 'D', 50: 'D', 51: 'D', 55: 'D', 59: 'D', 61: 'D', 63: 'D', 66: 'D', 67: 'D', 71: 'D', 74: 'D', 80: 'D',
    # Emotividad (M)
    2: 'M', 4: 'M', 8: 'M', 13: 'M', 18: 'M', 19: 'M', 20: 'M', 24: 'M', 32: 'M', 35: 'M', 41: 'M', 42: 'M', 52: 'M', 54: 'M', 62: 'M', 64: 'M', 72: 'M', 73: 'M', 75: 'M', 76: 'M', 78: 'M', 81: 'M', 83: 'M',
    # Extraversión (E)
    3: 'E', 6: 'E', 12: 'E', 16: 'E', 22: 'E', 25: 'E', 27: 'E', 28: 'E', 31: 'E', 39: 'E', 46: 'E', 47: 'E', 49: 'E', 53: 'E', 57: 'E', 58: 'E', 69: 'E', 70: 'E', 77: 'E',
    # Sinceridad (S)
    5: 'S', 7: 'S', 10: 'S', 11: 'S', 14: 'S', 21: 'S', 30: 'S', 33: 'S', 36: 'S', 38: 'S', 43: 'S', 45: 'S', 56: 'S', 60: 'S', 65: 'S', 68: 'S', 79: 'S', 82: 'S'
}

PUNTAJE_T_VARONES = {
    'E': {0:1, 1:1, 2:1, 3:2, 4:4, 5:5, 6:10, 7:10, 8:15, 9:20, 10:25, 11:30, 12:40, 13:45, 14:55, 15:65, 16:75, 17:85, 18:90, 19:98, 20:98, 21:98, 22:98, 23:98},
    'M': {0:1, 1:3, 2:4, 3:5, 4:10, 5:15, 6:20, 7:20, 8:25, 9:30, 10:35, 11:45, 12:50, 13:55, 14:65, 15:70, 16:75, 17:80, 18:85, 19:90, 20:95, 21:97, 22:99, 23:99},
    'D': {0:2, 1:5, 2:10, 3:20, 4:30, 5:40, 6:55, 7:65, 8:75, 9:80, 10:85, 11:90, 12:95, 13:95, 14:97, 15:99, 16:99, 17:99, 18:99, 19:99, 20:99, 21:99, 22:99, 23:99},
    'S': {0:1, 1:2, 2:4, 3:10, 4:15, 5:20, 6:30, 7:40, 8:50, 9:65, 10:70, 11:80, 12:85, 13:90, 14:90, 15:95, 16:97, 17:99, 18:99, 19:99}
}

PUNTAJE_T_MUJERES = {
    'E': {0:1, 1:1, 2:1, 3:2, 4:4, 5:5, 6:5, 7:10, 8:15, 9:20, 10:25, 11:30, 12:40, 13:50, 14:60, 15:70, 16:80, 17:90, 18:95, 19:99, 20:99, 21:99},
    'M': {0:1, 1:1, 2:2, 3:3, 4:4, 5:5, 6:10, 7:10, 8:15, 9:15, 10:20, 11:25, 12:35, 13:40, 14:45, 15:50, 16:55, 17:65, 18:70, 19:80, 20:85, 21:90, 22:96, 23:99},
    'D': {0:3, 1:10, 2:15, 3:25, 4:40, 5:50, 6:60, 7:75, 8:80, 9:85, 10:90, 11:95, 12:97, 13:98, 14:99, 15:99, 16:99, 17:99, 18:99},
    'S': {0:1, 1:1, 2:3, 3:5, 4:10, 5:15, 6:25, 7:35, 8:45, 9:55, 10:65, 11:70, 12:80, 13:85, 14:90, 15:95, 16:97, 17:99, 18:99}
}

# --- Función para calcular niveles EPQ-R ---
def calcular_epq_r_niveles(respuestas_usuario, sexo_paciente):
    tabla_puntaje = PUNTAJE_T_VARONES if sexo_paciente == 'MASCULINO' else PUNTAJE_T_MUJERES
    conteos = {'E': 0, 'M': 0, 'D': 0, 'S': 0}
    
    for i in range(1, 84):
        num_pregunta = i
        respuesta = respuestas_usuario.get(f"pregunta_{num_pregunta}")
        if respuesta == "Sí":
            letra = PERSONALITY_MAP.get(num_pregunta)
            if letra in conteos:
                conteos[letra] += 1

    puntajes_t = {
        'E': tabla_puntaje['E'].get(conteos['E'], 0),
        'M': tabla_puntaje['M'].get(conteos['M'], 0),
        'D': tabla_puntaje['D'].get(conteos['D'], 0),
        'S': tabla_puntaje['S'].get(conteos['S'], 0)
    }

    niveles = {}
    for letra, nombre in [('S', 'sinceridad'), ('E', 'extraversion'), ('M', 'emotividad'), ('D', 'dureza')]:
        pt = puntajes_t[letra]
        nivel = "Muy Alto"
        if pt <= 35: nivel = "Muy Poca"
        elif 36 <= pt <= 45: nivel = "Poca"
        elif 46 <= pt <= 55: nivel = "Moderado"
        elif 56 <= pt <= 65: nivel = "Bastante"
        niveles[f"nivel_{nombre}"] = nivel
        
    return niveles, conteos # Devuelve niveles y conteos para el PDF


def crear_interfaz_epq_r(supabase: Client, sexo_paciente: str):
    st.components.v1.html("<script>window.top.scrollTo(0, 0);</script>", height=0)
    st.title("Test de Personalidad EPQ-R")
    st.markdown("---")
    st.info(
        """
        **Instrucciones:** A continuación encontrará una serie de preguntas sobre su modo de actuar, de sentir y de pensar. 
        Para cada pregunta, marque la respuesta "Sí" o "No". No hay respuestas buenas o malas, sea lo más sincero posible.
        """
    )

    with st.form(key="epq_r_form"):
        st.markdown("---")
        comprende = st.checkbox("Sí, comprendo las instrucciones.", key="comprende_epq_r")
        st.markdown("---")
        
        respuestas_usuario_raw = {} # Guardará "Sí" o "No"
        
        # --- BUCLE CON PREGUNTAS REALES ---
        for i, pregunta_texto in enumerate(PREGUNTAS_EPQ_R):
            num_pregunta = i + 1
            st.write(f"**{num_pregunta}.- {pregunta_texto}**")
            respuestas_usuario_raw[f"pregunta_{num_pregunta}"] = st.radio(
                f"Respuesta {num_pregunta}", 
                ["Sí", "No"], 
                key=f"q_{num_pregunta}", 
                horizontal=True, 
                index=None, 
                label_visibility="collapsed"
            )
            if num_pregunta < len(PREGUNTAS_EPQ_R):
                st.markdown("---")

        siguiente_button = st.form_submit_button("Siguiente")

        if siguiente_button:
            if 'ficha_id' not in st.session_state:
                st.error("Error crítico: No se encontró el ID de la ficha de ingreso. Por favor, vuelva a empezar.")
                return

            errores = [f"Pregunta {i+1}" for i, _ in enumerate(PREGUNTAS_EPQ_R) if respuestas_usuario_raw.get(f"pregunta_{i+1}") is None]
            
            if errores:
                st.error("Por favor, responda todas las preguntas. Faltan las siguientes: " + ", ".join(errores))
            else:
                with st.spinner("Guardando resultados..."):
                    
                    # 1. Calcular niveles y conteos
                    if not sexo_paciente:
                         st.error("Error: No se pudo determinar el sexo del paciente para calcular los resultados.")
                         return 
                    niveles_calculados, conteos_calculados = calcular_epq_r_niveles(respuestas_usuario_raw, sexo_paciente)

                    # 2. Transformar respuestas para la base de datos (letra/None)
                    processed_respuestas_db = {}
                    for key, answer in respuestas_usuario_raw.items():
                        num_pregunta = int(key.split('_')[1])
                        if answer == "Sí":
                            letra = PERSONALITY_MAP.get(num_pregunta)
                            processed_respuestas_db[key] = letra
                        else:
                            processed_respuestas_db[key] = None

                    # 3. Preparar datos para Supabase (incluyendo niveles)
                    epq_r_data_to_save = {
                        "id": st.session_state.ficha_id,
                        "comprende": comprende,
                        **processed_respuestas_db, 
                        **niveles_calculados 
                    }
                    
                    try:
                        # 4. Enviar a Supabase
                        response = supabase.from_('test_epq_r').insert(epq_r_data_to_save).execute()
                        if response.data:
                            # 5. Guardar datos para el PDF en session_state
                            if 'form_data' not in st.session_state:
                                st.session_state.form_data = {}
                            st.session_state.form_data['test_epq_r'] = {
                                "comprende": comprende,
                                **respuestas_usuario_raw, # Guardar Sí/No original
                                **niveles_calculados, 
                                "conteos": conteos_calculados 
                            }
                            st.session_state.current_test_index += 1
                            st.rerun()
                        else:
                            st.error(f"Error al guardar los resultados: {response.error.message if response.error else 'Error desconocido'}")
                    except Exception as e:
                        st.error(f"Ocurrió una excepción al intentar guardar los resultados: {e}")

