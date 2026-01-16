import streamlit as st
from supabase import Client

# --- Función para calcular resultados de Epworth ---
def calcular_epworth(respuestas):
    # Suma los valores de las respuestas (0-3)
    total_score = sum(respuestas.values())
    interpretacion = "Normal."
    if 11 <= total_score <= 15:
        interpretacion = "Somnolencia diurna excesiva leve a moderada."
    elif total_score > 15:
        interpretacion = "Somnolencia diurna excesiva severa."
    return total_score, interpretacion

# --- Interfaz del Test de Epworth ---
def crear_interfaz_epworth(supabase: Client):
    st.title("Test de Somnolencia de Epworth")
    st.markdown("---")
    st.subheader("Instrucciones")
    st.info(
        """
        **¿Con qué frecuencia se podría usted quedar dormido en las siguientes situaciones, dentro de su jornada laboral?**
        Incluso si no ha realizado recientemente alguna de las actividades mencionadas a continuación, 
        trate de imaginar en qué medida le afectarían.
        *(En caso de no poder realizar alguna de las actividades que se mencionan en su trabajo, puede marcar 0)*
        """
    )
    
    with st.form(key="epworth_form"):
        st.markdown("---")
        st.text("¿Comprende las instrucciones del test?")
        comprende = st.checkbox("Sí, comprendo la instrucción.")
        st.markdown("---")
        st.write("**Forma de calificar:** 0 = Nunca / 1 = Escasa / 2 = Moderada / 3 = Elevada posibilidad")

        preguntas = {
            "sentado_leyendo": "Sentado y leyendo",
            "viendo_tv": "Viendo televisión",
            "sentado_publico": "Sentado en un lugar público (ej. cine, reunión).",
            "pasajero_auto": "Viajando como pasajero en un auto durante 1 hora",
            "descansando_tarde": "Descansando en la tarde cuando las circunstancias lo permiten",
            "sentado_conversando": "Sentado y conversando con alguien",
            "post_almuerzo": "Sentado en un ambiente tranquilo después del almuerzo (sin alcohol).",
            "auto_detenido": "En un auto, mientras se encuentra detenido por algunos minutos en el tráfico."
        }

        respuestas_usuario_raw = {}
        for key, pregunta in preguntas.items():
            respuestas_usuario_raw[key] = st.radio(
                label=pregunta,
                options=[0, 1, 2, 3],
                horizontal=True,
                key=key
            )
        
        siguiente_button = st.form_submit_button("Siguiente")

        if siguiente_button:
            if 'ficha_id' not in st.session_state:
                st.error("Error crítico: No se encontró el ID de la ficha de ingreso. Por favor, vuelva a empezar.")
                return

            with st.spinner("Guardando resultados..."):
                # 1. Calcular puntaje e interpretación
                puntaje_total, interpretacion = calcular_epworth(respuestas_usuario_raw)
                
                # 2. Preparar datos para Supabase (incluyendo resultados calculados)
                epworth_data_to_save = {
                    "id": st.session_state.ficha_id,
                    "comprende": comprende,
                    **respuestas_usuario_raw, # Guardar los puntajes 0-3
                    "puntaje_total": puntaje_total, 
                    "interpretacion": interpretacion, 
                    "estado": "Completado" 
                }
                
                # 3. Guardar datos completos en session_state para el PDF
                if 'form_data' not in st.session_state:
                    st.session_state.form_data = {}
                st.session_state.form_data['test_epworth'] = epworth_data_to_save 
                
                # 4. Enviar a Supabase
                try:
                    # --- CORRECCIÓN: Se elimina la comprobación explícita de response.error ---
                    response = supabase.from_('test_epworth').upsert(epworth_data_to_save).execute() 
                    
                    # Si no hubo excepción, asumimos que fue exitoso
                    st.session_state.current_test_index += 1
                    st.rerun()
                
                except Exception as e:
                     # Si execute() lanza una excepción, se captura aquí
                    st.error(f"Ocurrió una excepción al intentar guardar los resultados: {e}")

