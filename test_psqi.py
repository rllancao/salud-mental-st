import streamlit as st
from supabase import Client
import json
import math

# --- DATOS DEL TEST PSQI ---

QUESTIONS_TEXT = {
    1: "Durante el último mes, ¿Cuál ha sido, normalmente, su hora de acostarse? (Formato 24h)",
    2: "¿Cuánto tiempo habrá tardado en dormirse, normalmente, las noches del último mes?",
    3: "Durante el último mes, ¿A qué hora se ha levantado habitualmente por la mañana? (Formato 24h)",
    4: "¿Cuántas horas calcula que habrá dormido verdaderamente cada noche durante el último mes?",
    5: "Durante el último mes, cuántas veces ha tenido usted problemas para dormir a causa de: No poder conciliar el sueño en la primera media hora:",
    6: "Durante el último mes, cuántas veces ha tenido usted problemas para dormir a causa de:  Despertarse durante la noche o de madrugada:",
    7: "Durante el último mes, cuántas veces ha tenido usted problemas para dormir a causa de: Tener que levantarse para ir al servicio higiénico.",
    8: "Durante el último mes, cuántas veces ha tenido usted problemas para dormir a causa de: No poder respirar bien.",
    9: "Durante el último mes, cuántas veces ha tenido usted problemas para dormir a causa de: Toser o roncar ruidosamente:",
    10: "Durante el último mes, cuántas veces ha tenido usted problemas para dormir a causa de: Sentir frío:",
    11: "Durante el último mes, cuántas veces ha tenido usted problemas para dormir a causa de: Sentir demasiado calor:",
    12: "Durante el último mes, cuántas veces ha tenido usted problemas para dormir a causa de:  Tener pesadillas o malos sueños.",
    13: "Durante el último mes, cuántas veces ha tenido usted problemas para dormir a causa de: Sufrir dolores.",
    14: "Otras Razones (Especifique):",
    15: "Describe la razón de la pregunta 14 (Opcional):", # Campo de texto
    16: "Durante el último mes, ¿Cómo valoraría en conjunto, la calidad de su sueño?",
    17: "Durante el último mes, ¿Cuántas veces habrá tomado medicinas (por su cuenta o recetadas por el médico) para dormir?",
    18: "Durante el último mes, ¿cuántas veces ha sentido somnolencia mientras conducía, comía o desarrollaba alguna otra actividad?",
    19: "Durante el último mes, ¿Ha representado para usted muchos problemas el tener energía para realizar alguna de las actividades detalladas en la pregunta anterior?",
}

FREQ_OPTIONS = [
    "Ninguna vez en el último mes", # 0
    "Menos de una vez a la semana", # 1
    "Una o dos veces a la semana",   # 2
    "Tres o más veces a la semana"  # 3
]
Q16_OPTIONS = ["Bastante buena", "Buena", "Mala", "Bastante mala"] # 0, 1, 2, 3
Q19_OPTIONS = ["Ningún problema", "Sólo un leve problema", "Un problema", "Un grave problema"] # 0, 1, 2, 3

SELECTOR_OPTIONS = {
    1: list(range(0, 25)), # Horas 00 a 24
    2: ["< 15 minutos", "16-30 minutos", "31-60 minutos", "> 60 minutos"], # 0, 1, 2, 3
    3: list(range(0, 25)), # Horas 00 a 24
    4: list(range(1, 16)), # Horas de sueño 1 a 15
}

# --- MAPEO DE PUNTUACIONES ---
FREQ_SCORE_MAP = {FREQ_OPTIONS[i]: i for i in range(len(FREQ_OPTIONS))}
Q16_SCORE_MAP = {Q16_OPTIONS[i]: i for i in range(len(Q16_OPTIONS))}
Q19_SCORE_MAP = {Q19_OPTIONS[i]: i for i in range(len(Q19_OPTIONS))}
Q2_SCORE_MAP = {SELECTOR_OPTIONS[2][i]: i for i in range(len(SELECTOR_OPTIONS[2]))}
Q4_SCORE_MAP = {1:3, 2:3, 3:3, 4:3, 5:2, 6:1, 7:1, 8:0, 9:0, 10:0, 11:0, 12:0, 13:0, 14:0, 15:0}
LATENCIA_FINAL_MAP = {0:0, 1:1, 2:1, 3:2, 4:2, 5:3, 6:3}
PERTURBACIONES_FINAL_MAP = {i: 1 for i in range(1, 10)}
PERTURBACIONES_FINAL_MAP.update({i: 2 for i in range(10, 19)})
PERTURBACIONES_FINAL_MAP.update({i: 3 for i in range(19, 33)}) # Asumimos hasta 3*11=33
PERTURBACIONES_FINAL_MAP[0] = 0
DIFUSION_FINAL_MAP = {0:0, 1:1, 2:1, 3:2, 4:2, 5:3, 6:3}
INTERPRETACION_FINAL_MAP = {i: "Sin problemas de sueño" for i in range(5)}
INTERPRETACION_FINAL_MAP.update({i: "Merece Atención médica" for i in range(5, 8)})
INTERPRETACION_FINAL_MAP.update({i: "Merece Atención médica y tratamiento medico" for i in range(8, 15)})
INTERPRETACION_FINAL_MAP.update({i: "Problema grave de sueño" for i in range(15, 22)})

