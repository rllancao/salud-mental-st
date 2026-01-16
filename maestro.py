import streamlit as st
import streamlit.components.v1 as components  # Importar componentes para JS
from supabase import create_client, Client, PostgrestAPIResponse, ClientOptions
import ficha_salud_mental
import interfaz_psicologo
import interfaz_enfermera
import interfaz_contraloria
import test_epworth 
import test_epq_r
import test_pbll
import test_wonderlic
import test_disc
import test_alerta
import test_barratt
import test_kostick
import test_psqi
import test_western
import test_d48
import test_16pf
import generador_pdf
from datetime import datetime, date

# para correr el codigo: python -m streamlit run maestro.py 

# --- Configuración de Supabase ---
@st.cache_resource
def init_supabase():
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(
        url,
        key,
        options=ClientOptions(
            persist_session=False
        )
    )

supabase: Client = init_supabase()

# --- Función para cargar el perfil del usuario ---
def load_user_profile(user):
    try:
        response: PostgrestAPIResponse = supabase.from_("perfiles").select("rol, sede").eq("id", user.id).limit(1).execute()
        if response.data:
            profile = response.data[0]
            st.session_state.user = user
            st.session_state.user_role = profile.get("rol")
            st.session_state.user_sedes = profile.get("sede", [])
            return True
        else:
            st.session_state.user = user
            st.session_state.user_role = "paciente"
            st.session_state.user_sedes = []
            return True
    except Exception as e:
        st.error(f"Error al cargar el perfil del usuario: {e}")
        return False

# --- Funciones de autenticación ---
def sign_in(email, password):
    try:
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if response.user:
            if load_user_profile(response.user):
                st.success("¡Inicio de sesión exitoso!")
                st.rerun()
    except Exception as e:
        st.error(f"Error al iniciar sesión: {e}")

def sign_out():
    supabase.auth.sign_out()
    for key in st.session_state.keys():
        del st.session_state[key]
    st.rerun()

# --- Función para reanudar sesión del paciente ---
def resume_session(supabase_client, ficha_id):
    try:
        ficha_response = supabase_client.from_('ficha_ingreso').select('rut').eq('id', ficha_id).single().execute()
        if not ficha_response.data:
            st.warning("No se pudo reanudar la sesión (ID no válido).")
            st.query_params.clear()
            return False

        st.session_state.ficha_id = ficha_id
        rut = ficha_response.data['rut']
        
        mysql_response = ficha_salud_mental.fetch_patient_data(supabase_client, rut)
        if not mysql_response or mysql_response == "not_found":
            st.warning("No se pudo reanudar la sesión. Datos del paciente no encontrados.")
            st.query_params.clear()
            return False

        st.session_state.datos_paciente = mysql_response.get("data", {})
        st.session_state.lista_tests = mysql_response.get("tests", [])
        
        current_index = 0
        for test_name in st.session_state.lista_tests:
            is_done = False
            tabla_test = {"EPWORTH": "test_epworth", "WONDERLIC": "test_wonderlic", "DISC": "test_disc", "EPQ-R": "test_epq_r",
                          "PBLL": "test_pbll", "ALERTA": "test_alerta", "BARRATT": "test_barratt", "KOSTICK": "test_kostick",
                          "PSQI": "test_psqi", "WESTERN": "test_western", "D-48": "test_d48", "16 PF": "test_16pf"}.get(test_name)
            
            if tabla_test:
                res = supabase_client.from_(tabla_test).select('id', count='exact').eq('id', ficha_id).execute()
                if res.count > 0:
                    is_done = True
            
            if is_done:
                current_index += 1
            else:
                break
        
        st.session_state.current_test_index = current_index
        st.session_state.step = "test"
        st.success("Sesión reanudada.")
        return True

    except Exception as e:
        st.error(f"Error al reanudar la sesión: {e}")
        st.query_params.clear()
        return False

