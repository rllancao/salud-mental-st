import streamlit as st
from supabase import create_client, Client, PostgrestAPIResponse, ClientOptions
import ficha_salud_mental
import interfaz_psicologo
import interfaz_enfermera

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
            # --- CAMBIO CLAVE: 'sede' ahora es una lista, la guardamos como 'user_sedes' ---
            st.session_state.user_sedes = profile.get("sede", []) # Guardamos como lista
            return True
        else:
            st.session_state.user = user
            st.session_state.user_role = "paciente"
            st.session_state.user_sedes = [] # El paciente no tiene sedes
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

# --- Lógica principal de la aplicación ---
st.set_page_config(
    page_title="Gestión de Salud Mental",
    layout="wide",
    initial_sidebar_state="collapsed" 
)

col1, col2, col3 = st.columns([2, 3, 2])
with col2:
    st.image("workmed_logo.png", width='stretch')

st.sidebar.title("Menú Principal")

# --- Intentar restaurar la sesión al inicio ---
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
    ficha_salud_mental.crear_interfaz_paciente(supabase)

else:
    st.sidebar.write(f"Conectado como: {st.session_state.user.email}")
    st.sidebar.write(f"Rol: {st.session_state.user_role}")
    
    # --- CAMBIO CLAVE: Mostrar la lista de sedes asignadas ---
    if st.session_state.get("user_sedes"):
        st.sidebar.write("Sedes Asignadas:")
        for sede in st.session_state.user_sedes:
            st.sidebar.markdown(f"- {sede}")
    
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

