import streamlit as st
from supabase import Client

# --- LISTA COMPLETA DE PREGUNTAS EPQ-R ---
PREGUNTAS_EPQ_R = [
    # Pregunta 1 (ya existente)
    "¿Se detiene a pensar las cosas antes de hacerlas?",
    # Preguntas 2 a 83 de tu lista
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


def crear_interfaz_epq_r(supabase: Client):
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
        
        respuestas = {}
        
        # --- BUCLE CON PREGUNTAS REALES ---
        for i, pregunta_texto in enumerate(PREGUNTAS_EPQ_R):
            num_pregunta = i + 1
            st.write(f"**{num_pregunta}.- {pregunta_texto}**")
            # El valor ("Sí" o "No") se almacena en el diccionario 'respuestas'
            respuestas[f"pregunta_{num_pregunta}"] = st.radio(
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

            # Verificar que todas las preguntas hayan sido respondidas
            errores = [f"Pregunta {i+1}" for i, _ in enumerate(PREGUNTAS_EPQ_R) if respuestas.get(f"pregunta_{i+1}") is None]
            
            if errores:
                st.error("Por favor, responda todas las preguntas. Faltan las siguientes: " + ", ".join(errores))
            else:
                with st.spinner("Guardando resultados..."):
                    
                    # --- NUEVA LÓGICA: Transformar respuestas para la base de datos ---
                    processed_respuestas = {}
                    for key, answer in respuestas.items():
                        num_pregunta = int(key.split('_')[1])
                        if answer == "Sí":
                            # Si la respuesta es "Sí", se busca la letra correspondiente
                            letra = PERSONALITY_MAP.get(num_pregunta)
                            processed_respuestas[key] = letra
                        else:
                            # Si la respuesta es "No", se envía un valor nulo
                            processed_respuestas[key] = None

                    # Datos a guardar en la base de datos (con letras o nulos)
                    epq_r_data_to_save = {
                        "id": st.session_state.ficha_id,
                        "comprende": comprende,
                        **processed_respuestas
                    }
                    
                    try:
                        response = supabase.from_('test_epq_r').insert(epq_r_data_to_save).execute()
                        if response.data:
                            # Guardar las respuestas originales ("Sí"/"No") para la generación del PDF
                            if 'form_data' not in st.session_state:
                                st.session_state.form_data = {}
                            st.session_state.form_data['test_epq_r'] = {
                                "comprende": comprende,
                                **respuestas
                            }
                            st.session_state.current_test_index += 1
                            st.rerun()
                        else:
                            st.error(f"Error al guardar los resultados: {response.error.message if response.error else 'Error desconocido'}")
                    except Exception as e:
                        st.error(f"Ocurrió una excepción al intentar guardar los resultados: {e}")