# --- Función para guardar los PDFs al final ---
def guardar_datos_finales(supabase_client):
    if 'ficha_id' not in st.session_state:
        st.error("No se encontró un ID de sesión para generar los informes.")
        return False

    ficha_id = st.session_state.ficha_id
    
    try:
        ficha_response = supabase_client.from_('ficha_ingreso').select('*').eq('id', ficha_id).single().execute()
        if not ficha_response.data:
            st.error("No se encontraron los datos de la ficha de ingreso para generar el PDF.")
            return False
        ficha_data_original = ficha_response.data
        rut_paciente = ficha_data_original['rut']
        nombre_paciente = ficha_data_original['nombre_completo']
        
        # Fecha y hora para evitar duplicidad de nombres
        fecha_hora_actual_str = datetime.now().strftime('%Y-%m-%d_%H%M')

        # --- CORRECCIÓN: Se elimina .single() y se comprueba si hay datos ---
        wonderlic_response = supabase_client.from_('test_wonderlic').select('*').eq('id', ficha_id).execute()
        wonderlic_data = wonderlic_response.data[0] if wonderlic_response.data else None

        disc_response = supabase_client.from_('test_disc').select('*').eq('id', ficha_id).execute()
        disc_data = None
        if disc_response.data:
            disc_data_raw = {k: v for k, v in disc_response.data[0].items() if k.startswith('grupo_')}
            disc_data = test_disc.evaluate_disc(disc_data_raw)

        epworth_response = supabase_client.from_('test_epworth').select('*').eq('id', ficha_id).execute()
        epworth_data = epworth_response.data[0] if epworth_response.data else None
        
        epq_r_response = supabase_client.from_('test_epq_r').select('*').eq('id', ficha_id).execute()
        epq_r_data = epq_r_response.data[0] if epq_r_response.data else None
        
        pbll_response = supabase_client.from_('test_pbll').select('*').eq('id', ficha_id).execute()
        pbll_data = pbll_response.data[0] if pbll_response.data else None
        
        alerta_response = supabase_client.from_('test_alerta').select('*').eq('id', ficha_id).execute()
        alerta_data = alerta_response.data[0] if alerta_response.data else None
        
        barratt_response = supabase_client.from_('test_barratt').select('*').eq('id', ficha_id).execute()
        barratt_data = barratt_response.data[0] if barratt_response.data else None

        kostick_response = supabase_client.from_('test_kostick').select('*').eq('id', ficha_id).execute()
        kostick_data = kostick_response.data[0] if kostick_response.data else None
        
        psqi_response = supabase_client.from_('test_psqi').select('*').eq('id', ficha_id).execute()
        psqi_data = psqi_response.data[0] if psqi_response.data else None
        
        western_response = supabase_client.from_('test_western').select('*').eq('id', ficha_id).execute()
        western_data = western_response.data[0] if western_response.data else None

        d48_response = supabase_client.from_('test_d48').select('*').eq('id', ficha_id).execute()
        d48_data = d48_response.data[0] if d48_response.data else None
        
        _16pf_response = supabase_client.from_('test_16pf').select('*').eq('id', ficha_id).execute()
        _16pf_data = _16pf_response.data[0] if _16pf_response.data else None

        pdf_bytes_main = ficha_salud_mental.generar_pdf(supabase_client,ficha_data_original, wonderlic_data=wonderlic_data, disc_data=disc_data,
                                                        pbll_data=pbll_data, alerta_data=alerta_data, barratt_data=barratt_data, kostick_data=kostick_data,
                                                        psqi_data=psqi_data, western_data=western_data, d48_data=d48_data, _16pf_data=_16pf_data)
        
        nombre_archivo_main = f"{rut_paciente}_{fecha_hora_actual_str}_FichaIngreso.pdf"
        file_path_main = f"fichas_ingreso_SM/{nombre_archivo_main}"
        supabase_client.storage.from_("ficha_ingreso_SM_bucket").upload(file=pdf_bytes_main, path=file_path_main, file_options={"content-type": "application/pdf"})
        supabase_client.from_('registros_fichas_sm').insert({'rut': rut_paciente, 'pdf_path': file_path_main, 'nombre_completo': nombre_paciente}).execute()

        if epworth_data:
            pdf_bytes_epworth = generador_pdf.generar_pdf_epworth(epworth_data, ficha_data_original)
            nombre_archivo_epworth = f"{rut_paciente}_{fecha_hora_actual_str}_Epworth.pdf"
            file_path_epworth = f"fichas_ingreso_SM/{nombre_archivo_epworth}"
            supabase_client.storage.from_("ficha_ingreso_SM_bucket").upload(file=pdf_bytes_epworth, path=file_path_epworth, file_options={"content-type": "application/pdf"})
            supabase_client.from_('test_epworth').update({'pdf_path': file_path_epworth}).eq('id', ficha_id).execute()

        if epq_r_data:
            pdf_bytes_epq_r = generador_pdf.generar_pdf_epq_r(epq_r_data, ficha_data_original)
            nombre_archivo_epq_r = f"{rut_paciente}_{fecha_hora_actual_str}_EPQR.pdf"
            file_path_epq_r = f"fichas_ingreso_SM/{nombre_archivo_epq_r}"
            supabase_client.storage.from_("ficha_ingreso_SM_bucket").upload(file=pdf_bytes_epq_r, path=file_path_epq_r, file_options={"content-type": "application/pdf"})
            supabase_client.from_('test_epq_r').update({'pdf_path': file_path_epq_r}).eq('id', ficha_id).execute()

    except Exception as e:
        st.error(f"Error al generar o guardar los informes PDF: {e}")
        return False

    return True

