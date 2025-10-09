import streamlit as st
import pandas as pd
from supabase import Client
import pymysql
import json
from datetime import datetime, timedelta
import plotly.graph_objects as go

# --- Conexión a Base de Datos MySQL (Necesaria para buscar agendados) ---
@st.cache_resource
def connect_to_mysql():
    try:
        connection = pymysql.connect(
            host=st.secrets["mysql"]["host"],
            user=st.secrets["mysql"]["user"],
            password=st.secrets["mysql"]["password"],
            database=st.secrets["mysql"]["database"],
            port=st.secrets["mysql"]["port"]
        )
        return connection
    except Exception as e:
        st.error(f"No se pudo conectar a la base de datos de WorkmedFlow: {e}")
        return None

# --- Función para obtener pacientes agendados para hoy en una sede ---
@st.cache_data(ttl=300) # Cache de 5 minutos para no sobrecargar la BD
def fetch_agendados_hoy(sede):
    connection = connect_to_mysql()
    if not connection:
        return []

    # Lógica para agrupar sedes de Santiago
    sede_busqueda = sede
    if "SANTIAGO" in sede:
        sede_busqueda = "CENTRO DE SALUD WORKMED SANTIAGO"

    query = """
    SELECT datosPersona
    FROM `agendaview`
    WHERE fecha = CURDATE() AND nombre_lab LIKE %s
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (f"%{sede_busqueda}%",))
            results = cursor.fetchall()
        
        pacientes_agendados = []
        for row in results:
            datos_persona = json.loads(row[0])
            nombre_completo = " ".join(filter(None, [
                datos_persona.get('nombre', '').strip(),
                datos_persona.get('nombre2', '').strip(),
                datos_persona.get('apellidoP', '').strip(),
                datos_persona.get('apellidoM', '').strip()
            ]))
            pacientes_agendados.append({
                "rut": datos_persona.get('rut'),
                "nombre_completo": nombre_completo
            })
        return pacientes_agendados
    except Exception as e:
        st.error(f"Error al buscar los pacientes agendados: {e}")
        return []

# --- Función para obtener RUTs de fichas completadas hoy en una sede ---
@st.cache_data(ttl=60) # Cache de 1 minuto
def fetch_completados_hoy(_supabase: Client, sede):
    try:
        today = datetime.now()
        start_of_today = today.strftime('%Y-%m-%d 00:00:00')
        tomorrow = today + timedelta(days=1)
        start_of_tomorrow = tomorrow.strftime('%Y-%m-%d 00:00:00')
        
        # Lógica para agrupar sedes de Santiago
        sede_busqueda = sede
        if "SANTIAGO" in sede:
            sede_busqueda = "CENTRO DE SALUD WORKMED SANTIAGO"

        response = _supabase.from_('ficha_ingreso').select('rut').like('sucursal_workmed', f'%{sede_busqueda}%').gte('created_at', start_of_today).lt('created_at', start_of_tomorrow).execute()
        
        if response.data:
            return {item['rut'] for item in response.data}
        return set()
    except Exception as e:
        st.error(f"Error al buscar las fichas completadas: {e}")
        return set()


# --- Interfaz principal de la Enfermera ---
def crear_interfaz_enfermera(_supabase: Client):
    # --- CAMBIO CLAVE: Obtener la lista de sedes del usuario ---
    sedes_enfermera = st.session_state.get("user_sedes", [])

    if not sedes_enfermera:
        st.error("No tiene sedes asignadas. Por favor, contacte a un administrador.")
        return

    # --- CAMBIO CLAVE: Mostrar un selector si hay más de una sede ---
    if len(sedes_enfermera) > 1:
        sede_seleccionada = st.selectbox("Seleccione una sede para visualizar:", options=sedes_enfermera)
    else:
        sede_seleccionada = sedes_enfermera[0]

    st.title(f"Panel de Enfermera - Sede: {sede_seleccionada}")
    st.markdown("---")

    with st.spinner(f"Actualizando lista de pacientes para {sede_seleccionada}..."):
        pacientes_agendados = fetch_agendados_hoy(sede_seleccionada)
        ruts_completados = fetch_completados_hoy(_supabase, sede_seleccionada)

    if not pacientes_agendados:
        st.info("No hay pacientes agendados para el día de hoy en esta sede.")
        return

    lista_final_pacientes = []
    for paciente in pacientes_agendados:
        estado = "🟢 Completado" if paciente['rut'] in ruts_completados else "🟡 Pendiente"
        lista_final_pacientes.append({
            'RUT': paciente['rut'],
            'Nombre Paciente': paciente['nombre_completo'],
            'Estado Ficha Ingreso': estado
        })

    total_agendados = len(pacientes_agendados)
    total_completados = len(ruts_completados)
    total_pendientes = total_agendados - total_completados
    
    # --- UI con Gráfico y Resumen ---
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Estado de Fichas de Ingreso")
        if total_agendados > 0:
            labels = ['Completados', 'Pendientes']
            values = [total_completados, total_pendientes]
            colors = ['#2ca02c', '#ffdd57']
            
            fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.4,
                                        marker_colors=colors, textinfo='value', hoverinfo='label+percent')])
            fig.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0), height=250)
            
            config = {'displayModeBar': False}
            st.plotly_chart(fig, width='stretch', config=config)
        else:
            st.info("No hay datos para mostrar en el gráfico.")

    with col2:
        st.subheader("Resumen del Día")
        st.metric("Total Agendados", total_agendados)
        st.metric("Fichas Completadas", total_completados)
        st.metric("Fichas Pendientes", total_pendientes, delta_color="inverse")

    st.markdown("---")
    
    # --- Filtros Interactivos ---
    st.write("#### Filtrar Pacientes")
    filter_option = st.radio(
        "Seleccione una vista:",
        ('Todos', 'Pendientes', 'Completados'),
        horizontal=True,
        label_visibility="collapsed"
    )

    # --- Tabla Filtrada ---
    if filter_option == "Pendientes":
        filtered_list = [p for p in lista_final_pacientes if p['Estado Ficha Ingreso'] == "🟡 Pendiente"]
    elif filter_option == "Completados":
        filtered_list = [p for p in lista_final_pacientes if p['Estado Ficha Ingreso'] == "🟢 Completado"]
    else: # "Todos"
        filtered_list = lista_final_pacientes

    if filtered_list:
        df = pd.DataFrame(filtered_list)
        st.dataframe(df, width='stretch')
    else:
        st.info("No hay pacientes que coincidan con el filtro seleccionado.")

