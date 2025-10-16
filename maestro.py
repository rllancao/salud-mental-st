import streamlit as st
from supabase import create_client, Client, PostgrestAPIResponse, ClientOptions
import ficha_salud_mental
import interfaz_psicologo
import interfaz_enfermera
import test_epworth 
import test_wonderlic
import test_disc
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
        # --- CORRECCIÓN DE SEGURIDAD: Se deshabilita la persistencia de sesión del lado del servidor ---
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
            # Si no hay perfil, se asigna el rol de paciente por defecto
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
    # Limpia todo el session_state al cerrar sesión para seguridad
    for key in st.session_state.keys():
        del st.session_state[key]
    st.rerun()

# --- Función para reanudar sesión del paciente ---
def resume_session(supabase_client, ficha_id):
    """Repopula el estado de la sesión desde Supabase usando un ficha_id."""
    try:
        ficha_response = supabase_client.from_('ficha_ingreso').select('rut').eq('id', ficha_id).single().execute()
        if not ficha_response.data:
            st.warning("No se pudo reanudar la sesión (ID no válido). Por favor, comience de nuevo.")
            st.query_params.clear()
            return False

        st.session_state.ficha_id = ficha_id
        rut = ficha_response.data['rut']
        
        mysql_response = ficha_salud_mental.fetch_patient_data(rut)
        if not mysql_response or mysql_response == "not_found":
            st.warning("No se pudo reanudar la sesión. Datos originales del paciente no encontrados.")
            st.query_params.clear()
            return False

        st.session_state.datos_paciente = mysql_response.get("data", {})
        st.session_state.lista_tests = mysql_response.get("tests", [])
        
        current_index = 0
        for test_name in st.session_state.lista_tests:
            is_done = False
            tabla_test = ""
            if test_name == "EPWORTH": tabla_test = "test_epworth"
            elif test_name == "WONDERLIC": tabla_test = "test_wonderlic"
            elif test_name == "DISC": tabla_test = "test_disc"
            
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
        fecha_actual_str = datetime.now().strftime('%Y-%m-%d')

        wonderlic_response = supabase_client.from_('test_wonderlic').select('*').eq('id', ficha_id).single().execute()
        wonderlic_data = wonderlic_response.data if wonderlic_response.data else None

        disc_response = supabase_client.from_('test_disc').select('*').eq('id', ficha_id).single().execute()
        disc_data = None
        if disc_response.data:
            disc_data_raw = {k: v for k, v in disc_response.data.items() if k.startswith('grupo_')}
            disc_data = test_disc.evaluate_disc(disc_data_raw)

        epworth_response = supabase_client.from_('test_epworth').select('*').eq('id', ficha_id).single().execute()
        epworth_data = epworth_response.data if epworth_response.data else None
            
        pdf_bytes_main = ficha_salud_mental.generar_pdf(ficha_data_original, wonderlic_data=wonderlic_data, disc_data=disc_data)
        nombre_archivo_main = f"{rut_paciente}_{fecha_actual_str}_FichaIngreso.pdf"
        file_path_main = f"fichas_ingreso_SM/{nombre_archivo_main}"
        supabase_client.storage.from_("ficha_ingreso_SM_bucket").upload(file=pdf_bytes_main, path=file_path_main, file_options={"content-type": "application/pdf"})
        supabase_client.from_('registros_fichas_sm').insert({'rut': rut_paciente, 'pdf_path': file_path_main, 'nombre_completo': nombre_paciente}).execute()

        if epworth_data:
            pdf_bytes_epworth = generador_pdf.generar_pdf_epworth(epworth_data, ficha_data_original)
            nombre_archivo_epworth = f"{rut_paciente}_{fecha_actual_str}_Epworth.pdf"
            file_path_epworth = f"fichas_ingreso_SM/{nombre_archivo_epworth}"
            supabase_client.storage.from_("ficha_ingreso_SM_bucket").upload(file=pdf_bytes_epworth, path=file_path_epworth, file_options={"content-type": "application/pdf"})
            supabase_client.from_('test_epworth').update({'pdf_path': file_path_epworth}).eq('id', ficha_id).execute()

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
            test_actual = lista_tests[current_index]
            
            if "EPWORTH" == test_actual:
                test_epworth.crear_interfaz_epworth(supabase_client)
            elif "WONDERLIC" == test_actual:
                test_wonderlic.crear_interfaz_wonderlic(supabase_client)
            elif "DISC" == test_actual:
                test_disc.crear_interfaz_disc(supabase_client)
            else:
                st.warning(f"El test '{test_actual}' aún no está implementado. Será omitido.")
                if st.button("Continuar"):
                    st.session_state.current_test_index += 1
                    st.rerun()
        else:
            st.session_state.step = "final"
            st.rerun()

    elif current_step == "final":
        st.success("Ha completado todas las evaluaciones agendadas.")
        st.info("Por favor, presione 'Finalizar Proceso' para generar sus informes.")
        if st.button("Finalizar Proceso", type="primary"):
            with st.spinner("Generando informes..."):
                if guardar_datos_finales(supabase_client):
                    st.success("¡Proceso finalizado con éxito!")
                    st.balloons()
                    if "ficha_id" in st.query_params: st.query_params.clear()
                    for key in ['step', 'form_data', 'lista_tests', 'current_test_index', 'datos_paciente', 'ficha_id']:
                        if key in st.session_state: del st.session_state[key]
                    st.info("Puede cerrar esta ventana o comenzar una nueva evaluación.")
                    if st.button("Comenzar Nueva Evaluación"): st.rerun()
    
    else: # current_step == "ficha"
        ficha_salud_mental.crear_interfaz_paciente(supabase_client)

# --- Lógica principal de la aplicación ---
st.set_page_config(
    page_title="Gestión de Salud Mental",
    layout="wide",
    initial_sidebar_state="collapsed" 
)

col1, col2, col3 = st.columns([2, 3, 2])
with col2:
    st.image("workmed_logo.png")

# --- Lógica de Visualización ---
# La sesión de usuario autenticado ahora solo depende de st.session_state
if st.session_state.get('user') is None:
    # Flujo del paciente (no autenticado)
    with st.sidebar.expander("Acceso para Personal"):
        email = st.text_input("Correo")
        password = st.text_input("Contraseña", type="password")
        if st.button("Iniciar Sesión"):
            sign_in(email, password)
    
    patient_flow_router(supabase)

else:
    # Flujo de personal (autenticado)
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
    else:
        st.error("Rol de usuario no reconocido. Contacte a un administrador.")