# --- Router para el flujo del paciente ---
def patient_flow_router(supabase_client):
    if 'ficha_id' not in st.session_state and "ficha_id" in st.query_params:
        if resume_session(supabase_client, st.query_params["ficha_id"]):
            st.rerun()

    current_step = st.session_state.get("step", "ficha")

    if current_step == "test":
        current_index = st.session_state.get("current_test_index", 0)
        lista_tests = st.session_state.get("lista_tests", [])

        if current_index < len(lista_tests):
            # --- MOSTRAR TEST ACTUAL ---
            test_actual = lista_tests[current_index]
            
            # --- SCROLL TO TOP (FIXED) ---
            # Usamos f-string para cambiar el contenido del script en cada paso.
            # Esto fuerza a Streamlit a re-ejecutar el componente sin usar el parámetro 'key' que causaba error.
            components.html(
                f"""
                <script>
                    // Test Index: {current_index} (Fuerza actualización)
                    var topElement = window.parent.document.getElementById('inicio_pagina');
                    if (topElement) {{
                        topElement.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
                    }} else {{
                        var main = window.parent.document.querySelector('section.main');
                        if (main) main.scrollTo(0, 0);
                    }}
                </script>
                """,
                height=0
            )

            # Mostrar mensaje amigable de progreso
            st.progress((current_index) / len(lista_tests), text=f"Progreso: Test {current_index + 1} de {len(lista_tests)}")
            
            sexo_paciente = st.session_state.get("datos_paciente", {}).get("sexo", None)
            
            if "EPWORTH" == test_actual:
                test_epworth.crear_interfaz_epworth(supabase_client)
            elif "WONDERLIC" == test_actual:
                test_wonderlic.crear_interfaz_wonderlic(supabase_client)
            elif "DISC" == test_actual:
                test_disc.crear_interfaz_disc(supabase_client)
            elif "ALERTA" == test_actual:
                test_alerta.crear_interfaz_alerta(supabase_client)
            elif "EPQ-R" == test_actual:
                test_epq_r.crear_interfaz_epq_r(supabase_client, sexo_paciente)
            elif "PBLL" == test_actual:
                test_pbll.crear_interfaz_pbll(supabase_client)
            elif "BARRATT" == test_actual:
                test_barratt.crear_interfaz_barratt(supabase_client)
            elif "KOSTICK" == test_actual:
                test_kostick.crear_interfaz_kostick(supabase_client)
            elif "PSQI" == test_actual:
                test_psqi.crear_interfaz_psqi(supabase_client)
            elif "WESTERN" == test_actual:
                test_western.crear_interfaz_western(supabase_client)
            elif "D-48" == test_actual:
                test_d48.crear_interfaz_d48(supabase_client)
            elif "16 PF" == test_actual:
                test_16pf.crear_interfaz_16pf(supabase_client, sexo_paciente)
            else:
                st.warning(f"El test '{test_actual}' aún no está implementado.")
                if st.button("Continuar"):
                    st.session_state.current_test_index += 1
                    st.rerun()
        else:
            # --- TODOS LOS TESTS COMPLETADOS ---
            st.session_state.step = "final"
            st.rerun()

    elif current_step == "final":
        # --- PANTALLA DE FINALIZACIÓN AUTOMÁTICA ---
        
        # SCROLL TO TOP PARA EL FINAL
        components.html(
            """
            <script>
                // Final Step Scroll
                var topElement = window.parent.document.getElementById('inicio_pagina');
                if (topElement) {
                    topElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            </script>
            """,
            height=0
        )

        st.title("Proceso Finalizado") 
        
        with st.spinner("Generando sus informes finales, por favor espere un momento..."):
            if guardar_datos_finales(supabase_client):
                st.success("¡Felicitaciones! Ha completado todas las evaluaciones. Sus datos han sido guardados correctamente.")
                st.balloons()
                
                if "ficha_id" in st.query_params: st.query_params.clear()
                for key in ['step', 'form_data', 'lista_tests', 'current_test_index', 'datos_paciente', 'ficha_id']:
                    if key in st.session_state: del st.session_state[key]
                
                st.info("Puede cerrar esta ventana o notificar al profesional a cargo.")
                
                col_izq, col_centro, col_der = st.columns([1, 2, 1])
                with col_centro:
                    if st.button("Volver al Inicio", use_container_width=True, type="primary"): 
                        st.rerun()
            else:
                st.error("Hubo un problema al generar los informes finales. Por favor, avise al personal a cargo.")
    
    else: # current_step == "ficha"
        ficha_salud_mental.crear_interfaz_paciente(supabase_client)

