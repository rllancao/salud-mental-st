import streamlit as st
from supabase import Client

# --- Interfaz del Test de Epworth ---
def crear_interfaz_epworth(supabase: Client):
    st.title("Test de Somnolencia de Epworth")
    st.markdown("---")

    # --- Instrucciones del Test ---
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
        # --- Pregunta de Comprensión ---
        st.markdown("---")
        st.text("¿Comprende las instrucciones del test?")
        comprende = st.checkbox("Sí, comprendo la instrucción.")
        st.markdown("---")

        # --- Preguntas del Test ---
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

        respuestas = {}
        for key, pregunta in preguntas.items():
            respuestas[key] = st.radio(
                label=pregunta,
                options=[0, 1, 2, 3],
                horizontal=True,
                key=key
            )
        
        # --- Botón de Siguiente/Finalizar ---
        siguiente_button = st.form_submit_button("Siguiente")

        if siguiente_button:
            if 'ficha_id' not in st.session_state:
                st.error("Error crítico: No se encontró el ID de la ficha de ingreso. Por favor, vuelva a empezar.")
                return

            # Recopilar los datos del formulario para uso local (generación de PDF)
            epworth_data_local = {
                "comprende": comprende,
                **respuestas
            }
            
            # Guardar en session_state para la generación del PDF al final
            if 'form_data' not in st.session_state:
                st.session_state.form_data = {}
            st.session_state.form_data['test_epworth'] = epworth_data_local
            
            # Preparar datos para enviar a la base de datos
            epworth_data_db = epworth_data_local.copy()
            epworth_data_db['id'] = st.session_state.ficha_id
            epworth_data_db['estado'] = 'Completado'
            
            # Enviar a Supabase
            try:
                with st.spinner("Guardando resultados..."):
                    response = supabase.from_('test_epworth').insert(epworth_data_db).execute()
                    if response.data:
                        # Si el guardado es exitoso, avanzar al siguiente test
                        st.session_state.current_test_index += 1
                        st.rerun()
                    else:
                        st.error(f"Error al guardar los resultados del test: {response.error.message if response.error else 'Error desconocido.'}")
            
            except Exception as e:
                st.error(f"Ocurrió una excepción al intentar guardar los resultados: {e}")

