import streamlit as st
import pandas as pd
from supabase import Client
import pymysql
import json
from datetime import datetime, timedelta
import plotly.graph_objects as go

# --- Mantenemos la lista de todos los tests posibles para usar como columnas ---
TESTS_SALUD_MENTAL = [
    "EPWORTH", "DISC", "WONDERLIC", "ALERTA", "BARRATT", 
    "PBLL", "16 PF", "KOSTICK", "PSQI", "D-48", "WESTERN"
]

# --- Conexión a Base de Datos MySQL (sin cambios) ---
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

# --- Función para obtener pacientes agendados (sin cambios) ---
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
                    "tests_asignados": tests_asignados
                })
        return pacientes_agendados
    except Exception as e:
        st.error(f"Error al buscar los pacientes agendados: {e}")
        return []

# --- Función para obtener RUTs de pacientes que ya iniciaron (sin cambios) ---
@st.cache_data(ttl=60)
def fetch_iniciados_hoy(_supabase: Client, sede):
    try:
        today = datetime.now()
        start_of_today = today.strftime('%Y-%m-%d 00:00:00')
        tomorrow = today + timedelta(days=1)
        start_of_tomorrow = tomorrow.strftime('%Y-%m-%d 00:00:00')

        sede_busqueda = sede
        if "SANTIAGO" in sede:
            sede_busqueda = "CENTRO DE SALUD WORKMED SANTIAGO"

        response = _supabase.from_('ficha_ingreso').select('rut').like('sucursal_workmed', f'%{sede_busqueda}%').gte('created_at', start_of_today).lt('created_at', start_of_tomorrow).execute()

        if response.data:
            return {item['rut'] for item in response.data}
        return set()
    except Exception as e:
        st.error(f"Error al buscar las fichas iniciadas: {e}")
        return set()

# --- Función para obtener el progreso de los tests (sin cambios) ---
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

        if not ids: return progreso

        # Consultar tests completados
        epworth_response = _supabase.from_('test_epworth').select('id').in_('id', ids).eq('estado', 'Completado').execute()
        if epworth_response.data:
            for item in epworth_response.data:
                rut = id_a_rut_map.get(item['id'])
                if rut:
                    progreso[rut].append("EPWORTH")
        
        wonderlic_response = _supabase.from_('test_wonderlic').select('id').in_('id', ids).execute()
        if wonderlic_response.data:
            for item in wonderlic_response.data:
                rut = id_a_rut_map.get(item['id'])
                if rut:
                    progreso[rut].append("WONDERLIC")
        
        disc_response = _supabase.from_('test_disc').select('id').in_('id', ids).execute()
        if disc_response.data:
            for item in disc_response.data:
                rut = id_a_rut_map.get(item['id'])
                if rut:
                    progreso[rut].append("DISC")

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
        ruts_iniciados = fetch_iniciados_hoy(_supabase, sede_seleccionada)
        progreso_tests = fetch_progreso_tests(_supabase, [p['rut'] for p in pacientes_agendados])

    if not pacientes_agendados:
        st.info("No hay pacientes con prestaciones de salud mental agendados para hoy en esta sede.")
        return
    
    # --- LÓGICA DE CONSTRUCCIÓN DE LA TABLA Y ESTADÍSTICAS ---
    lista_final_pacientes = []
    stats = {"Finalizado": 0, "En Progreso": 0, "Pendiente": 0}

    columnas_base = ['RUT', 'Nombre Paciente']
    tests_del_dia = sorted(list(set(test for pac in pacientes_agendados for test in pac['tests_asignados'])))
    if not tests_del_dia:
        tests_del_dia = []

    for paciente in pacientes_agendados:
        rut = paciente['rut']
        paciente_row = {'RUT': rut, 'Nombre Paciente': paciente['nombre_completo']}
        
        tests_asignados = set(paciente['tests_asignados'])
        tests_completados = set(progreso_tests.get(rut, []))
        
        proceso_iniciado = rut in ruts_iniciados
        proceso_finalizado = tests_completados.issuperset(tests_asignados)

        # Determinar estado general para las estadísticas, el filtro y la nueva columna
        estado_general_str = ""
        estado_general_display = ""

        if not proceso_iniciado:
            stats["Pendiente"] += 1
            estado_general_str = "Pendientes"
            estado_general_display = "🟡 Pendiente"
        elif proceso_finalizado:
            stats["Finalizado"] += 1
            estado_general_str = "Finalizados"
            estado_general_display = "✅ Finalizado"
        else:
            stats["En Progreso"] += 1
            estado_general_str = "En Progreso"
            estado_general_display = "🔵 En Progreso"
        
        paciente_row['estado_general_filtro'] = estado_general_str # Para el filtro
        paciente_row['Estado General'] = estado_general_display # Para la tabla

        # Determinar el test "En Progreso" para la tabla detallada
        test_en_progreso = None
        if proceso_iniciado and not proceso_finalizado:
            for test in paciente['tests_asignados']:
                if test not in tests_completados:
                    test_en_progreso = test
                    break

        # Rellenar el estado para cada test en la tabla
        for test in tests_del_dia:
            if test not in tests_asignados:
                paciente_row[test] = '⚪ No Aplica'
            elif test in tests_completados:
                paciente_row[test] = '✅ Finalizado'
            elif test == test_en_progreso:
                paciente_row[test] = '🔵 En Progreso'
            else:
                paciente_row[test] = '🟡 Pendiente'
        
        lista_final_pacientes.append(paciente_row)

    # --- VISTA DE RESUMEN ---
    total_agendados = len(pacientes_agendados)
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
            st.plotly_chart(fig, width='stretch', config=config)

    with col2:
        st.subheader("Resumen del Día")
        st.metric("Total Pacientes (Salud Mental)", total_agendados)
        st.metric("Procesos Finalizados", stats['Finalizado'])
        st.metric("Procesos Pendientes/En Curso", stats['Pendiente'] + stats['En Progreso'], delta_color="inverse")

    st.markdown("---")
    
    # --- VISTA DE TABLA DETALLADA Y FILTROS ---
    st.subheader("Estado Detallado de Evaluaciones de Pacientes")
    
    filter_option = st.radio(
        "Filtrar pacientes por estado general:",
        ('Todos', 'Pendientes', 'En Progreso', 'Finalizados'),
        horizontal=True,
        key="filter_pacientes"
    )

    if filter_option == 'Todos':
        filtered_list = lista_final_pacientes
    else:
        filtered_list = [p for p in lista_final_pacientes if p.get('estado_general_filtro') == filter_option]

    if filtered_list:
        # Definir el orden de las columnas para el DataFrame final
        columnas_finales = columnas_base + tests_del_dia + ['Estado General']
        df = pd.DataFrame(filtered_list)
        # Reordenar y mostrar solo las columnas deseadas
        st.dataframe(df[columnas_finales], width='stretch')
    else:
        st.info(f"No hay pacientes que coincidan con el filtro '{filter_option}'.")