# --- Lógica principal de la aplicación ---
st.set_page_config(page_title="Gestión de Salud Mental", layout="wide", initial_sidebar_state="collapsed" )

# --- ANCLAJE PARA SCROLL ---
st.markdown("<div id='inicio_pagina'></div>", unsafe_allow_html=True)

col1, col2, col3 = st.columns([2, 3, 2])
with col2:
    st.image("workmed_logo.png")

if st.session_state.get('user') is None:
    with st.sidebar.expander("Acceso para Personal"):
        email = st.text_input("Correo")
        password = st.text_input("Contraseña", type="password")
        if st.button("Iniciar Sesión"):
            sign_in(email, password)
    patient_flow_router(supabase)
else:
    st.sidebar.title("Menú Principal")
    st.sidebar.write(f"Conectado como: {st.session_state.user.email}")
    st.sidebar.write(f"Rol: {st.session_state.user_role}")
    if st.session_state.get("user_sedes"):
        st.sidebar.write("Sedes Asignadas:")
        for sede in st.session_state.user_sedes:
            st.sidebar.markdown(f"- {sede}")
    
    if st.sidebar.button("Cerrar Sesión"):
        sign_out()
    
    if st.session_state.user_role == "psicologo":
        interfaz_psicologo.crear_interfaz_psicologo(supabase)
    elif st.session_state.user_role == "enfermera":
        interfaz_enfermera.crear_interfaz_enfermera(supabase)
    elif st.session_state.user_role == "contraloria":
        interfaz_contraloria.crear_interfaz_contraloria(supabase)
    else:
        st.error("Rol de usuario no reconocido.")