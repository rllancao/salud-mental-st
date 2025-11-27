import streamlit as st
from supabase import Client

# --- DATOS DEL TEST BARRATT ---
INVERTED_QUESTIONS = [1, 5, 6, 7, 8, 10, 11, 13, 17, 19, 22, 30]
OPTIONS = {"Rara vez o nunca": 1, "A veces": 2, "A menudo": 3, "Casi siempre o siempre": 4}
INVERTED_OPTIONS = {"Rara vez o nunca": 4, "A veces": 3, "A menudo": 2, "Casi siempre o siempre": 1}

QUESTIONS_BY_TYPE = {
    "cognitiva": [4, 7, 10, 13, 16, 19, 24, 27],
    "motora": [2, 6, 9, 12, 15, 18, 21, 23, 26, 29], 
    "no_planeada": [1, 3, 5, 8, 11, 14, 17, 20, 22, 25, 28, 30]
}

# --- DEBES RELLENAR ESTE DICCIONARIO CON LAS 30 AFIRMACIONES ---
QUESTIONS_TEXT = {
    1: "Planifico las tareas con cuidado.", 2: "Hago las cosas sin pensarlas.",
    3: "Casi nunca me tomo las cosas a pecho (No me perturbo con facilidad).", 4: "Mis pensamientos pueden tener gran velocidad (Tengo pensamientos que van muy rápido en mi mente).",
    5: "Planifico mis viajes con antelación.", 6: "Soy una persona con autocontrol.",
    7: "Me concentro con facilidad (Se me hace fácil concentrarme).", 8: "Ahorro con regularidad.",
    9: "Se me hace difícil estar quieto/a durante largos periodos de tiempo.", 10: "Pienso las cosas cuidadosamente.",
    11: "Planifico para tener un trabajo fijo (me esfuerzo por asegurar que tendré dinero para pagar mis gastos).", 12: "Digo las cosas sin pensarlas.",
    13: "Me gusta pensar sobre problemas complicados (me gusta pensar sobre problemas complejos).", 14: "Cambio de trabajo frecuentemente (no me quedo en el mismo trabajo durante largos periodos de tiempo)",
    15: "Actúo impulsivamente.", 16: "Me aburro con facilidad tratando de resolver problemas en mi mente (me aburre pensar en algo por demasiado tiempo).",
    17: "Visito al médico y dentista con regularidad.", 18: "Hago las cosas en el momento que se me ocurren.",
    19: "Soy una persona que piensa sin distraerse (puedo enfocar mi mente en una sola cosa por mucho tiempo).", 20: "Cambio de vivienda a menudo (me mudo con frecuencia o no me gusta vivir en el mismo sitio por mucho tiempo).",
    21: "Compro cosas impulsivamente.", 22: "Termino lo que empiezo.",
    23: "Camino y me muevo con rapidez.", 24: "Resuelvo los problemas experimentando (resuelvo los problemas empleando una posible solución y viendo si funciona).",
    25: "Gasto en efectivo o a crédito más de lo que gano (gasto más de lo que gano).", 26: "Hablo rápido.",
    27: "Tengo pensamiento extraños cuando estoy pensando (a veces tengo pensamiento irrelevantes cuando pienso).", 28: "Me interesa más el presente que el futuro.",
    29: "Me siento inquieto/a en clases o charlas (me siento inquieto/a si tengo que oír a alguien hablar durante un largo periodo de tiempo).", 30: "Planifico el futuro (me interesa más el futuro que el presente)."
}

# --- Función para calcular resultados de Barratt ---
def calcular_barratt(processed_scores):
    scores = {"cognitiva": 0, "motora": 0, "no_planeada": 0}
    
    for q_num, score in processed_scores.items():
        if isinstance(q_num, int): # Solo procesar claves numéricas (preguntas)
            # Sumar al tipo correspondiente
            for tipo, preguntas in QUESTIONS_BY_TYPE.items():
                if q_num in preguntas:
                    scores[tipo] += score
                    break
                    
    score_total = sum(scores.values())

    # Calcular niveles
    def get_level(score, ranges):
        if score <= ranges[0]: return "Baja"
        if score <= ranges[1]: return "Media"
        if score <= ranges[2]: return "Alta"
        return "Muy Alta"

    level_cognitiva = get_level(scores["cognitiva"], [4, 9, 20])
    level_motora = get_level(scores["motora"], [4, 9, 20])
    level_no_planeada = get_level(scores["no_planeada"], [7, 13, 24])
    level_total = get_level(score_total, [15, 32, 76])
    
    return scores, score_total, level_cognitiva, level_motora, level_no_planeada, level_total

