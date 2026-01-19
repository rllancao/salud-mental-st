import streamlit as st
from supabase import Client

def crear_interfaz_intro(supabase: Client):
    # Forzar scroll al inicio al cargar esta vista
    st.components.v1.html("<script>window.scrollTo(0,0);</script>", height=0)

    st.title("Bienvenido/a a su Evaluación Psicológica")
    st.markdown("---")

    st.markdown(
        """
        <div style="text-align: justify; font-size: 1.1em;">
            Ha completado exitosamente su ficha de ingreso. A continuación, dará inicio a una serie de 
            tests psicológicos diseñados para evaluar distintos aspectos de su perfil.
            <br><br>
            Antes de comenzar, es importante que tenga en cuenta la siguiente información para que pueda 
            rendir sus pruebas con tranquilidad y eficacia:
        </div>
        """, 
        unsafe_allow_html=True
    )

    st.markdown("### 🕒 **Tipos de Evaluaciones y Tiempos**")
    st.info(
        """
        * **Tests con Tiempo Límite:** Algunas pruebas miden su velocidad y precisión (como ejercicios de lógica o patrones). 
            En estos casos, verá un **reloj en pantalla** indicando el tiempo restante. Si el tiempo se acaba, el sistema guardará automáticamente lo que haya alcanzado a responder.
            * *Consejo:* No se detenga demasiado en una pregunta difícil; avance y trate de contestar la mayor cantidad posible.
        
        * **Tests Sin Límite de Tiempo:** Otras pruebas, como los cuestionarios de personalidad, no tienen tiempo límite. 
            Tómese el tiempo necesario para leer y responder sinceramente.
        """
    )

    st.markdown("### ✅ **Sobre las Respuestas**")
    st.success(
        """
        * **No hay respuestas "buenas" o "malas"** en los tests de personalidad. Lo importante es que su respuesta refleje **su** forma de ser o pensar real.
        * En las pruebas de lógica o habilidad, sí existen respuestas correctas, pero **no se espera que conteste todo perfecto**. Están diseñadas para medir su nivel actual.
        * Algunas preguntas pueden parecer repetitivas o extrañas; esto es normal en las evaluaciones psicológicas. Por favor, responda todas.
        """
    )

    st.markdown("### 📋 **Instrucciones Generales**")
    st.warning(
        """
        1.  **Lea atentamente** las instrucciones al inicio de cada test antes de presionar "Empezar".
        2.  Asegúrese de estar en un lugar tranquilo y sin distracciones.
        3.  No utilice ayuda externa (calculadoras, internet, otras personas) a menos que se indique lo contrario.
        4.  Si se siente cansado/a entre tests, puede tomar un breve respiro antes de iniciar el siguiente, pero una vez que inicie un test con tiempo, no podrá detener el reloj.
        """
    )

    st.markdown("---")
    st.write("Si está listo/a para comenzar, presione el botón a continuación.")
    st.write("")

    col_izq, col_centro, col_der = st.columns([1, 2, 1])
    with col_centro:
        if st.button("🚀 Comenzar Evaluaciones", type="primary", use_container_width=True):
            # Cambiar el estado para avanzar al primer test
            st.session_state.step = "test"
            st.rerun()