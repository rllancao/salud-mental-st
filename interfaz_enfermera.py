import streamlit as st
import pandas as pd
from supabase import Client
import pymysql
import json
from datetime import datetime, timedelta, date
import plotly.graph_objects as go

TESTS_SALUD_MENTAL = [
    "EPWORTH", "DISC", "WONDERLIC", "ALERTA", "BARRATT", 
    "PBLL", "16 PF", "KOSTICK", "PSQI", "D-48", "WESTERN", "EPQ-R"
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
def fetch_agendados_hoy(sede, _supabase: Client):
    connection = connect_to_mysql()
    if not connection:
        return []

    sede_busqueda = sede
    if "SANTIAGO" in sede:
        sede_busqueda = "CENTRO DE SALUD WORKMED SANTIAGO"

    # --- CORRECCIÓN: La consulta ahora incluye a todos los que tienen prestaciones de salud mental ---
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
        ruts_aeronautica = []

        for row in results:
            datos_persona = json.loads(row[0])
            prestaciones_str = row[1] or ""
            
            # --- CORRECCIÓN: Se identifica a aeronáutica por la prestación ---
            is_aeronautica = 'evaluacion salud mental' in prestaciones_str.lower()
            
            tests_asignados_mysql = []
            try:
                lista_prestaciones_raw = json.loads(prestaciones_str)
                for prestacion in lista_prestaciones_raw:
                    for test_valido in TESTS_SALUD_MENTAL:
                        if test_valido in prestacion.upper() and test_valido not in tests_asignados_mysql:
                            tests_asignados_mysql.append(test_valido)
            except (json.JSONDecodeError, TypeError):
                continue
            
            # Solo agregar al listado si es de aeronáutica o tiene tests asignados en MySQL
            if is_aeronautica or tests_asignados_mysql:
                nombre_completo = " ".join(filter(None, [
                    datos_persona.get('nombre', '').strip(),
                    datos_persona.get('nombre2', '').strip(),
                    datos_persona.get('apellidoP', '').strip(),
                    datos_persona.get('apellidoM', '').strip()
                ]))
                
                paciente = {
                    "rut": datos_persona.get('rut'),
                    "nombre_completo": nombre_completo,
                    "tests_asignados": tests_asignados_mysql,
                    "is_aeronautica": is_aeronautica
                }
                pacientes_agendados.append(paciente)
                
                if is_aeronautica:
                    ruts_aeronautica.append(paciente["rut"])

        # Buscar asignaciones manuales para pacientes de aeronáutica
        if ruts_aeronautica:
            today_str = date.today().isoformat()
            response = _supabase.from_('asignaciones_aeronautica').select('rut, tests_asignados').in_('rut', ruts_aeronautica).gte('created_at', f'{today_str}T00:00:00').execute()
            
            if response.data:
                asignaciones_manuales = {item['rut']: item['tests_asignados'] for item in response.data}
                
                for paciente in pacientes_agendados:
                    if paciente["is_aeronautica"] and paciente["rut"] in asignaciones_manuales:
                        # Para aeronáutica, los tests manuales reemplazan a los de la agenda
                        paciente["tests_asignados"] = asignaciones_manuales[paciente["rut"]]
        
        # Filtrar pacientes que no sean de aeronáutica y no tengan tests
        pacientes_final = [p for p in pacientes_agendados if p["is_aeronautica"] or p["tests_asignados"]]

        return pacientes_final

    except Exception as e:
        st.error(f"Error al buscar los pacientes agendados: {e}")
        return []

# --- Función para obtener RUTs de pacientes que ya iniciaron el proceso ---
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

# --- Función para obtener el progreso de los tests ---
@st.cache_data(ttl=60)
def fetch_progreso_tests(_supabase: Client, ruts: list):
    progreso = {rut: [] for rut in ruts}
    if not ruts:
        return progreso

    try:
        fichas_response = _supabase.from_('ficha_ingreso').select('id, rut').in_('rut', ruts).execute()
        if not fichas_response.data:
            return progreso
        
        id_a_rut_map = {item['id']: item['rut'] for item in fichas_response.data}
        ids = list(id_a_rut_map.keys())

        if not ids: return progreso

        # Consultar todos los tests completados
        tablas_tests = ["test_epworth", "test_wonderlic", "test_disc", "test_epq_r", "test_pbll", "test_alerta"]
        nombres_tests = ["EPWORTH", "WONDERLIC", "DISC", "EPQ-R", "PBLL", "ALERTA"]

        for tabla, nombre_test in zip(tablas_tests, nombres_tests):
            response = _supabase.from_(tabla).select('id').in_('id', ids).execute()
            if response.data:
                for item in response.data:
                    rut = id_a_rut_map.get(item['id'])
                    if rut:
                        progreso[rut].append(nombre_test)

    except Exception as e:
        st.error(f"Error al verificar el progreso de los tests: {e}")
    
    return progreso

# --- Interfaz principal de la Enfermera ---
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
        # Se pasa el cliente de supabase a la función
        pacientes_agendados = fetch_agendados_hoy(sede_seleccionada, _supabase)
        ruts_iniciados = fetch_iniciados_hoy(_supabase, sede_seleccionada)
        progreso_tests = fetch_progreso_tests(_supabase, [p['rut'] for p in pacientes_agendados])

    if not pacientes_agendados:
        st.info("No hay pacientes con prestaciones de salud mental agendados para hoy en esta sede.")
        return

    # Preparar datos para la tabla y las estadísticas
    stats = {"Finalizado": 0, "En Progreso": 0, "Pendiente": 0}
    all_assigned_tests = sorted(list(set(test for p in pacientes_agendados for test in p['tests_asignados'])))
    
    lista_final_pacientes = []
    for paciente in pacientes_agendados:
        rut = paciente['rut']
        tests_asignados = set(paciente['tests_asignados'])
        
        row_data = {'RUT': rut, 'Nombre Paciente': paciente['nombre_completo']}
        
        tests_completados = set(progreso_tests.get(rut, []))
        num_asignados = len(tests_asignados)
        num_completados = len(tests_completados.intersection(tests_asignados))
        
        estado_general = ""
        if rut not in ruts_iniciados:
            estado_general = "🟡 Pendiente"
            stats["Pendiente"] += 1
        else:
            if num_completados >= num_asignados and num_asignados > 0:
                estado_general = "✅ Finalizado"
                stats["Finalizado"] += 1
            else:
                estado_general = "🔵 En Progreso"
                stats["En Progreso"] += 1
        
        row_data['Estado General'] = estado_general
        
        # Rellenar estado por test
        primer_pendiente_encontrado = False
        for test in all_assigned_tests:
            if test not in tests_asignados:
                row_data[test] = '⚪ No Aplica'
            elif test in tests_completados:
                row_data[test] = '✅ Finalizado'
            else:
                if estado_general == "🔵 En Progreso" and not primer_pendiente_encontrado:
                    row_data[test] = '🔵 En Progreso'
                    primer_pendiente_encontrado = True
                else:
                    row_data[test] = '🟡 Pendiente'
        
        lista_final_pacientes.append(row_data)

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
    
    # --- MEJORA DE DISEÑO: Se alinea el botón de actualizar con los filtros ---
    col_filtros, col_actualizar = st.columns([3, 1])
    with col_filtros:
        st.write("#### Filtrar Pacientes")
        filter_option = st.radio(
            "Seleccione una vista:", 
            ('Todos', 'Pendientes', 'En Progreso', 'Finalizados'), 
            horizontal=True, 
            label_visibility="collapsed"
        )
    
    with col_actualizar:
        st.write("") # Spacer para alinear verticalmente el botón
        if st.button("🔄️ Actualizar Tabla"):
            st.cache_data.clear()
            st.rerun()

    if filter_option == "Pendientes":
        filtered_list = [p for p in lista_final_pacientes if 'Pendiente' in p['Estado General']]
    elif filter_option == "En Progreso":
        filtered_list = [p for p in lista_final_pacientes if 'En Progreso' in p['Estado General']]
    elif filter_option == "Finalizados":
        filtered_list = [p for p in lista_final_pacientes if 'Finalizado' in p['Estado General']]
    else:
        filtered_list = lista_final_pacientes

    if filtered_list:
        df = pd.DataFrame(filtered_list)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No hay pacientes que coincidan con el filtro seleccionado.")