# --- NUEVA FUNCIÓN DE CÁLCULO ---
def calcular_psqi(respuestas):
    puntuaciones = {}

    # 1. Calidad subjetiva del sueño (Pregunta 16)
    p_comp1 = Q16_SCORE_MAP.get(respuestas.get("pregunta_16"), 0)
    puntuaciones["Calidad subjetiva del sueño"] = p_comp1

    # 2. Latencia del sueño (Pregunta 2 y 5)
    p_comp2_q2 = Q2_SCORE_MAP.get(respuestas.get("pregunta_2"), 0)
    p_comp2_q5 = FREQ_SCORE_MAP.get(respuestas.get("pregunta_5"), 0)
    suma_comp2 = p_comp2_q2 + p_comp2_q5
    p_comp2 = LATENCIA_FINAL_MAP.get(suma_comp2, 3) # Asumir 3 si la suma es > 6
    puntuaciones["Latencia del sueño"] = p_comp2

    # 3. Duración del sueño (Pregunta 4)
    horas_dormidas_raw = respuestas.get("pregunta_4", 0)
    p_comp3 = Q4_SCORE_MAP.get(int(horas_dormidas_raw), 0)
    puntuaciones["Duración del sueño"] = p_comp3

    # 4. Eficiencia de sueño habitual (Pregunta 1, 3, 4)
    try:
        hora_acostarse = int(respuestas.get("pregunta_1", 0))
        hora_levantarse = int(respuestas.get("pregunta_3", 0))
        horas_dormidas = int(respuestas.get("pregunta_4", 0))

        if hora_levantarse < hora_acostarse:
            horas_en_cama = (24 - hora_acostarse) + hora_levantarse
        else:
            horas_en_cama = hora_levantarse - hora_acostarse
        
        if horas_en_cama == 0:
            eficiencia_pct = 0
        else:
            eficiencia_pct = (horas_dormidas / horas_en_cama) * 100
        
        eficiencia_pct = math.ceil(eficiencia_pct) # Redondear hacia arriba

        p_comp4 = 0
        if eficiencia_pct < 65: p_comp4 = 3
        elif 65 <= eficiencia_pct <= 74: p_comp4 = 2
        elif 75 <= eficiencia_pct <= 84: p_comp4 = 1
        elif eficiencia_pct >= 85: p_comp4 = 0
        
        puntuaciones["Eficiencia de sueño habitual"] = p_comp4
    except Exception:
        puntuaciones["Eficiencia de sueño habitual"] = 0 # Default en caso de error

    # 5. Perturbaciones del sueño (Pregunta 6-14)
    suma_comp5 = 0
    for i in range(6, 15):
        suma_comp5 += FREQ_SCORE_MAP.get(respuestas.get(f"pregunta_{i}"), 0)
    p_comp5 = PERTURBACIONES_FINAL_MAP.get(suma_comp5, 3) # Asumir 3 si es > 32
    puntuaciones["Perturbaciones del sueño"] = p_comp5

    # 6. Uso de medicación hipnótica (Pregunta 17)
    p_comp6 = FREQ_SCORE_MAP.get(respuestas.get("pregunta_17"), 0)
    puntuaciones["Uso de medicación hipnótica"] = p_comp6

    # 7. Difusión diurna (Pregunta 18 y 19)
    p_comp7_q18 = FREQ_SCORE_MAP.get(respuestas.get("pregunta_18"), 0)
    p_comp7_q19 = Q19_SCORE_MAP.get(respuestas.get("pregunta_19"), 0)
    suma_comp7 = p_comp7_q18 + p_comp7_q19
    p_comp7 = DIFUSION_FINAL_MAP.get(suma_comp7, 3) # Asumir 3 si es > 6
    puntuaciones["Disfunción diurna"] = p_comp7

    # 8. Total de puntos
    puntaje_total = sum(puntuaciones.values())

    # 9. Descripción según puntaje
    interpretacion = INTERPRETACION_FINAL_MAP.get(puntaje_total, "Problema grave de sueño")

    resultado = {
        "Puntaje Total": puntaje_total,
        "Interpretacion": interpretacion
    }
    
    return puntuaciones, resultado


