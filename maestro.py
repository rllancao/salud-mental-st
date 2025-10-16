import streamlit as st
from supabase import create_client, Client, PostgrestAPIResponse, ClientOptions
import ficha_salud_mental
import interfaz_psicologo
import interfaz_enfermera
import test_epworth 
import test_wonderlic
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
            persist_session=True
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

# --- Función para guardar todos los datos al final ---
def guardar_datos_finales(supabase_client):
    ficha_data_original = st.session_state.form_data.get('ficha_ingreso', {})
    if not ficha_data_original:
        st.error("No se encontraron datos de la ficha de ingreso para guardar.")
        return False

    # --- Paso 1: Guardar Ficha de Ingreso ---
    try:
        ficha_data_db = ficha_data_original.copy()
        fecha_vencimiento = ficha_data_db.get("fecha_vencimiento_licencia")
        if isinstance(fecha_vencimiento, date):
            ficha_data_db["fecha_vencimiento_licencia"] = fecha_vencimiento.strftime('%Y-%m-%d')
        else:
            ficha_data_db["fecha_vencimiento_licencia"] = None

        ficha_response = supabase_client.from_('ficha_ingreso').insert(ficha_data_db).execute()
        
        if not ficha_response.data:
            st.error(f"Hubo un error al guardar la ficha de ingreso principal: {ficha_response.error}")
            return False
        
        ficha_id = ficha_response.data[0]['id']
        rut_paciente = ficha_data_original['rut']
        nombre_paciente = ficha_data_original['nombre_completo']
        fecha_actual_str = datetime.now().strftime('%Y-%m-%d')

    except Exception as e:
        st.error(f"Error al guardar los datos en la tabla 'ficha_ingreso': {e}")
        return False

    # --- Paso 2: Generar y Guardar PDF Principal ---
    try:
        wonderlic_data = st.session_state.form_data.get('test_wonderlic')
        pdf_bytes_main = ficha_salud_mental.generar_pdf(ficha_data_original, wonderlic_data=wonderlic_data)
        nombre_archivo_main = f"{rut_paciente}_{fecha_actual_str}_FichaIngreso.pdf"
        file_path_main = f"fichas_ingreso_SM/{nombre_archivo_main}"
        supabase_client.storage.from_("ficha_ingreso_SM_bucket").upload(file=pdf_bytes_main, path=file_path_main, file_options={"content-type": "application/pdf"})
        
        supabase_client.from_('registros_fichas_sm').insert({
            'rut': rut_paciente, 'pdf_path': file_path_main,
            'nombre_completo': nombre_paciente,
        }).execute()
    except Exception as e:
        st.error(f"Error al generar o guardar el PDF de la Ficha de Ingreso: {e}")
        return False

    # --- Paso 3: Guardar Tests ---
    try:
        # Test de Epworth
        epworth_data = st.session_state.form_data.get('test_epworth')
        if epworth_data:
            pdf_bytes_epworth = generador_pdf.generar_pdf_epworth(epworth_data, ficha_data_original)
            nombre_archivo_epworth = f"{rut_paciente}_{fecha_actual_str}_Epworth.pdf"
            file_path_epworth = f"fichas_ingreso_SM/{nombre_archivo_epworth}"
            supabase_client.storage.from_("ficha_ingreso_SM_bucket").upload(file=pdf_bytes_epworth, path=file_path_epworth, file_options={"content-type": "application/pdf"})
            
            epworth_data_db = epworth_data.copy()
            epworth_data_db['id'] = ficha_id
            epworth_data_db['estado'] = 'Completado'
            epworth_data_db['pdf_path'] = file_path_epworth
            supabase_client.from_('test_epworth').insert(epworth_data_db).execute()
        
        # Test de Wonderlic
        wonderlic_data = st.session_state.form_data.get('test_wonderlic')
        if wonderlic_data:
            wonderlic_data_db = wonderlic_data.copy()
            wonderlic_data_db['id'] = ficha_id
            supabase_client.from_('test_wonderlic').insert(wonderlic_data_db).execute()

    except Exception as e:
        st.warning(f"La ficha principal se guardó, pero hubo un error al guardar los datos de los tests: {e}")

    return True


# --- Router para el flujo del paciente (CORREGIDO) ---
def patient_flow_router(supabase_client):
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
            else:
                st.warning(f"El test '{test_actual}' aún no está implementado. Será omitido.")
                if st.button("Continuar"):
                    st.session_state.current_test_index += 1
                    st.rerun()
        else: # Si ya no hay más tests en la lista
            st.session_state.step = "final"
            st.rerun()

    elif current_step == "final":
        st.success("Ha completado todas las evaluaciones agendadas.")
        st.info("Por favor, presione 'Guardar Todo' para finalizar el proceso.")
        if st.button("Guardar Todo", type="primary"):
            with st.spinner("Guardando su información..."):
                if guardar_datos_finales(supabase_client):
                    st.success("¡Información guardada con éxito!")
                    st.balloons()
                    for key in ['step', 'form_data', 'lista_tests', 'current_test_index', 'datos_paciente']:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.info("Puede cerrar esta ventana.")
    
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
    st.image("workmed_logo.png", width='stretch')

# --- Intentar restaurar la sesión al inicio ---
if 'user' not in st.session_state:
    session = supabase.auth.get_session()
    if session and session.user:
        load_user_profile(session.user)
    else:
        st.session_state.user = None

# --- Lógica de Visualización (CORREGIDA para ser mutuamente excluyente) ---
if st.session_state.get('user') is None:
    # Si no hay usuario logueado, SIEMPRE se muestra el flujo del paciente
    st.sidebar.title("Menú Principal")
    with st.sidebar.expander("Acceso para Personal"):
        email = st.text_input("Correo")
        password = st.text_input("Contraseña", type="password")
        
        if st.button("Iniciar Sesión"):
            sign_in(email, password)
    
    # La llamada única al router soluciona el bug de renderizado doble
    patient_flow_router(supabase)

else:
    # Si hay un usuario logueado, se muestra su interfaz específica
    st.sidebar.title("Menú Principal")
    st.sidebar.write(f"Conectado como: {st.session_state.user.email}")
    st.sidebar.write(f"Rol: {st.session_state.user_role}")
    if st.session_state.get("user_sedes"):
        st.sidebar.write("Sedes Asignadas:")
        for sede in st.session_state.user_sedes:
            st.sidebar.markdown(f"- {sede}")
    
    if st.sidebar.button("Cerrar Sesión"):
        sign_out()
    
    # Se llama a la interfaz correspondiente al rol, o al router si es paciente
    if st.session_state.user_role == "paciente":
        patient_flow_router(supabase)
    elif st.session_state.user_role == "psicologo":
        interfaz_psicologo.crear_interfaz_psicologo(supabase)
    elif st.session_state.user_role == "enfermera":
        interfaz_enfermera.crear_interfaz_enfermera(supabase)
    else:
        st.error("Rol de usuario no reconocido. Contacte a un administrador.")

