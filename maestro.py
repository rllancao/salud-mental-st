import streamlit as st
from supabase import create_client, Client, PostgrestAPIResponse, ClientOptions
import ficha_salud_mental
import interfaz_psicologo
import interfaz_enfermera

# --- Configuración de Supabase ---
@st.cache_resource
def init_supabase():
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    # --- CAMBIO CLAVE: Usar el objeto ClientOptions ---
    # Esto se alinea con las versiones recientes de la librería supabase-py.
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
            st.session_state.user_sede = profile.get("sede")
            return True
        else:
            # Si el usuario existe en Supabase Auth pero no tiene perfil
            st.session_state.user = user
            st.session_state.user_role = "paciente" # Asignar rol por defecto
            st.session_state.user_sede = None
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
    # Limpiar todo el estado de la sesión para un cierre limpio
    for key in st.session_state.keys():
        del st.session_state[key]
    st.rerun()

# --- Lógica principal de la aplicación ---
st.set_page_config(page_title="Gestión de Salud Mental", layout="wide")
st.sidebar.title("Menú Principal")

# --- CAMBIO CLAVE: Intentar restaurar la sesión al inicio ---
# Esto se ejecuta cada vez que la página se carga o refresca.
if 'user' not in st.session_state:
    session = supabase.auth.get_session()
    if session and session.user:
        load_user_profile(session.user)
    else:
        st.session_state.user = None


# Lógica de visualización basada en si el usuario está en la sesión
if st.session_state.get('user') is None:
    st.sidebar.markdown("---")
    st.sidebar.subheader("Iniciar Sesión")
    email = st.sidebar.text_input("Correo")
    password = st.sidebar.text_input("Contraseña", type="password")
    
    if st.sidebar.button("Iniciar Sesión"):
        sign_in(email, password)
    
    st.sidebar.markdown("---")
    st.sidebar.info("Solo tiene acceso a la Ficha de Ingreso. Inicie sesión para ver las otras secciones.")
    ficha_salud_mental.crear_interfaz_paciente(supabase)

else:
    # Si el usuario está autenticado, mostrar la interfaz correspondiente
    st.sidebar.write(f"Conectado como: {st.session_state.user.email}")
    st.sidebar.write(f"Rol: {st.session_state.user_role}")
    if st.session_state.get("user_sede"):
        st.sidebar.write(f"Sede: {st.session_state.user_sede}")
    
    if st.sidebar.button("Cerrar Sesión"):
        sign_out()
    
    if st.session_state.user_role == "paciente":
        ficha_salud_mental.crear_interfaz_paciente(supabase)
    elif st.session_state.user_role == "psicologo":
        interfaz_psicologo.crear_interfaz_psicologo(supabase)
    elif st.session_state.user_role == "enfermera":
        interfaz_enfermera.crear_interfaz_enfermera(supabase)
    else:
        st.error("Rol de usuario no reconocido. Contacte a un administrador.")

