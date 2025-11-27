import streamlit as st
from supabase import Client

# --- RESPUESTAS CORRECTAS ---
# DEBES RELLENAR ESTE DICCIONARIO CON LAS ALTERNATIVAS CORRECTAS PARA CADA PREGUNTA
CORRECT_ANSWERS = {
    1: "C", 2: "A", 3: "D", 4: "B", 5: "E", 6: "A", 7: "C", 8: "E", 9: "D",
    10: "B", 11: "B", 12: "B", 13: "C", 14: "B", 15: "B", 16: "C", 17: "D", 18: "D",
    19: "B", 20: "D", 21: "B", 22: "A", 23: "A", 24: "C", 25: "A", 26: "C", 27: "B",
    28: "D", 29: "A", 30: "D", 31: "C", 32: "E", 33: "D", 34: "D", 35: "E", 36: "E"
}

def calcular_alerta(processed_results):
    total_score = sum(processed_results.values())
    interpretacion = "No definida"
    if 1 <= total_score <= 7: interpretacion = "Inferior"
    elif 8 <= total_score <= 14: interpretacion = "Inferior al término medio"
    elif 15 <= total_score <= 20: interpretacion = "Promedio"
    elif 23 <= total_score <= 29: interpretacion = "Superior al promedio" # Ajustado según tabla
    elif 30 <= total_score <= 36: interpretacion = "Superior"
    return total_score, interpretacion

def crear_interfaz_alerta(supabase: Client):
    st.components.v1.html("<script>window.top.scrollTo(0, 0);</script>", height=0)
    st.title("Test de Alerta")
    st.markdown("---")
    st.info(
        """
        **Instrucciones:** A continuación, se le presentarán 36 problemas. 
        Cada problema consiste en una imagen y una pregunta. 
        Seleccione la alternativa (A, B, C, D o E) que considere correcta.
        """
    )

    with st.form(key="alerta_form"):
        st.markdown("---")
        comprende = st.checkbox("Sí, comprendo las instrucciones.", key="comprende_alerta")
        st.markdown("---")
        
        respuestas_usuario = {}
        
        # --- EJEMPLO ---
        st.write("**EJEMPLO: En el cuadro 1 aparece una vela encendida y una ventana abierta, cuyas cortinas, movidas por el viento hacia la vela, pueden incendiarse. Por lo tanto, usted debe marcar la letra C, porque la vela encendida es el objeto peligroso.**")
        try:
            st.image("alerta_images/ejemplo.png", width=400)
        except Exception:
            st.warning("Imagen de ejemplo 'alerta_images/ejemplo.png' no encontrada.")
        st.markdown("---")


        # --- BUCLE SIMPLIFICADO: Itera de 1 a 36 ---
        for i in range(1, 37):
            st.write(f"**{i}.- Identifique la letra del objeto que representa un mayor peligro:**")
            try:
                st.image(f"alerta_images/pregunta_{i}.png", width=400)
            except Exception: st.warning(f"Imagen 'alerta_images/pregunta_{i}.png' no encontrada.")
            respuestas_usuario[f"pregunta_{i}"] = st.radio(f"Alternativas {i}", ["A", "B", "C", "D", "E"], key=f"q_{i}", horizontal=True, index=None, label_visibility="collapsed")
            if i < 36: st.markdown("---")

        siguiente_button = st.form_submit_button("Siguiente")

        if siguiente_button:
            if 'ficha_id' not in st.session_state:
                st.error("Error crítico: No se encontró el ID.")
                return

            errores = [f"Pregunta {i}" for i in range(1, 37) if respuestas_usuario.get(f"pregunta_{i}") is None]
            
            if errores:
                st.error("Responda todas las preguntas: " + ", ".join(errores))
            else:
                with st.spinner("Guardando..."):
                    # Procesar respuestas (1/0)
                    processed_results = {}
                    for i in range(1, 37):
                        key = f"pregunta_{i}"
                        correcta = CORRECT_ANSWERS.get(i)
                        processed_results[key] = 1 if respuestas_usuario[key] == correcta else 0

                    # --- NUEVO: Calcular resultados ---
                    puntaje_total, interpretacion = calcular_alerta(processed_results)

                    # --- MEJORA: Datos a guardar en Supabase ---
                    alerta_data_to_save = {
                        "id": st.session_state.ficha_id,
                        "comprende": comprende,
                        **processed_results, # Guardar 1 o 0
                        "puntaje_total": puntaje_total,
                        "interpretacion": interpretacion
                    }
                    
                    try:
                        response = supabase.from_('test_alerta').insert(alerta_data_to_save).execute()
                        if response.data:
                            # Guardar respuestas originales y resultados para PDF
                            st.session_state.form_data['test_alerta'] = {
                                "comprende": comprende,
                                **respuestas_usuario, # Guardar A, B, C...
                                "puntaje_total": puntaje_total,
                                "interpretacion": interpretacion
                            }
                            st.session_state.current_test_index += 1
                            st.rerun()
                        else:
                            st.error(f"Error al guardar: {response.error.message if response.error else 'Error'}")
                    except Exception as e:
                        st.error(f"Excepción al guardar: {e}")


