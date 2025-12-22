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

# --- Función para obtener pacientes agendados ---
@st.cache_data(ttl=300)
def fetch_agendados_hoy(sede, _supabase: Client):
    connection = connect_to_mysql()
    if not connection:
        return []

    sede_busqueda = sede
    if "SANTIAGO" in sede:
        sede_busqueda = "CENTRO DE SALUD WORKMED SANTIAGO"

    query = """
    SELECT datosPersona, prestacionesSalud, fecha
    FROM `agendaViewPrest`
    WHERE fecha >= DATE_SUB(CURDATE(), INTERVAL 14 DAY) 
      AND fecha <= CURDATE()
      AND nombre_lab LIKE %s 
      AND prestacionesSalud IS NOT NULL
    ORDER BY fecha DESC
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (f"%{sede_busqueda}%",))
            results = cursor.fetchall()
        
        pacientes_agendados = []
        ruts_aeronautica = []

        for row in results:
            try:
                datos_persona = json.loads(row[0])
                prestaciones_str = row[1] or ""
                fecha_atencion = row[2]
                
                is_aeronautica = 'evaluacion salud mental' in prestaciones_str.lower()
                
                tests_asignados_mysql = []
                try:
                    lista_prestaciones_raw = json.loads(prestaciones_str)
                    for prestacion in lista_prestaciones_raw:
                        for test_valido in TESTS_SALUD_MENTAL:
                            if test_valido in prestacion.upper() and test_valido not in tests_asignados_mysql:
                                tests_asignados_mysql.append(test_valido)
                except (json.JSONDecodeError, TypeError):
                    pass
                
                if is_aeronautica or tests_asignados_mysql:
                    nombre_completo = " ".join(filter(None, [
                        datos_persona.get('nombre', '').strip(),
                        datos_persona.get('nombre2', '').strip(),
                        datos_persona.get('apellidoP', '').strip(),
                        datos_persona.get('apellidoM', '').strip()
                    ]))
                    
                    paciente = {
                        "fecha": fecha_atencion,
                        "rut": datos_persona.get('rut'),
                        "nombre_completo": nombre_completo,
                        "tests_asignados": tests_asignados_mysql,
                        "is_aeronautica": is_aeronautica
                    }
                    pacientes_agendados.append(paciente)
                    ruts_aeronautica.append(paciente["rut"])
            except Exception:
                continue

        if ruts_aeronautica:
            start_date = (date.today() - timedelta(days=15)).isoformat()
            
            res_aero = _supabase.from_('asignaciones_aeronautica').select('rut, tests_asignados').in_('rut', ruts_aeronautica).gte('created_at', f'{start_date}T00:00:00').execute()
            mapa_aero = {item['rut']: item['tests_asignados'] for item in res_aero.data} if res_aero.data else {}

            res_manual = _supabase.from_('asignaciones_manuales').select('rut, tests_asignados').in_('rut', ruts_aeronautica).gte('created_at', f'{start_date}T00:00:00').execute()
            mapa_manual = {item['rut']: item['tests_asignados'] for item in res_manual.data} if res_manual.data else {}

            for paciente in pacientes_agendados:
                rut = paciente["rut"]
                if rut in mapa_manual:
                    paciente["tests_asignados"] = mapa_manual[rut]
                elif rut in mapa_aero:
                    paciente["tests_asignados"] = mapa_aero[rut]
        
        pacientes_final = [p for p in pacientes_agendados if p["tests_asignados"] or p["is_aeronautica"]]
        return pacientes_final

    except Exception as e:
        st.error(f"Error al buscar los pacientes agendados: {e}")
        return []

# --- Función para obtener RUTs de pacientes iniciados ---
@st.cache_data(ttl=60)
def fetch_iniciados_recientes(_supabase: Client, sede):
    try:
        today = datetime.now()
        start_date = (today - timedelta(days=15)).strftime('%Y-%m-%d 00:00:00')
        
        sede_busqueda = sede
        if "SANTIAGO" in sede:
            sede_busqueda = "CENTRO DE SALUD WORKMED SANTIAGO"

        response = _supabase.from_('ficha_ingreso').select('rut').like('sucursal_workmed', f'%{sede_busqueda}%').gte('created_at', start_date).execute()

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
        today = datetime.now()
        start_date = (today - timedelta(days=15)).strftime('%Y-%m-%d 00:00:00')

        fichas_response = _supabase.from_('ficha_ingreso').select('id, rut').in_('rut', ruts).gte('created_at', start_date).execute()
        
        if not fichas_response.data:
            return progreso
        
        id_a_rut_map = {item['id']: item['rut'] for item in fichas_response.data}
        ids = list(id_a_rut_map.keys())

        if not ids: return progreso

        tablas_tests = ["test_epworth", "test_wonderlic", "test_disc", "test_epq_r", "test_pbll", "test_alerta", "test_barratt", "test_kostick", "test_psqi", "test_western", "test_d48", "test_16pf"]
        nombres_tests = ["EPWORTH", "WONDERLIC", "DISC", "EPQ-R", "PBLL", "ALERTA", "BARRATT", "KOSTICK", "PSQI", "WESTERN", "D-48", "16 PF"]

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

    with st.spinner(f"Cargando pacientes de los últimos 14 días para {sede_seleccionada}..."):
        pacientes_agendados = fetch_agendados_hoy(sede_seleccionada, _supabase)
        ruts_iniciados = fetch_iniciados_recientes(_supabase, sede_seleccionada)
        progreso_tests = fetch_progreso_tests(_supabase, [p['rut'] for p in pacientes_agendados])

    if not pacientes_agendados:
        st.info("No hay pacientes con prestaciones de salud mental agendados en los últimos 14 días.")
        return

    stats_hoy = {"Finalizado": 0, "En Progreso": 0, "Pendiente": 0}
    all_assigned_tests = sorted(list(set(test for p in pacientes_agendados for test in p['tests_asignados'])))
    
    lista_final_pacientes = []
    today_date = date.today()

    for paciente in pacientes_agendados:
        rut = paciente['rut']
        fecha_paciente = paciente['fecha']
        if isinstance(fecha_paciente, datetime): fecha_paciente = fecha_paciente.date()
        fecha_str = fecha_paciente.strftime('%Y-%m-%d') if isinstance(fecha_paciente, (date, datetime)) else str(fecha_paciente)
        
        tests_asignados = set(paciente['tests_asignados'])
        tests_completados = set(progreso_tests.get(rut, []))
        num_asignados = len(tests_asignados)
        num_completados = len(tests_completados.intersection(tests_asignados))
        
        # --- LÓGICA HÍBRIDA ---
        estado_filtro = "Pendiente"
        icono = "🟡"
        
        if rut not in ruts_iniciados and num_completados == 0:
             estado_filtro = "Pendiente"
             icono = "🟡"
             if fecha_paciente == today_date: stats_hoy["Pendiente"] += 1
        else:
            if num_completados >= num_asignados and num_asignados > 0:
                estado_filtro = "Finalizado"
                icono = "✅"
                if fecha_paciente == today_date: stats_hoy["Finalizado"] += 1
            else:
                estado_filtro = "En Progreso"
                icono = "🔵"
                if fecha_paciente == today_date: stats_hoy["En Progreso"] += 1
        
        display_estado = f"{icono} {num_completados}/{num_asignados}"
        
        row_data = {
            'Fecha': fecha_str,
            'RUT': rut, 
            'Nombre Paciente': paciente['nombre_completo'],
            'Estado': display_estado, # Columna híbrida
            '_filtro': estado_filtro # Oculta para filtrar
        }

        # Rellenar estado por test
        primer_pendiente_encontrado = False
        for test in all_assigned_tests:
            if test not in tests_asignados: row_data[test] = '⚪ No Aplica'
            elif test in tests_completados: row_data[test] = '✅ Finalizado'
            else:
                if estado_filtro == "En Progreso" and not primer_pendiente_encontrado:
                    row_data[test] = '🔵 En Progreso'
                    primer_pendiente_encontrado = True
                else:
                    row_data[test] = '🟡 Pendiente'
        
        lista_final_pacientes.append(row_data)

    total_agendados_hoy = stats_hoy['Finalizado'] + stats_hoy['En Progreso'] + stats_hoy['Pendiente']
    
    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("Estado de Evaluaciones (Solo Hoy)")
        if total_agendados_hoy > 0:
            labels = ['Finalizados', 'En Progreso', 'Pendientes']
            values = [stats_hoy['Finalizado'], stats_hoy['En Progreso'], stats_hoy['Pendiente']]
            colors = ['#2ca02c', '#1f77b4', '#ffdd57']
            fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.4, marker_colors=colors, textinfo='value', hoverinfo='label+percent')])
            fig.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0), height=250)
            config = {'displayModeBar': False}
            st.plotly_chart(fig, width='stretch', config=config)
        else:
            st.info("No hay pacientes agendados para hoy.")

    with col2:
        st.subheader("Resumen del Día (Hoy)")
        st.metric("Total Pacientes Hoy", total_agendados_hoy)
        st.metric("Procesos Finalizados Hoy", stats_hoy['Finalizado'])
        st.metric("Procesos Pendientes Hoy", stats_hoy['Pendiente'] + stats_hoy['En Progreso'], delta_color="inverse")

    st.markdown("---")
    
    col_filtros, col_actualizar = st.columns([3, 1])
    with col_filtros:
        st.write("#### Filtrar Pacientes (Últimos 14 días)")
        filter_option = st.radio(
            "Seleccione una vista:", 
            ('Todos', 'Pendientes', 'En Progreso', 'Finalizados'), 
            horizontal=True, 
            label_visibility="collapsed"
        )
    
    with col_actualizar:
        st.write("") 
        if st.button("🔄️ Actualizar Tabla"):
            st.cache_data.clear()
            st.rerun()

    if filter_option == "Pendientes":
        filtered_list = [p for p in lista_final_pacientes if p['_filtro'] == 'Pendiente']
    elif filter_option == "En Progreso":
        filtered_list = [p for p in lista_final_pacientes if p['_filtro'] == 'En Progreso']
    elif filter_option == "Finalizados":
        filtered_list = [p for p in lista_final_pacientes if p['_filtro'] == 'Finalizado']
    else:
        filtered_list = lista_final_pacientes

    if filtered_list:
        df = pd.DataFrame(filtered_list)
        # Mostrar tabla sin la columna oculta de filtro
        if '_filtro' in df.columns: df = df.drop(columns=['_filtro'])
        
        # Reordenar: Fecha, RUT, Nombre, Estado...
        cols = ['Fecha', 'RUT', 'Nombre Paciente', 'Estado'] + [c for c in df.columns if c not in ['Fecha', 'RUT', 'Nombre Paciente', 'Estado']]
        df = df[cols]
        
        st.dataframe(df, width='stretch')
    else:
        st.info("No hay pacientes que coincidan con el filtro seleccionado.")