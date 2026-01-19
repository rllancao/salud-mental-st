import streamlit as st
from supabase import Client
import time
import base64

# --- Helper function to encode image to base64 ---
def get_image_as_base64(path):
    """Encodes an image file to a base64 string for embedding in HTML."""
    try:
        with open(path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
    except FileNotFoundError:
        # No mostramos warning para no ensuciar la UI si falta el gif
        return None
    
# --- Función para calcular resultados de Wonderlic ---
def calcular_wonderlic(respuestas_correctas, edad_paciente):
    total_score_raw = sum(respuestas_correctas.values())
    ajuste = 0
    # Asegurarse que edad_paciente sea un número antes de comparar
    edad_paciente_num = 0
    if isinstance(edad_paciente, (int, float)):
        edad_paciente_num = edad_paciente
        
    if 30 <= edad_paciente_num <= 39: ajuste = 1
    elif 40 <= edad_paciente_num <= 49: ajuste = 2
    elif 50 <= edad_paciente_num <= 54: ajuste = 3
    elif 55 <= edad_paciente_num <= 60: ajuste = 4
    elif edad_paciente_num > 60: ajuste = 5
    puntaje_total = total_score_raw + ajuste

    interpretacion = "Excelente capacidad para sintetizar información, solucionar problemas y aprender rápidamente."
    if puntaje_total <= 15: interpretacion = "Capacidad regular para actividades nuevas, pero exitoso en tareas rutinarias."
    elif 16 <= puntaje_total <= 19: interpretacion = "Capaz de desarrollar actividades simples y repetitivas con efectividad."
    elif 20 <= puntaje_total <= 24: interpretacion = "Aprende rutinas rápidamente y se desempeña bien en tareas de mediana complejidad."
    elif 25 <= puntaje_total <= 34: interpretacion = "Muy buena capacidad de autoaprendizaje y análisis de problemas."
    
    return puntaje_total, interpretacion

# --- Interfaz del Test Wonderlic ---
def crear_interfaz_wonderlic(supabase: Client):
    # --- SCROLL TO TOP ROBUSTO ---
    # Se ejecuta cada vez que se carga/recarga la función (ej. al presionar Empezar Test)
    st.components.v1.html(
        """
        <script>
            // Intentar hacer scroll al elemento con ID 'inicio_pagina' (definido en maestro.py)
            var topElement = window.parent.document.getElementById('inicio_pagina');
            if (topElement) {
                topElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
            } else {
                // Fallback: scroll al top del contenedor principal
                var main = window.parent.document.querySelector('section.main');
                if (main) {
                    main.scrollTo(0, 0);
                } else {
                    window.scrollTo(0, 0);
                }
            }
        </script>
        """, 
        height=0
    )

    st.title("Test de Habilidad Cognitiva (Wonderlic)")
    st.markdown("---")

    # --- Estado 1: Instrucciones (Pantalla Previa) ---
    if 'wonderlic_started' not in st.session_state:
        st.session_state.wonderlic_started = False

    if not st.session_state.wonderlic_started:
        st.info(
            """
            **INSTRUCCIONES:**
            El siguiente cuestionario es de conocimientos generales. A continuación responda todas las preguntas que pueda.
            Si alguna la encuentra muy difícil o no sabe la respuesta, déjela sin responder y pase a la siguiente.
            \n**NO PRESIONE EL BOTÓN DE "EMPEZAR" HASTA QUE ESTÉ LISTO.**
            """
        )
        
        st.warning(
            """
            **TIEMPO LÍMITE:**
            TIENE UN MÁXIMO DE **12 MINUTOS** PARA COMPLETAR EL TEST.
            **(No debe usar calculadora)**
            """
        )
        
        st.markdown("---")
        comprende = st.checkbox("Sí, comprendo las instrucciones.", key="comprende_wonderlic_intro")
        st.markdown("---")

        if st.button("Empezar Test", type="primary"):
            st.session_state.wonderlic_started = True
            st.session_state.wonderlic_comprende = comprende
            st.session_state.wonderlic_start_time = time.time()
            st.session_state.wonderlic_submitted = False
            st.rerun()

    # --- Estado 2: El Test (Con Temporizador) ---
    else:
        # Inicializar tiempos si se recarga la página
        if 'wonderlic_start_time' not in st.session_state:
            st.session_state.wonderlic_start_time = time.time()
        if 'wonderlic_submitted' not in st.session_state:
            st.session_state.wonderlic_submitted = False

        # Cálculo del tiempo (15 minutos = 900 segundos)
        elapsed_time = time.time() - st.session_state.wonderlic_start_time
        remaining_time = 720 - elapsed_time
        is_time_up = remaining_time <= 0
        
        # --- Mostrar Temporizador GIF ---
        if not st.session_state.get('wonderlic_submitted', False):
            gif_base64 = get_image_as_base64("12-minute.gif")
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
        
        # --- PREGUNTAS DEL TEST (Dentro de un Form) ---
        with st.form(key="wonderlic_form"):
            st.write("**Pregunta 1:** El último mes del año es:")
            st.radio("Opciones para la pregunta 1", ["Enero", "Marzo", "Julio", "Diciembre", "Octubre"], key="q1", label_visibility="collapsed", horizontal=True, index=None)
            st.markdown("---")
            st.write("**Pregunta 2:** Capturar es lo contrario de:")
            st.radio("Opciones para la pregunta 2", ["Lugar", "Soltar", "Riesgo", "Aventura", "Degradar"], key="q2", label_visibility="collapsed", horizontal=True, index=None)
            st.markdown("---")
            st.write("**Pregunta 3:** La mayor parte de las palabras que siguen son parecidas. ¿Cuál es la que no tiene relación con las otras?")
            st.radio("Opciones para la pregunta 3", ["Enero", "Agosto", "Miércoles", "Octubre", "Diciembre"], key="q3", label_visibility="collapsed", horizontal=True, index=None)
            st.markdown("---")
            st.write("**Pregunta 4:** Conteste SI o NO:  R.S.V.P.  ¿Significa 'no se requiere una respuesta'?")
            st.radio("Opciones para la pregunta 4", ["Sí", "No"], key="q4", label_visibility="collapsed", horizontal=True, index=None)
            st.markdown("---")
            st.write("**Pregunta 5:** En el siguiente conjunto de palabras. ¿Qué palabra es diferente de las otras?")
            st.radio("Opciones para la pregunta 5", ["Tropa", "Grupo", "Participar", "Jauría", "Cuadrilla"], key="q5", label_visibility="collapsed", horizontal=True, index=None)
            st.markdown("---")
            st.write("**Pregunta 6:** USUAL es lo contrario de:")
            st.radio("Opciones para la pregunta 6", ["Raro", "Habitual", "Regular", "Constante", "Simple"], key="q6", label_visibility="collapsed", horizontal=True, index=None)
            st.markdown("---")
            st.write("**Pregunta 7:** ¿Qué figura se puede formar con las dos figuras que aparecen en paréntesis?")
            try: st.image("triangulo.png", width=800)
            except Exception: st.warning("Imagen 'triangulo.png' no encontrada.")
            st.radio("Opciones para la pregunta 7", ["A", "B", "C", "D", "E"], key="q7", horizontal=True, index=None)
            st.markdown("---")
            st.write("**Pregunta 8:** Fíjese en la siguiente progresión de números. ¿Qué número debe seguir? 8 - 4 - 2 - 1 - ½ - ¼")
            st.radio("Opciones para la pregunta 8", ["2", "3", "1/8", "1/9"], key="q8", label_visibility="collapsed", horizontal=True, index=None)
            st.markdown("---")
            st.write("**Pregunta 9:** CLIENTE / CONSUMIDOR son palabras que tienen significado:")
            st.radio("Opciones para la pregunta 9", ["Similar", "Contradictorio", "Ni similar ni contradictorio"], key="q9", label_visibility="collapsed", horizontal=True, index=None)
            st.markdown("---")
            st.write("**Pregunta 10:** ¿Cuál de estas palabras se relaciona con la acción de oler, así como los dientes se relacionan con la acción de masticar?:")
            st.radio("Opciones para la pregunta 10", ["Dulce", "Hediondez", "Olor", "Nariz", "Nieve"], key="q10", label_visibility="collapsed", horizontal=True, index=None)
            st.markdown("---")
            st.write("**Pregunta 11:** OTOÑO es lo contrario de:")
            st.radio("Opciones para la pregunta 11", ["Vacaciones", "Verano", "Primavera", "Invierno", "Nieve"], key="q11", label_visibility="collapsed", horizontal=True, index=None)
            st.markdown("---")
            st.write("**Pregunta 12:** Un tren recorre 300 pies en ½ segundo. A la misma velocidad. ¿Cuántos pies recorrerá en 10 segundos?:")
            st.radio("Opciones para la pregunta 12", ["4000", "1000", "3500", "6000"], key="q12", label_visibility="collapsed", horizontal=True, index=None)
            st.markdown("---")
            st.write("**Pregunta 13:** Suponga que los dos primeros enunciados son verdaderos. El último de ellos es: 'Estos muchachos son niños normales' - 'Todos los niños normales son activos' - 'Estos muchachos son activos'")
            st.radio("Opciones para la pregunta 13", ["Verdadero", "Falso", "Dudoso"], key="q13", label_visibility="collapsed", horizontal=True, index=None)
            st.markdown("---")
            st.write("**Pregunta 14:** REMOTO es lo contrario de:")
            st.radio("Opciones para la pregunta 14", ["Recluido", "Cercano", "Lejano", "Apresurado", "Exacto"], key="q14", label_visibility="collapsed", horizontal=True, index=None)
            st.markdown("---")
            st.write("**Pregunta 15:** Los dulces de limón se venden a 3 por 10 centavos. ¿Cuánto costará 1 ½ docena?")
            st.radio("Opciones para la pregunta 15", ["60", "55", "40", "65"], key="q15", label_visibility="collapsed", horizontal=True, index=None)
            st.markdown("---")
            st.write("**Pregunta 16:** ¿Cuántas de las cantidades enumeradas abajo son idénticas entre sí?")
            opciones_q16 = ["84721 - 84721", "9210651 - 9210561", "14201201 - 1410210", "96101101 - 961011161", "88884444 - 88884444"]
            cols_16 = st.columns(len(opciones_q16))
            for i, opcion in enumerate(opciones_q16): cols_16[i].checkbox(str(opcion), key=f"q16_{opcion}")
            st.markdown("---")
            st.write("**Pregunta 17:** Ordene las siguientes palabras para formar un enunciado verdadero y coherente. Luego, indique cuál es la última letra de la última palabra de la frase formada. Palabras: 'Una – verbo – oración – un – tiene – siempre'.")
            st.radio("Opciones para la pregunta 17", ["E", "O", "Siempre"], key="q17", label_visibility="collapsed", horizontal=True, index=None)
            st.markdown("---")
            st.write("**Pregunta 18:** Un muchacho tiene 5 años y su hermana el doble. Cuando el niño tenga 8 años. ¿Qué edad tendrá la hermana?")
            st.radio("Opciones para la pregunta 18", ["10", "13", "20", "11"], key="q18", label_visibility="collapsed", horizontal=True, index=None)
            st.markdown("---")
            st.write("**Pregunta 19:** Esta / Está; estas palabras tienen significado:")
            st.radio("Opciones para la pregunta 19", ["Similar", "Contradictorio", "Ni similar ni contradictorio"], key="q19", label_visibility="collapsed", horizontal=True, index=None)
            st.markdown("---")
            st.write("**Pregunta 20:** Suponga que los dos primeros enunciados son verdaderos. El último enunciado es:'Juan tiene la misma edad que Patricia' - 'Patricia es más joven que Pepe' - 'Juan es más joven que Pepe'")
            st.radio("Opciones para la pregunta 20", ["Verdadero", "Falso", "Ni similar ni contradictorio"], key="q20", label_visibility="collapsed", horizontal=True, index=None)
            st.markdown("---")
            st.write("**Pregunta 21:** Un agente de negocios compró unos barriles por \\$4.000, los vendió por \\$5.000, ganando \\$50 en cada uno. ¿Cuántos barriles había comprado?")
            st.radio("Opciones para la pregunta 21", ["50", "21", "20", "19"], key="q21", label_visibility="collapsed", horizontal=True, index=None)
            st.markdown("---")
            st.write("**Pregunta 22:** Supongamos que usted ordena las siguientes palabras, de tal manera que formen una frase completa. Si es un enunciado verdadero, marque una V, pero si es falso marque una F \"Huevos – ponen – todas – las – gallinas\"")
            st.radio("Opciones para la pregunta 22", ["V", "F"], key="q22", label_visibility="collapsed", horizontal=True, index=None)
            st.markdown("---")
            st.write("**Pregunta 23:** Dos de los siguientes refranes tienen el mismo significado. ¿Cuáles son?")
            opciones_q23 = ["a) Dime con quién andas y te diré quién eres", "b) Hijo de tigre sale pintado", "c) Perro que ladra no muerde", "d) En casa de herrero, cuchillo de palo", "e) De tal palo, tal astilla"]
            cols_23 = st.columns(len(opciones_q23))
            for i, opcion in enumerate(opciones_q23): cols_23[i].checkbox(str(opcion), key=f"q23_{opcion}")
            st.markdown("---")
            st.write("**Pregunta 24:** Un reloj se atrasó un minuto y 18 segundos en 39 días. ¿Cuántos segundos se atrasó en cada día?")
            st.radio("Opciones para la pregunta 24", ["1", "5","2","4"], key="q24", label_visibility="collapsed", horizontal=True, index=None)
            st.markdown("---")
            st.write("**Pregunta 25:** TAZA / TASA; estas palabras tienen significado:")
            st.radio("Opciones para la pregunta 25", ["Similar", "Contradictorio","Ni similar ni contradictorio"], key="q25", label_visibility="collapsed", horizontal=True, index=None)
            st.markdown("---")
            st.write("**Pregunta 26:** Suponga que los dos primeros enunciados son verdaderos. El último de ellos es: 'Todos los cuáqueros son pacifistas' - 'Algunas de las personas de este cuarto son cuáqueros' - 'Algunas de las personas de este cuarto son pacifistas'")
            st.radio("Opciones para la pregunta 26", ["Verdadero", "Falso","Dudoso"], key="q26", label_visibility="collapsed", horizontal=True, index=None)
            st.markdown("---")
            st.write("**Pregunta 27:** En 30 días un muchacho ahorró \\$100. ¿Cuál fue su ahorro promedio diario?")
            st.radio("Opciones para la pregunta 27", ["0.31", "1", "3.33 o 3 1/3", "3"], key="q27", label_visibility="collapsed", horizontal=True, index=None)
            st.markdown("---")
            st.write("**Pregunta 28:** INGENIOSO / INGENUO; estas palabras tienen significado:")
            st.radio("Opciones para la pregunta 28", ["Similar", "Contradictorio", "Ni similar ni contradictorio"], key="q28", label_visibility="collapsed", horizontal=True, index=None)
            st.markdown("---")
            st.write("**Pregunta 29:** Dos hombres pescaron 36 pescados: X pescó 5 veces más que Y. ¿Cuántos pescados pescó Y?")
            st.radio("Opciones para la pregunta 29", ["6", "4", "11", "5"], key="q29", label_visibility="collapsed", horizontal=True, index=None)
            st.markdown("---")
            st.write("**Pregunta 30:** Un recipiente rectangular, completamente lleno, contiene 800 pies cúbicos de granos. Si el recipiente tiene 8 pies de ancho y 10 pies de largo. ¿Cuál es la altura del recipiente?")
            st.radio("Opciones para la pregunta 30", ["10", "11", "19", "20"], key="q30", label_visibility="collapsed", horizontal=True, index=None)
            st.markdown("---")
            st.write("**Pregunta 31:** Uno de los números de la siguiente serie, no tiene relación con los demás. Identifique el número que no concuerda con la serie y marque la opción con el número correcto : ½ - ¼ - 1/6 - 1/8 - 1/9 - 1/12")
            st.radio("Opciones para la pregunta 31", ["1/9", "1/6", "1/5"], key="q31", label_visibility="collapsed", horizontal=True, index=None)
            st.markdown("---")
            st.write("**Pregunta 32:** Conteste esta pregunta SI o NO. ¿Significa A.C. ¿Antes de Cristo?")
            st.radio("Opciones para la pregunta 32", ["Sí", "No"], key="q32", label_visibility="collapsed", horizontal=True, index=None)
            st.markdown("---")
            st.write("**Pregunta 33:** Coser / Cocer; estas palabras tienen significado:")
            st.radio("Opciones para la pregunta 33", ["Similar", "Contradictorio", "Ni similar ni contradictorio"], key="q33", label_visibility="collapsed", horizontal=True, index=None)
            st.markdown("---")
            st.write("**Pregunta 34:** Una falda requiere 2 ½ yardas de tela. ¿Cuántas faldas se pueden cortar de una pieza de 45 yardas?")
            st.radio("Opciones para la pregunta 34", ["20", "18", "15", "10"], key="q34", label_visibility="collapsed", horizontal=True, index=None)
            st.markdown("---")
            st.write("**Pregunta 35:** Un reloj tenía la hora precisa al mediodía del lunes. A las 2 de la tarde del miércoles se atrasaba 25 segundos. Al mismo ritmo, ¿Cuántos segundos se atrasaría en ½ hora?")
            st.radio("Opciones para la pregunta 35", ["1/2", "1/4", "1/8", "1"], key="q35", label_visibility="collapsed", horizontal=True, index=None)
            st.markdown("---")
            st.write("**Pregunta 36:** Nuestro equipo de baseball perdió 9 juegos esta temporada, lo que representa 1/8 del total de partidos jugados. ¿Cuántos partidos jugaron esta temporada?")
            st.radio("Opciones para la pregunta 36", ["72", "24", "34"], key="q36", label_visibility="collapsed", horizontal=True, index=None)
            st.markdown("---")
            st.write("**Pregunta 37:** ¿Cuál es el siguiente número de esta serie? : 1 - 0.5 - 0.25 - 0.125")
            st.radio("Opciones para la pregunta 37", ["0.0625", "0.05", "0.6"], key="q37", label_visibility="collapsed", horizontal=True, index=None)
            st.markdown("---")
            st.write("**Pregunta 38:** Esta figura geométrica puede ser dividida en dos partes por una línea recta, y éstas pueden unirse de manera que formen un cuadrado perfecto. Marque los números por donde trazaría la línea recta.")
            try: st.image("trazos.png", width=600)
            except Exception: st.warning("Imagen 'trazos.png' no encontrada.")
            st.radio("Opciones para la pregunta 38", ["4 y 10", "6 y 9", "3 y 10"], key="q38", horizontal=True, index=None)
            st.markdown("---")
            st.write("**Pregunta 39:** Los significados de las siguientes oraciones son: 'Una escoba nueva limpia bien' - 'Los zapatos viejos son más cómodos'.")
            st.radio("Opciones para la pregunta 39", ["Similares", "Contradictorios", "Ni similares ni contradictorios"], key="q39", label_visibility="collapsed", horizontal=True, index=None)
            st.markdown("---")
            st.write("**Pregunta 40:** ¿Cuántos de los cinco pares de nombres escritos abajo son idénticos entre sí?.")
            try: st.image("nombres.png", width=400)
            except Exception: st.warning("Imagen 'nombres.png' no encontrada.")
            st.radio("Opciones para la pregunta 40", ["1", "2", "3", "4", "5"], key="q40", horizontal=True, index=None)
            st.markdown("---")
            st.write("**Pregunta 41:** Dos de los siguientes refranes tienen significados similares. ¿Cuáles son?")
            opciones_q41 = ["a) El que está en el lodo querrá meter al otro", "b) Más vale tarde que nunca", "c) Con la vara que midas serás medido", "d) Mal de muchos, consuelo de tontos", "e) Perro que ladra no muerde"]
            cols_41 = st.columns(len(opciones_q41))
            for i, opcion in enumerate(opciones_q41): cols_41[i].checkbox(str(opcion), key=f"q41_{opcion}")
            st.markdown("---")
            st.write("**Pregunta 42:** Esta figura geométrica puede ser dividida en dos partes por una línea recta y éstas se pueden unir de cierta manera, para formar un cuadrado perfecto. Marque los números por donde trazaría la línea recta.")
            try: st.image("trazos2.png", width=600)
            except Exception: st.warning("Imagen 'trazos2.png' no encontrada.")
            st.radio("Opciones para la pregunta 42", ["7 y 17", "2 y 23", "3 y 22", "5 y 7"], key="q42", horizontal=True, index=None)
            st.markdown("---")
            st.write("**Pregunta 43:** ¿Cuáles de los números en el siguiente grupo representa la cantidad más pequeña?")
            st.radio("Opciones para la pregunta 43", ["10", "1", "0.999", "0.33", "11"], key="q43", label_visibility="collapsed", horizontal=True, index=None)
            st.markdown("---")
            st.write("**Pregunta 44:** Los significados de las siguientes oraciones son: 'Nadie se arrepintió jamás de su honestidad' - 'La honestidad se elogia, pero no se paga'.")
            st.radio("Opciones para la pregunta 44", ["Similares", "Contradictorios", "Ni similares ni contradictorios"], key="q44", label_visibility="collapsed", horizontal=True, index=None)
            st.markdown("---")
            st.write("**Pregunta 45:** Por \\$180 un tendero compra un cajón de naranjas de 12 docenas. Se sabe que 2 docenas se pudrirán antes que él pueda venderlas. ¿A cuánto debe vender la docena de lo que le queda para ganar 1/3 sobre el costo total?")
            st.radio("Opciones para la pregunta 45", ["\\$24", "\\$20", "\\$22.50", "\\$25"], key="q45", label_visibility="collapsed", horizontal=True, index=None)
            st.markdown("---")
            st.write("**Pregunta 46:** En el siguiente grupo de palabras. ¿Cuál de ellas es diferente de las otras?")
            st.radio("Opciones para la pregunta 46", ["Colonia", "Compañera", "Pollada", "Tripulación", "Constelación"], key="q46", label_visibility="collapsed", horizontal=True, index=None)
            st.markdown("---")
            st.write("**Pregunta 47:** Suponga que los dos primeros enunciados son verdaderos. Es el último:'Los genios son ridiculizados' - 'Yo soy ridiculizado' - 'Yo soy un genio'")
            st.radio("Opciones para la pregunta 47", ["Verdadero", "Falso", "Dudoso"], key="q47", label_visibility="collapsed", horizontal=True, index=None)
            st.markdown("---")
            st.write("**Pregunta 48:** ¿Cuánto recibiría X adicionalmente, en comparación con Y y Z, al repartir las ganancias de \\$1,500 entre tres socios que han invertido respectivamente \\$4,500, \\$3,500 y \\$2,000, si la distribución se realiza en proporción a la cantidad invertida?")
            st.radio("Opciones para la pregunta 48", ["\\$175", "\\$250", "\\$300", "\\$350"], key="q48", label_visibility="collapsed", horizontal=True, index=None)
            st.markdown("---")
            st.write("**Pregunta 49:** Cuatro de las cinco figuras pueden ser unidas para formar un triángulo. ¿Cuáles son?")
            try: st.image("formas.png", width=800)
            except Exception: st.warning("Imagen 'formas.png' no encontrada.")
            opciones_q49 = ["A", "B", "C", "D", "E"]
            cols_49 = st.columns(len(opciones_q49))
            for i, opcion in enumerate(opciones_q49): cols_49[i].checkbox(str(opcion), key=f"q49_{opcion}")
            st.markdown("---")
            st.write("**Pregunta 50:** ¿Cuántas páginas de tamaño más pequeño deben imprimirse para un artículo de 30,000 palabras, considerando que una página grande contiene 1,200 palabras y una página pequeña contiene 1,500 palabras, y la revista tiene un límite de 22 páginas?")
            st.radio("Opciones para la pregunta 50", ["10", "12", "15", "20"], key="q50", label_visibility="collapsed", horizontal=True, index=None)

            siguiente_button = st.form_submit_button("Finalizar y Guardar")

        # --- Lógica de Envío (Manual o Automática) ---
        if siguiente_button or is_time_up:
            if not st.session_state.wonderlic_submitted:
                st.session_state.wonderlic_submitted = True # Evitar doble envío
                
                if 'ficha_id' not in st.session_state:
                    st.error("Error crítico: No se encontró el ID de la ficha de ingreso.")
                    return
                
                if 'datos_paciente' not in st.session_state or 'edad' not in st.session_state.datos_paciente:
                     st.error("Error crítico: No se encontraron los datos del paciente (edad).")
                     return
                edad_paciente = st.session_state.datos_paciente.get('edad') or 0 

                if is_time_up:
                    st.warning("⏳ El tiempo se ha acabado. Se enviarán las respuestas registradas hasta ahora.")
                
                with st.spinner("Procesando y guardando respuestas..."):
                    # Lógica de Corrección
                    resultados_correctas = {f'pregunta_{i}': 0 for i in range(1, 51)}
                    resultados_correctas['pregunta_1'] = 1 if st.session_state.get('q1') == "Diciembre" else 0
                    resultados_correctas['pregunta_2'] = 1 if st.session_state.get('q2') == "Soltar" else 0
                    resultados_correctas['pregunta_3'] = 1 if st.session_state.get('q3') == "Miércoles" else 0
                    resultados_correctas['pregunta_4'] = 1 if st.session_state.get('q4') == "No" else 0
                    resultados_correctas['pregunta_5'] = 1 if st.session_state.get('q5') == "Participar" else 0
                    resultados_correctas['pregunta_6'] = 1 if st.session_state.get('q6') == "Raro" else 0
                    resultados_correctas['pregunta_7'] = 1 if st.session_state.get('q7') == "C" else 0
                    resultados_correctas['pregunta_8'] = 1 if st.session_state.get('q8') == "1/8" else 0
                    resultados_correctas['pregunta_9'] = 1 if st.session_state.get('q9') == "Similar" else 0
                    resultados_correctas['pregunta_10'] = 1 if st.session_state.get('q10') == "Nariz" else 0
                    resultados_correctas['pregunta_11'] = 1 if st.session_state.get('q11') == "Primavera" else 0
                    resultados_correctas['pregunta_12'] = 1 if st.session_state.get('q12') == "6000" else 0
                    resultados_correctas['pregunta_13'] = 1 if st.session_state.get('q13') == "Verdadero" else 0
                    resultados_correctas['pregunta_14'] = 1 if st.session_state.get('q14') == "Cercano" else 0
                    resultados_correctas['pregunta_15'] = 1 if st.session_state.get('q15') == "60" else 0
                    
                    respuestas_q16_set = {opc for opc in opciones_q16 if st.session_state.get(f"q16_{opc}", False)}
                    correctas_q16_set = {"84721 - 84721", "88884444 - 88884444"}
                    resultados_correctas['pregunta_16'] = 1 if respuestas_q16_set == correctas_q16_set else 0

                    resultados_correctas['pregunta_17'] = 1 if st.session_state.get('q17') == "O" else 0
                    resultados_correctas['pregunta_18'] = 1 if st.session_state.get('q18') == "13" else 0
                    resultados_correctas['pregunta_19'] = 1 if st.session_state.get('q19') == "Ni similar ni contradictorio" else 0
                    resultados_correctas['pregunta_20'] = 1 if st.session_state.get('q20') == "Verdadero" else 0
                    resultados_correctas['pregunta_21'] = 1 if st.session_state.get('q21') == "20" else 0
                    resultados_correctas['pregunta_22'] = 1 if st.session_state.get('q22') == "F" else 0
                    
                    respuestas_q23_set = {opc for opc in opciones_q23 if st.session_state.get(f"q23_{opc}", False)}
                    correctas_q23_set = {"b) Hijo de tigre sale pintado", "e) De tal palo, tal astilla"}
                    resultados_correctas['pregunta_23'] = 1 if respuestas_q23_set == correctas_q23_set else 0

                    resultados_correctas['pregunta_24'] = 1 if st.session_state.get('q24') == "2" else 0
                    resultados_correctas['pregunta_25'] = 1 if st.session_state.get('q25') == "Ni similar ni contradictorio" else 0
                    resultados_correctas['pregunta_26'] = 1 if st.session_state.get('q26') == "Verdadero" else 0
                    resultados_correctas['pregunta_27'] = 1 if st.session_state.get('q27') == "3.33 o 3 1/3" else 0
                    resultados_correctas['pregunta_28'] = 1 if st.session_state.get('q28') == "Contradictorio" else 0
                    resultados_correctas['pregunta_29'] = 1 if st.session_state.get('q29') == "6" else 0
                    resultados_correctas['pregunta_30'] = 1 if st.session_state.get('q30') == "10" else 0
                    resultados_correctas['pregunta_31'] = 1 if st.session_state.get('q31') == "1/9" else 0
                    resultados_correctas['pregunta_32'] = 1 if st.session_state.get('q32') == "Sí" else 0
                    resultados_correctas['pregunta_33'] = 1 if st.session_state.get('q33') == "Ni similar ni contradictorio" else 0
                    resultados_correctas['pregunta_34'] = 1 if st.session_state.get('q34') == "18" else 0
                    resultados_correctas['pregunta_35'] = 1 if st.session_state.get('q35') == "1/4" else 0
                    resultados_correctas['pregunta_36'] = 1 if st.session_state.get('q36') == "72" else 0
                    resultados_correctas['pregunta_37'] = 1 if st.session_state.get('q37') == "0.0625" else 0
                    resultados_correctas['pregunta_38'] = 1 if st.session_state.get('q38') == "6 y 9" else 0
                    resultados_correctas['pregunta_39'] = 1 if st.session_state.get('q39') == "Contradictorios" else 0
                    resultados_correctas['pregunta_40'] = 1 if st.session_state.get('q40') == "3" else 0
                    
                    respuestas_q41_set = {opc for opc in opciones_q41 if st.session_state.get(f"q41_{opc}", False)}
                    correctas_q41_set = {"a) El que está en el lodo querrá meter al otro", "d) Mal de muchos, consuelo de tontos"}
                    resultados_correctas['pregunta_41'] = 1 if respuestas_q41_set == correctas_q41_set else 0

                    resultados_correctas['pregunta_42'] = 1 if st.session_state.get('q42') == "3 y 22" else 0
                    resultados_correctas['pregunta_43'] = 1 if st.session_state.get('q43') == "0.33" else 0
                    resultados_correctas['pregunta_44'] = 1 if st.session_state.get('q44') == "Contradictorios" else 0
                    resultados_correctas['pregunta_45'] = 1 if st.session_state.get('q45') == "\\$24" else 0
                    resultados_correctas['pregunta_46'] = 1 if st.session_state.get('q46') == "Compañera" else 0
                    resultados_correctas['pregunta_47'] = 1 if st.session_state.get('q47') == "Dudoso" else 0
                    resultados_correctas['pregunta_48'] = 1 if st.session_state.get('q48') == "\\$175" else 0
                    
                    respuestas_q49_set = {opc for opc in opciones_q49 if st.session_state.get(f"q49_{opc}", False)}
                    correctas_q49_set = {"A", "B", "D", "E"}
                    resultados_correctas['pregunta_49'] = 1 if respuestas_q49_set == correctas_q49_set else 0
                    
                    resultados_correctas['pregunta_50'] = 1 if st.session_state.get('q50') == "12" else 0
                    
                    puntaje_total, interpretacion = calcular_wonderlic(resultados_correctas, edad_paciente)

                    wonderlic_data_to_save = {
                        "id": st.session_state.ficha_id,
                        "comprende": st.session_state.get("wonderlic_comprende", False),
                        **resultados_correctas,
                        "puntaje_total": puntaje_total,
                        "interpretacion": interpretacion
                    }
                    
                    st.session_state.form_data['test_wonderlic'] = {
                        "comprende": st.session_state.get("wonderlic_comprende", False),
                        "puntaje_total": puntaje_total,
                        "interpretacion": interpretacion
                    }

                    try:
                        response = supabase.from_('test_wonderlic').insert(wonderlic_data_to_save).execute()
                        if response.data:
                            # Limpiar variables
                            for key in ['wonderlic_start_time', 'wonderlic_submitted', 'wonderlic_started', 'wonderlic_comprende']:
                                if key in st.session_state:
                                    del st.session_state[key]
                            
                            st.session_state.current_test_index += 1    
                            st.rerun()
                        else:
                            st.error(f"Error al guardar: {response.error.message if response.error else 'Error desconocido.'}")
                    
                    except Exception as e:
                        st.error(f"Excepción al guardar: {e}")

        # Actualizar el reloj
        elif not st.session_state.wonderlic_submitted:
            time.sleep(719)
            st.rerun()