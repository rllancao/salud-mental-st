import streamlit as st
from supabase import Client
import time
import base64

# --- RESPUESTAS CORRECTAS ---
CORRECT_ANSWERS = {
    1: "C", 2: "A", 3: "D", 4: "B", 5: "E", 6: "A", 7: "C", 8: "E", 9: "D",
    10: "B", 11: "B", 12: "B", 13: "C", 14: "B", 15: "B", 16: "C", 17: "D", 18: "D",
    19: "B", 20: "D", 21: "B", 22: "A", 23: "A", 24: "C", 25: "A", 26: "C", 27: "B",
    28: "D", 29: "A", 30: "D", 31: "C", 32: "E", 33: "D", 34: "D", 35: "E", 36: "E"
}

def get_image_as_base64(path):
    """Encodes an image file to a base64 string for embedding in HTML."""
    try:
        with open(path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
    except FileNotFoundError:
        # No mostramos warning invasivo si falla el gif, solo logueamos o ignoramos
        return None

def calcular_alerta(processed_results):
    total_score = sum(processed_results.values())
    interpretacion = "No definida"
    if 1 <= total_score <= 7: interpretacion = "Inferior"
    elif 8 <= total_score <= 14: interpretacion = "Inferior al término medio"
    elif 15 <= total_score <= 20: interpretacion = "Promedio"
    elif 23 <= total_score <= 29: interpretacion = "Superior al promedio" 
    elif 30 <= total_score <= 36: interpretacion = "Superior"
    return total_score, interpretacion

def crear_interfaz_alerta(supabase: Client):
    # --- CONTROL DE ESTADO Y SCROLL ---
    
    # Inicializar estado si no existe
    if 'alerta_started' not in st.session_state:
        st.session_state.alerta_started = False

    # --- SCROLL TO TOP ROBUSTO ---
    # Inyectamos el estado 'alerta_started' en el script para que cambie cuando
    # el usuario presiona "Empezar Test", forzando la re-ejecución del scroll.
    st.components.v1.html(
        f"""
        <script>
            // Status: {st.session_state.alerta_started} (Fuerza actualización al cambiar estado)
            
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

    st.title("Test de Alerta")
    st.markdown("---")

    # --- Estado 1: Instrucciones (Pantalla Previa) ---
    if not st.session_state.alerta_started:
        st.info(
            """
            **LO QUE USTED VA A HACER:** Esta prueba consiste en identificar situaciones de peligro.
            A continuación se le mostrarán varias imágenes. Usted debe observarlas y determinar cuál es el objeto o situación que representa un riesgo.
            \n**NO PRESIONE EL BOTÓN DE "EMPEZAR" HASTA QUE SE LE INDIQUE.**
            """
        )
        
        st.write("### Ejemplo:")
        st.write("**En el cuadro de ejemplo aparece una vela encendida y una ventana abierta, cuyas cortinas, movidas por el viento hacia la vela, pueden incendiarse.**")
        
        col_ej, col_txt = st.columns([1, 2])
        with col_ej:
            try:
                st.image("alerta_images/ejemplo.png", width=300)
            except Exception:
                st.warning("Imagen de ejemplo no encontrada.")
        with col_txt:
            st.success("**Respuesta Correcta:** La letra **C**, porque la vela encendida es el objeto peligroso.")

        st.warning(
            """
            **TIEMPO LÍMITE:**
            HAY 36 PREGUNTAS Y USTED TIENE **SOLO 9 MINUTOS** PARA CONTESTAR.
            TRABAJE RÁPIDO Y CONTESTE LO MEJOR QUE PUEDA.
            """
        )

        st.markdown("---")
        comprende = st.checkbox("Sí, comprendo las instrucciones.", key="comprende_alerta")
        st.markdown("---")

        if st.button("Empezar Test", type="primary"):
            st.session_state.alerta_started = True
            st.session_state.alerta_comprende = comprende
            st.session_state.alerta_start_time = time.time()
            st.session_state.alerta_submitted = False
            st.rerun()

    # --- Estado 2: El Test (Con Temporizador) ---
    else:
        # Inicializar tiempos si se recarga la página
        if 'alerta_start_time' not in st.session_state:
            st.session_state.alerta_start_time = time.time()
        if 'alerta_submitted' not in st.session_state:
            st.session_state.alerta_submitted = False

        # Cálculo del tiempo
        elapsed_time = time.time() - st.session_state.alerta_start_time
        remaining_time = 540 - elapsed_time # 9 minutos = 540 segundos
        is_time_up = remaining_time <= 0

        # --- Mostrar Temporizador GIF ---
        if not st.session_state.get('alerta_submitted', False):
            gif_base64 = get_image_as_base64("9-minute.gif")
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

        with st.form(key="alerta_form"):
            # Bucle de preguntas 1 a 36
            for i in range(1, 37):
                st.write(f"**{i}.- Identifique la letra del objeto que representa un mayor peligro:**")
                try:
                    st.image(f"alerta_images/pregunta_{i}.png", width=400)
                except Exception: 
                    st.warning(f"Imagen 'alerta_images/pregunta_{i}.png' no encontrada.")
                
                respuestas_usuario[f"pregunta_{i}"] = st.radio(
                    f"Alternativas {i}", 
                    ["A", "B", "C", "D", "E"], 
                    key=f"q_{i}", 
                    horizontal=True, 
                    index=None, 
                    label_visibility="collapsed"
                )
                if i < 36: st.markdown("---")

            siguiente_button = st.form_submit_button("Finalizar y Guardar")

        # --- Lógica de Envío (Manual o Automática por Tiempo) ---
        if siguiente_button or is_time_up:
            if not st.session_state.alerta_submitted:
                st.session_state.alerta_submitted = True # Evitar doble envío

                if 'ficha_id' not in st.session_state:
                    st.error("Error crítico: No se encontró el ID de la ficha.")
                    return

                if is_time_up:
                    st.warning("⏳ El tiempo se ha acabado. Se enviarán las respuestas registradas hasta ahora.")
                
                # Verificación opcional de respuestas vacías (solo si no se acabó el tiempo)
                errores = []
                if not is_time_up:
                    errores = [f"Pregunta {i}" for i in range(1, 37) if respuestas_usuario.get(f"pregunta_{i}") is None]

                if errores:
                    st.error("Por favor responda todas las preguntas antes de finalizar: " + ", ".join(errores))
                    st.session_state.alerta_submitted = False # Permitir intentar de nuevo
                else:
                    with st.spinner("Calculando y guardando resultados..."):
                        # Procesar respuestas (1/0)
                        processed_results = {}
                        for i in range(1, 37):
                            key = f"pregunta_{i}"
                            correcta = CORRECT_ANSWERS.get(i)
                            # Si se acabó el tiempo y no respondió, cuenta como mala (None != correcta)
                            usuario_resp = respuestas_usuario.get(key)
                            processed_results[key] = 1 if usuario_resp == correcta else 0

                        # Calcular resultados
                        puntaje_total, interpretacion = calcular_alerta(processed_results)

                        # Datos a guardar en Supabase
                        alerta_data_to_save = {
                            "id": st.session_state.ficha_id,
                            "comprende": st.session_state.get("alerta_comprende", False),
                            **processed_results, 
                            "puntaje_total": puntaje_total,
                            "interpretacion": interpretacion
                        }
                        
                        try:
                            response = supabase.from_('test_alerta').insert(alerta_data_to_save).execute()
                            if response.data:
                                # Guardar en sesión para PDF
                                st.session_state.form_data['test_alerta'] = {
                                    "comprende": st.session_state.get("alerta_comprende", False),
                                    **respuestas_usuario, 
                                    "puntaje_total": puntaje_total,
                                    "interpretacion": interpretacion
                                }
                                
                                # Limpiar variables de sesión de este test
                                for key in ['alerta_started', 'alerta_comprende', 'alerta_start_time', 'alerta_submitted']:
                                    if key in st.session_state:
                                        del st.session_state[key]

                                st.session_state.current_test_index += 1
                                st.rerun()
                            else:
                                st.error(f"Error al guardar: {response.error.message if response.error else 'Error'}")
                        except Exception as e:
                            st.error(f"Excepción al guardar: {e}")

        # Actualizar el reloj si no se ha enviado
        elif not st.session_state.alerta_submitted:
            time.sleep(1)
            st.rerun()