def crear_interfaz_barratt(supabase: Client):
    st.components.v1.html("<script>window.top.scrollTo(0, 0);</script>", height=0)
    st.title("Escala de Impulsividad de Barratt (BIS-11)")
    st.markdown("---")
    st.info(
        """
        **Instrucciones:** Las personas son diferentes en cuanto a la forma en que se comportan y sienten en diferentes situaciones. Esta es una prueba para medir algunas de las formas en que usted actúa y piensa. No se detenga demasiado en ninguna de las oraciones. Responda rápido y honestamente.

            Se encontrará con 30 situaciones.

            Para cada situación considere cómo piensa y actúa usted, de manera de saber si esta forma de actuar o pensar la realiza:

            *Rara vez o Nunca (1 punto)
            *A veces (2 puntos)
            *A menudo (3 puntos)
            *Casi siempre o Siempre (4 puntos)

            **Nota:** Algunas preguntas tienen puntaje invertido.
        """
    )

    with st.form(key="barratt_form"):
        st.markdown("---")
        comprende = st.checkbox("Sí, comprendo las instrucciones.", key="comprende_barratt")
        st.markdown("---")
        
        respuestas_usuario_texto = {} # Guardará el texto de la opción elegida

        for i in range(1, 31):
            st.write(f"**{i}.- {QUESTIONS_TEXT.get(i, f'Texto pregunta {i} no encontrado')}**")
            
            # Usar las opciones normales siempre para el radio button
            opciones_display = list(OPTIONS.keys())
            
            respuestas_usuario_texto[f"pregunta_{i}"] = st.radio(
                f"Respuesta para la pregunta {i}",
                opciones_display,
                key=f"q_{i}",
                horizontal=True,
                index=None,
                label_visibility="collapsed"
            )
            if i < 30:
                st.markdown("---")

        siguiente_button = st.form_submit_button("Siguiente")

        if siguiente_button:
            if 'ficha_id' not in st.session_state:
                st.error("Error crítico: No se encontró el ID de la ficha de ingreso.")
                return

            errores = [f"Pregunta {i}" for i in range(1, 31) if respuestas_usuario_texto.get(f"pregunta_{i}") is None]
            
            if errores:
                st.error("Por favor, responda todas las afirmaciones. Faltan: " + ", ".join(errores))
            else:
                with st.spinner("Guardando resultados..."):
                    
                    # 1. Procesar las respuestas para obtener los puntajes numéricos (1-4)
                    processed_scores = {}
                    for i in range(1, 31):
                        pregunta_key_num = i
                        pregunta_key_str = f"pregunta_{i}"
                        respuesta_texto = respuestas_usuario_texto[pregunta_key_str]
                        
                        if pregunta_key_num in INVERTED_QUESTIONS:
                            processed_scores[pregunta_key_num] = INVERTED_OPTIONS.get(respuesta_texto, 0) # Usar 0 si hay error
                        else:
                            processed_scores[pregunta_key_num] = OPTIONS.get(respuesta_texto, 0) # Usar 0 si hay error

                    # 2. Calcular los puntajes y niveles
                    scores_por_tipo, score_total, lvl_cog, lvl_mot, lvl_np, lvl_tot = calcular_barratt(processed_scores)

                    # 3. Preparar datos para Supabase
                    barratt_data_to_save = {
                        "id": st.session_state.ficha_id,
                        "comprende": comprende,
                        # Guardar los puntajes numéricos (1-4) para cada pregunta
                        **{f"pregunta_{k}": v for k, v in processed_scores.items()}, 
                        # Guardar los resultados calculados
                        "puntaje_cognitiva": scores_por_tipo["cognitiva"],
                        "nivel_cognitiva": lvl_cog,
                        "puntaje_motora": scores_por_tipo["motora"],
                        "nivel_motora": lvl_mot,
                        "puntaje_no_planeada": scores_por_tipo["no_planeada"],
                        "nivel_no_planeada": lvl_np,
                        "puntaje_total": score_total,
                        "nivel_total": lvl_tot
                    }
                    
                    # 4. Guardar datos completos en session_state para el PDF
                    # (Incluye los puntajes brutos 1-4 y los resultados calculados)
                    st.session_state.form_data['test_barratt'] = barratt_data_to_save 

                    # 5. Enviar a Supabase
                    try:
                        response = supabase.from_('test_barratt').insert(barratt_data_to_save).execute()
                        if response.data:
                            st.session_state.current_test_index += 1
                            st.rerun()
                        else:
                            st.error(f"Error al guardar: {response.error.message if response.error else 'Error desconocido'}")
                    except Exception as e:
                        st.error(f"Ocurrió una excepción al guardar: {e}")