def crear_interfaz_psqi(supabase: Client):
    st.components.v1.html("<script>window.top.scrollTo(0, 0);</script>", height=0)
    st.title("Índice de Calidad del Sueño de Pittsburgh (PSQI)")
    st.markdown("---")
    st.info(
        """
        **Instrucciones:** Las siguientes preguntas hacen referencia a cómo a dormido usted.
        Intente ajustarse en sus respuestas de la manera más exacta posible a lo ocurrido durante la mayor parte de los días y/o noches del último mes.
        Por favor, responda a todas las preguntas que sean obligatorias.
        """
    )

    with st.form(key="psqi_form"):
        st.markdown("---")
        comprende = st.checkbox("Sí, comprendo las instrucciones.", key="comprende_psqi")
        st.markdown("---")

        respuestas_usuario = {}

        # Preguntas 1-4 (Selectores)
        for i in range(1, 5):
            st.write(f"**{i}.- {QUESTIONS_TEXT.get(i, f'Texto pregunta {i} no definido')}**")
            respuestas_usuario[f"pregunta_{i}"] = st.selectbox(
                f"Respuesta {i}",
                SELECTOR_OPTIONS.get(i, ["Definir opciones"]),
                key=f"q_{i}",
                index=None,
                 label_visibility="collapsed"
            )
            st.markdown("---")

        # Preguntas 5-14 (Frecuencia)
        for i in range(5, 15):
            st.write(f"**{i}.- {QUESTIONS_TEXT.get(i, f'Texto pregunta {i} no definido')}**")
            respuestas_usuario[f"pregunta_{i}"] = st.radio(
                f"Respuesta {i}",
                FREQ_OPTIONS,
                key=f"q_{i}",
                index=None,
                horizontal=False, 
                label_visibility="collapsed"
            )
            st.markdown("---")

        # Pregunta 15 (Texto opcional)
        st.write(f"**15.- {QUESTIONS_TEXT.get(15, f'Texto pregunta 15 no definido')}**")
        respuestas_usuario["pregunta_15"] = st.text_input("Descripción (opcional)", key="q_15")
        st.markdown("---")

        # Pregunta 16 (Calidad global)
        st.write(f"**16.- {QUESTIONS_TEXT.get(16, f'Texto pregunta 16 no definido')}**")
        respuestas_usuario["pregunta_16"] = st.radio(
            "Respuesta 16",
            Q16_OPTIONS,
            key="q_16",
            index=None,
            horizontal=False,
            label_visibility="collapsed"
        )
        st.markdown("---")

        # Preguntas 17-18 (Frecuencia)
        for i in range(17, 19):
            st.write(f"**{i}.- {QUESTIONS_TEXT.get(i, f'Texto pregunta {i} no definido')}**")
            respuestas_usuario[f"pregunta_{i}"] = st.radio(
                f"Respuesta {i}",
                FREQ_OPTIONS,
                key=f"q_{i}",
                index=None,
                horizontal=False,
                label_visibility="collapsed"
            )
            st.markdown("---")

        # Pregunta 19 (Problema entusiasmo)
        st.write(f"**19.- {QUESTIONS_TEXT.get(19, f'Texto pregunta 19 no definido')}**")
        respuestas_usuario["pregunta_19"] = st.radio(
            "Respuesta 19",
            Q19_OPTIONS,
            key="q_19",
            index=None,
            horizontal=False,
            label_visibility="collapsed"
        )

        siguiente_button = st.form_submit_button("Siguiente")

        if siguiente_button:
            if 'ficha_id' not in st.session_state:
                st.error("Error crítico: No se encontró el ID de la ficha de ingreso.")
                return

            # Verificar que todas las preguntas (excepto la 15 opcional) hayan sido respondidas
            errores = []
            for i in range(1, 20):
                 if i != 15 and respuestas_usuario.get(f"pregunta_{i}") is None:
                      errores.append(f"Pregunta {i}")

            if errores:
                st.error("Por favor, responda todas las preguntas obligatorias. Faltan: " + ", ".join(errores))
            else:
                with st.spinner("Calculando y guardando resultados..."):
                    
                    # --- NUEVO: Realizar cálculos ---
                    puntuaciones, resultado = calcular_psqi(respuestas_usuario)

                    # --- MODIFICADO: Guardar datos calculados en JSON ---
                    psqi_data_to_save = {
                        "id": st.session_state.ficha_id,
                        "comprende": comprende,
                        **respuestas_usuario,
                        # --- CORRECCIÓN: Se añade ensure_ascii=False ---
                        "puntuaciones": json.dumps(puntuaciones, ensure_ascii=False),
                        "resultado": json.dumps(resultado, ensure_ascii=False)
                    }

                    try:
                        response = supabase.from_('test_psqi').insert(psqi_data_to_save).execute()
                        if response.data:
                            # Guardar las respuestas raw y los resultados para el PDF
                            if 'form_data' not in st.session_state:
                                st.session_state.form_data = {}
                            st.session_state.form_data['test_psqi'] = {
                                "respuestas": respuestas_usuario,
                                "puntuaciones": puntuaciones,
                                "resultado": resultado
                            }

                            st.session_state.current_test_index += 1
                            st.rerun()
                        else:
                            st.error(f"Error al guardar los resultados: {response.error.message if response.error else 'Error desconocido'}")
                    except Exception as e:
                        st.error(f"Ocurrió una excepción al intentar guardar los resultados: {e}")

