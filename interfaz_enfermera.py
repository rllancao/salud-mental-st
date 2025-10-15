import streamlit as st
import pandas as pd
from supabase import Client
import pymysql
import json
from datetime import datetime, timedelta
import plotly.graph_objects as go

# --- NUEVO: Lista de tests de salud mental relevantes ---
TESTS_SALUD_MENTAL = [
    "EPWORTH", "DISC", "WONDERLIC", "ALERTA", "BARRATT", 
    "PBLL", "16 PF", "KOSTICK", "PSQI", "D-48", "WESTERN"
]

# --- Conexión a Base de Datos MySQL ---
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

# --- Función para obtener pacientes agendados (MODIFICADA) ---
@st.cache_data(ttl=300)
def fetch_agendados_hoy(sede):
    connection = connect_to_mysql()
    if not connection:
        return []

    sede_busqueda = sede
    if "SANTIAGO" in sede:
        sede_busqueda = "CENTRO DE SALUD WORKMED SANTIAGO"

    query = """
    SELECT datosPersona, prestacionesSalud
    FROM `agendaViewPrest`
    WHERE fecha = CURDATE() 
      AND nombre_lab LIKE %s 
      AND prestacionesSalud IS NOT NULL
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (f"%{sede_busqueda}%",))
            results = cursor.fetchall()
        
        pacientes_agendados = []
        for row in results:
            datos_persona = json.loads(row[0])
            
            # Filtrar las prestaciones para quedarnos solo con las de salud mental
            prestaciones_str = row[1]
            tests_asignados = []
            if prestaciones_str:
                try:
                    lista_prestaciones_raw = json.loads(prestaciones_str)
                    for prestacion in lista_prestaciones_raw:
                        for test_valido in TESTS_SALUD_MENTAL:
                            if test_valido in prestacion.upper():
                                if test_valido not in tests_asignados:
                                    tests_asignados.append(test_valido)
                except (json.JSONDecodeError, TypeError):
                    continue
            
            # Solo agregamos al paciente si tiene al menos un test de salud mental asignado
            if tests_asignados:
                nombre_completo = " ".join(filter(None, [
                    datos_persona.get('nombre', '').strip(),
                    datos_persona.get('nombre2', '').strip(),
                    datos_persona.get('apellidoP', '').strip(),
                    datos_persona.get('apellidoM', '').strip()
                ]))
                pacientes_agendados.append({
                    "rut": datos_persona.get('rut'),
                    "nombre_completo": nombre_completo,
                    "tests_asignados": tests_asignados # Guardamos la lista de tests
                })
        return pacientes_agendados
    except Exception as e:
        st.error(f"Error al buscar los pacientes agendados: {e}")
        return []

# --- NUEVO: Función para obtener el progreso de los tests de varios pacientes ---
@st.cache_data(ttl=60)
def fetch_progreso_tests(_supabase: Client, ruts: list):
    progreso = {rut: [] for rut in ruts}
    if not ruts:
        return progreso

    try:
        fichas_response = _supabase.from_('ficha_ingreso').select('id, rut').in_('rut', ruts).execute()
        if not fichas_response.data:
            return progreso
        
        rut_a_id_map = {item['rut']: item['id'] for item in fichas_response.data}
        id_a_rut_map = {item['id']: item['rut'] for item in fichas_response.data}
        ids = list(rut_a_id_map.values())

        # Consultar Test de Epworth
        epworth_response = _supabase.from_('test_epworth').select('id').in_('id', ids).eq('estado', 'Completado').execute()
        if epworth_response.data:
            for item in epworth_response.data:
                rut = id_a_rut_map.get(item['id'])
                if rut:
                    progreso[rut].append("EPWORTH")
        
        # --- NUEVO: Consultar Test de Wonderlic ---
        # Como Wonderlic no tiene columna 'estado', simplemente verificamos si existe un registro.
        wonderlic_response = _supabase.from_('test_wonderlic').select('id').in_('id', ids).execute()
        if wonderlic_response.data:
            for item in wonderlic_response.data:
                rut = id_a_rut_map.get(item['id'])
                if rut:
                    progreso[rut].append("WONDERLIC")

    except Exception as e:
        st.error(f"Error al verificar el progreso de los tests: {e}")
    
    return progreso

# --- Interfaz principal de la Enfermera (MODIFICADA) ---
def crear_interfaz_enfermera(_supabase: Client):
    sedes_enfermera = st.session_state.get("user_sedes", [])
    if not sedes_enfermera:
        st.error("No tiene sedes asignadas. Por favor, contacte a un administrador.")
        return

    sede_seleccionada = sedes_enfermera[0]
    if len(sedes_enfermera) > 1:
        sede_seleccionada = st.selectbox("Seleccione una sede para visualizar:", options=sedes_enfermera)

    st.title(f"Panel de Enfermera - Sede: {sede_seleccionada}")
    st.markdown("---")

    with st.spinner(f"Actualizando lista de pacientes para {sede_seleccionada}..."):
        pacientes_agendados = fetch_agendados_hoy(sede_seleccionada)
        ruts_de_hoy = [p['rut'] for p in pacientes_agendados]
        progreso_tests = fetch_progreso_tests(_supabase, ruts_de_hoy)

    if not pacientes_agendados:
        st.info("No hay pacientes con prestaciones de salud mental agendados para hoy en esta sede.")
        return

    lista_final_pacientes = []
    stats = {"Finalizado": 0, "En Progreso": 0, "Pendiente": 0}

    for paciente in pacientes_agendados:
        rut = paciente['rut']
        tests_asignados = paciente['tests_asignados']
        tests_completados = progreso_tests.get(rut, [])
        
        num_asignados = len(tests_asignados)
        num_completados = len(tests_completados)

        if num_asignados == 0:
            continue

        if num_completados == num_asignados:
            estado = "✅ Finalizado"
            stats["Finalizado"] += 1
        elif num_completados > 0:
            estado = f"🔵 En Progreso ({num_completados}/{num_asignados})"
            stats["En Progreso"] += 1
        else:
            estado = "🟡 Pendiente"
            stats["Pendiente"] += 1
        
        lista_final_pacientes.append({
            'RUT': rut,
            'Nombre Paciente': paciente['nombre_completo'],
            'Estado Evaluaciones': estado
        })

    total_agendados = len(lista_final_pacientes)
    
    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("Estado de Evaluaciones")
        if total_agendados > 0:
            labels = ['Finalizados', 'En Progreso', 'Pendientes']
            values = [stats['Finalizado'], stats['En Progreso'], stats['Pendiente']]
            colors = ['#2ca02c', '#1f77b4', '#ffdd57']
            fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.4, marker_colors=colors, textinfo='value', hoverinfo='label+percent')])
            fig.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0), height=250)
            config = {'displayModeBar': False}
            st.plotly_chart(fig, use_container_width=True, config=config)

    with col2:
        st.subheader("Resumen del Día")
        st.metric("Total Pacientes (Salud Mental)", total_agendados)
        st.metric("Procesos Finalizados", stats['Finalizado'])
        st.metric("Procesos Pendientes", stats['Pendiente'] + stats['En Progreso'], delta_color="inverse")

    st.markdown("---")
    
    st.write("#### Filtrar Pacientes")
    filter_option = st.radio("Seleccione una vista:", ('Todos', 'Pendientes', 'En Progreso', 'Finalizados'), horizontal=True, label_visibility="collapsed")

    if filter_option == "Pendientes":
        filtered_list = [p for p in lista_final_pacientes if 'Pendiente' in p['Estado Evaluaciones']]
    elif filter_option == "En Progreso":
        filtered_list = [p for p in lista_final_pacientes if 'En Progreso' in p['Estado Evaluaciones']]
    elif filter_option == "Finalizados":
        filtered_list = [p for p in lista_final_pacientes if 'Finalizado' in p['Estado Evaluaciones']]
    else:
        filtered_list = lista_final_pacientes

    if filtered_list:
        df = pd.DataFrame(filtered_list)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No hay pacientes que coincidan con el filtro seleccionado.")

