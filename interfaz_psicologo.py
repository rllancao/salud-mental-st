import streamlit as st
from supabase import Client
import io
import pymysql
import json
from datetime import date, datetime, timedelta
import pandas as pd
import plotly.graph_objects as go
from concurrent.futures import ThreadPoolExecutor, as_completed

BUCKET_NAME = "ficha_ingreso_SM_bucket"
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

# --- Función para buscar pacientes de aeronáutica (SOLO HOY) ---
@st.cache_data(ttl=300)
def fetch_aeronautica_hoy(sede):
    connection = connect_to_mysql()
    if not connection:
        return []

    sede_busqueda = sede
    if "SANTIAGO" in sede:
        sede_busqueda = "CENTRO DE SALUD WORKMED SANTIAGO"

    # Busca solo los que tienen EVALUACION SALUD MENTAL en sus prestaciones para el día de HOY
    query = """
    SELECT datosPersona, prestacionesSalud
    FROM `agendaViewPrest`
    WHERE fecha = CURDATE() 
      AND nombre_lab LIKE %s 
      AND prestacionesSalud LIKE %s
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (f"%{sede_busqueda}%", '%EVALUACION SALUD MENTAL%'))
            results = cursor.fetchall()
        
        pacientes_aeronautica = []
        
        for row in results:
            try:
                datos_persona = json.loads(row[0])
                rut = datos_persona.get('rut')
                nombre_completo = " ".join(filter(None, [
                    datos_persona.get('nombre', '').strip(),
                    datos_persona.get('nombre2', '').strip(),
                    datos_persona.get('apellidoP', '').strip(),
                    datos_persona.get('apellidoM', '').strip()
                ]))
                
                # Parsear prestaciones originales
                prestaciones_str = row[1] if len(row) > 1 else ""
                tests_originales = []
                if prestaciones_str:
                    try:
                        lista_prest = json.loads(prestaciones_str)
                        for p in lista_prest:
                            for t in TESTS_SALUD_MENTAL:
                                if t in p.upper() and t not in tests_originales:
                                    tests_originales.append(t)
                    except: pass

                pacientes_aeronautica.append({
                    "rut": rut,
                    "nombre_completo": nombre_completo,
                    "tests_originales": tests_originales
                })
            except json.JSONDecodeError:
                continue 

        return pacientes_aeronautica
    except Exception as e:
        st.error(f"Error al buscar los pacientes de aeronáutica: {e}")
        return []

# --- Función para obtener TODOS los pacientes (RANGO 14 DÍAS) ---
# Usada para Agendamiento Manual y Estado Diario
@st.cache_data(ttl=300)
def fetch_todos_pacientes_rango(sede):
    connection = connect_to_mysql()
    if not connection:
        return []

    sede_busqueda = sede
    if "SANTIAGO" in sede:
        sede_busqueda = "CENTRO DE SALUD WORKMED SANTIAGO"

    # Consulta con rango de fecha (últimos 14 días) y orden descendente
    query = """
    SELECT datosPersona, prestacionesSalud, fecha
    FROM `agendaViewPrest`
    WHERE fecha >= DATE_SUB(CURDATE(), INTERVAL 14 DAY) 
      AND fecha <= CURDATE()
      AND nombre_lab LIKE %s 
      AND prestacionesSalud IS NOT NULL
      AND prestacionesSalud != ''
    ORDER BY fecha DESC
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (f"%{sede_busqueda}%",))
            results = cursor.fetchall()
        
        todos_pacientes = []
        
        for row in results:
            try:
                datos_persona = json.loads(row[0])
                prestaciones_str = row[1] or ""
                fecha_atencion = row[2] # Obtenemos la fecha
                
                # Parsear prestaciones y filtrar
                tests_originales = []
                tiene_prestacion_sm = False
                
                # Identificar si es aeronáutica explícitamente o tiene tests
                is_aeronautica = 'evaluacion salud mental' in prestaciones_str.lower()
                if is_aeronautica: tiene_prestacion_sm = True

                if prestaciones_str:
                    try:
                        lista_prest = json.loads(prestaciones_str)
                        for p in lista_prest:
                            for t in TESTS_SALUD_MENTAL:
                                if t in p.upper():
                                    tiene_prestacion_sm = True
                                    if t not in tests_originales:
                                        tests_originales.append(t)
                    except: pass 

                if tiene_prestacion_sm:
                    rut = datos_persona.get('rut')
                    nombre_completo = " ".join(filter(None, [
                        datos_persona.get('nombre', '').strip(),
                        datos_persona.get('nombre2', '').strip(),
                        datos_persona.get('apellidoP', '').strip(),
                        datos_persona.get('apellidoM', '').strip()
                    ]))

                    todos_pacientes.append({
                        "fecha": fecha_atencion,
                        "rut": rut,
                        "nombre_completo": nombre_completo,
                        "tests_originales": tests_originales
                    })
            except json.JSONDecodeError:
                continue 

        return todos_pacientes
    except Exception as e:
        st.error(f"Error al buscar el listado de pacientes: {e}")
        return []

# --- NUEVA FUNCIÓN OPTIMIZADA: Carga Masiva de Asignaciones (PARALELIZADA) ---
@st.cache_data(ttl=60)
def fetch_mapa_asignaciones(_supabase: Client, ruts: list):
    """
    Descarga todas las asignaciones manuales y de aeronáutica en paralelo.
    """
    manual_map = {}
    aero_map = {}
    
    if not ruts:
        return manual_map, aero_map

    try:
        start_date = (date.today() - timedelta(days=15)).strftime('%Y-%m-%d 00:00:00')
        
        # Función helper para ejecutar consultas en hilos
        def query_manual():
            return _supabase.from_('asignaciones_manuales')\
                .select('rut, tests_asignados, created_at')\
                .in_('rut', ruts)\
                .gte('created_at', start_date)\
                .order('created_at', desc=True)\
                .execute()

        def query_aero():
            return _supabase.from_('asignaciones_aeronautica')\
                .select('rut, tests_asignados, created_at')\
                .in_('rut', ruts)\
                .gte('created_at', start_date)\
                .order('created_at', desc=True)\
                .execute()

        # Ejecución paralela de las 2 consultas
        with ThreadPoolExecutor(max_workers=2) as executor:
            future_manual = executor.submit(query_manual)
            future_aero = executor.submit(query_aero)
            
            res_manual = future_manual.result()
            res_aero = future_aero.result()

        # Procesamiento de resultados
        if res_manual.data:
            for item in res_manual.data:
                rut = item['rut']
                if rut not in manual_map:
                    manual_map[rut] = item.get('tests_asignados', [])
            
        if res_aero.data:
            for item in res_aero.data:
                rut = item['rut']
                if rut not in aero_map:
                    aero_map[rut] = item.get('tests_asignados', [])
                    
    except Exception as e:
        st.error(f"Error al cargar asignaciones masivas: {e}")
        
    return manual_map, aero_map

# --- Función Genérica Individual (Mantenida para compatibilidad con Tabs 2 y 3) ---
def get_latest_assignment_generic(supabase: Client, rut: str, table_name: str):
    start_date = (date.today() - timedelta(days=15)).isoformat()
    try:
        response = supabase.from_(table_name).select('tests_asignados').eq('rut', rut).gte('created_at', f'{start_date}T00:00:00').order('created_at', desc=True).limit(1).execute()
        if response.data:
            return response.data[0].get('tests_asignados', [])
    except Exception:
        pass
    return None

# --- Helper Inteligente (Modificado para usar mapas opcionales) ---
def get_combined_assignment_smart(supabase: Client, rut: str, tests_originales: list, manual_map=None, aero_map=None):
    """
    Si se pasan los mapas (manual_map y aero_map), busca en memoria (Rápido).
    Si no se pasan, hace la consulta a Supabase (Lento, usado en tabs de edición individual).
    """
    # 1. Intentar buscar en Mapas (Optimización Tab 4)
    if manual_map is not None:
        if rut in manual_map:
            return manual_map[rut]
    else:
        # Fallback a consulta individual
        manual_tests = get_latest_assignment_generic(supabase, rut, 'asignaciones_manuales')
        if manual_tests is not None:
            return manual_tests

    # 2. Intentar buscar en Mapas (Optimización Tab 4)
    if aero_map is not None:
        if rut in aero_map:
            return aero_map[rut]
    else:
        # Fallback a consulta individual
        aero_tests = get_latest_assignment_generic(supabase, rut, 'asignaciones_aeronautica')
        if aero_tests is not None:
            return aero_tests
    
    return tests_originales

# --- FUNCIONES PARA ESTADO DIARIO ---
@st.cache_data(ttl=60)
def fetch_iniciados_recientes(_supabase: Client, sede):
    try:
        start_date = (date.today() - timedelta(days=15)).strftime('%Y-%m-%d 00:00:00')
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

@st.cache_data(ttl=60)
def fetch_progreso_tests(_supabase: Client, ruts: list):
    """
    Verifica el progreso en las 12 tablas de tests en PARALELO.
    """
    progreso = {rut: [] for rut in ruts}
    if not ruts: return progreso

    try:
        start_date = (date.today() - timedelta(days=15)).strftime('%Y-%m-%d 00:00:00')
        # 1. Obtener IDs de fichas (Una sola consulta)
        fichas_response = _supabase.from_('ficha_ingreso').select('id, rut').in_('rut', ruts).gte('created_at', start_date).execute()
        
        if not fichas_response.data:
            return progreso
        
        id_a_rut_map = {item['id']: item['rut'] for item in fichas_response.data}
        ids = list(id_a_rut_map.keys())
        if not ids: return progreso

        tablas_tests = ["test_epworth", "test_wonderlic", "test_disc", "test_epq_r", "test_pbll", "test_alerta", "test_barratt", "test_kostick", "test_psqi", "test_western", "test_d48", "test_16pf"]
        nombres_tests = ["EPWORTH", "WONDERLIC", "DISC", "EPQ-R", "PBLL", "ALERTA", "BARRATT", "KOSTICK", "PSQI", "WESTERN", "D-48", "16 PF"]

        # Función helper para ejecutar en hilo
        def check_tabla_test(tabla, nombre_test):
            try:
                res = _supabase.from_(tabla).select('id').in_('id', ids).execute()
                return nombre_test, res.data
            except:
                return nombre_test, []

        # 2. Ejecutar 12 consultas en paralelo
        with ThreadPoolExecutor(max_workers=12) as executor:
            futures = [executor.submit(check_tabla_test, t, n) for t, n in zip(tablas_tests, nombres_tests)]
            
            for future in as_completed(futures):
                nombre_test, data = future.result()
                if data:
                    for item in data:
                        rut = id_a_rut_map.get(item['id'])
                        if rut:
                            progreso[rut].append(nombre_test)

    except Exception as e:
        st.error(f"Error al verificar el progreso de los tests: {e}")
    
    return progreso

def crear_interfaz_psicologo(supabase: Client):
    st.title("Panel del Psicólogo")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Búsqueda de Informes", "Asignación Aeronáutica", "Agendamiento Manual", "Estado Diario"])

    # --- PESTAÑA 1: BÚSQUEDA DE INFORMES ---
    with tab1:
        st.header("Búsqueda y Descarga de Informes de Pacientes")
        st.write("Ingrese el RUT del paciente para buscar todos sus informes de salud mental asociados.")
        rut_busqueda = st.text_input("RUT del Paciente", placeholder="Ej. 12345678-9", key="rut_busqueda_psicologo")

        if st.button("Buscar Informes", key="btn_buscar_informes"):
            if not rut_busqueda:
                st.warning("Por favor, ingrese un RUT para buscar.")
            else:
                with st.spinner("Buscando todos los informes del paciente..."):
                    try:
                        todos_los_paths = set()
                        nombre_paciente = ""

                        # Buscar en tabla resumen
                        fichas_response = supabase.from_('registros_fichas_sm').select('nombre_completo, pdf_path').eq('rut', rut_busqueda).execute()
                        if fichas_response.data:
                            if not nombre_paciente:
                                nombre_paciente = fichas_response.data[0]['nombre_completo']
                            for ficha in fichas_response.data:
                                if ficha.get('pdf_path'):
                                    todos_los_paths.add(ficha['pdf_path'])
                        
                        # Buscar en tablas individuales
                        ids_response = supabase.from_('ficha_ingreso').select('id, nombre_completo').eq('rut', rut_busqueda).execute()
                        if ids_response.data:
                            if not nombre_paciente:
                                nombre_paciente = ids_response.data[0]['nombre_completo']
                            fichas_ids = [item['id'] for item in ids_response.data]
                            
                            for tabla_test in ["test_epworth", "test_epq_r"]:
                                test_response = supabase.from_(tabla_test).select('pdf_path').in_('id', fichas_ids).execute()
                                if test_response.data:
                                    for test in test_response.data:
                                        if test.get('pdf_path'):
                                            todos_los_paths.add(test['pdf_path'])

                        if todos_los_paths:
                            st.success(f"Se encontraron {len(todos_los_paths)} informes únicos para el paciente: {nombre_paciente}")
                            st.markdown("---")
                            for path in todos_los_paths:
                                nombre_archivo = path.split('/')[-1]
                                tipo_informe = "Informe Desconocido"
                                if "FichaIngreso" in nombre_archivo: tipo_informe = "Informe de Ficha de Ingreso"
                                elif "Epworth" in nombre_archivo: tipo_informe = "Informe de Test de Epworth"
                                elif "EPQR" in nombre_archivo: tipo_informe = "Informe de Test EPQ-R"
                                
                                st.subheader(f"📄 {tipo_informe}")
                                st.write(f"Nombre del archivo: `{nombre_archivo}`")
                                try:
                                    res = supabase.storage.from_(BUCKET_NAME).download(path=path)
                                    pdf_bytes = io.BytesIO(res)
                                    st.download_button(label=f"Descargar {tipo_informe}", data=pdf_bytes, file_name=nombre_archivo, mime="application/pdf", key=f"dl_{path}")
                                    st.markdown("---")
                                except Exception as download_error:
                                    st.error(f"No se pudo descargar el archivo '{nombre_archivo}': {download_error}")
                        else:
                            st.warning(f"No se encontró ningún informe para el RUT: {rut_busqueda}")
                    except Exception as db_error:
                        st.error(f"Error al consultar la base de datos: {db_error}")

    # --- PESTAÑA 2: ASIGNACIÓN AERONÁUTICA (Solo Hoy) ---
    with tab2:
        st.header("Asignación Manual para Aeronáutica")
        st.write("Listado de pacientes agendados **HOY** bajo perfil 'Aeronáutica' en su sede.")
        
        sedes_psicologo = st.session_state.get("user_sedes", [])
        if not sedes_psicologo:
            st.error("No tiene sedes asignadas. Por favor, contacte a un administrador.")
        else:
            sede_seleccionada = sedes_psicologo[0]
            if len(sedes_psicologo) > 1:
                sede_seleccionada = st.selectbox("Seleccione una sede:", options=sedes_psicologo, key="sede_psicologo_aero")

            # Usamos la función original que busca solo por CURDATE()
            pacientes_aeronautica = fetch_aeronautica_hoy(sede_seleccionada)

            if not pacientes_aeronautica:
                st.info("No se encontraron pacientes de aeronáutica agendados para hoy en esta sede.")
            else:
                st.success(f"Se encontraron {len(pacientes_aeronautica)} pacientes de aeronáutica.")
                
                for idx, paciente in enumerate(pacientes_aeronautica):
                    rut_p = paciente['rut']
                    nombre_p = paciente['nombre_completo']
                    
                    assigned_tests = get_latest_assignment_generic(supabase, rut_p, 'asignaciones_aeronautica')
                    if assigned_tests is None: assigned_tests = []

                    expander_title = f"**{nombre_p}** - {rut_p}"
                    if assigned_tests:
                        expander_title += f"  ✅ Asignados: {len(assigned_tests)}"
                    
                    with st.expander(expander_title):
                        st.write("Seleccione los tests a asignar:")
                        cols = st.columns(3)
                        selected_tests = []
                        for i, test in enumerate(TESTS_SALUD_MENTAL):
                            is_checked = cols[i % 3].checkbox(test, value=(test in assigned_tests), key=f"aero_{rut_p}_{test}_{idx}")
                            if is_checked:
                                selected_tests.append(test)
                        
                        if st.button("Guardar Asignación", key=f"guardar_aero_{rut_p}_{idx}"):
                            try:
                                response = supabase.from_('asignaciones_aeronautica').insert({
                                    'rut': rut_p,
                                    'tests_asignados': selected_tests
                                }).execute()
                                if response.data:
                                    st.success(f"Asignación para {nombre_p} guardada con éxito.")
                                    st.cache_data.clear()
                                else:
                                    st.error(f"Error al guardar: {response.error.message if response.error else 'Error desconocido'}")
                            except Exception as e:
                                st.error(f"Ocurrió una excepción al guardar: {e}")

    # --- PESTAÑA 3: AGENDAMIENTO MANUAL (Rango 14 días) ---
    with tab3:
        st.header("Agendamiento Manual de Pacientes (Todos)")
        st.write("Listado de pacientes agendados (últimos 14 días) con prestaciones de Salud Mental. Use el buscador para filtrar.")

        sedes_manual = st.session_state.get("user_sedes", [])
        if not sedes_manual:
            st.error("No tiene sedes asignadas.")
        else:
            sede_manual = sedes_manual[0]
            if len(sedes_manual) > 1:
                sede_manual = st.selectbox("Seleccione una sede:", options=sedes_manual, key="sede_manual_select")
            
            # BOTÓN DE ACTUALIZAR
            col_a, col_b = st.columns([5, 1])
            with col_a:
                rut_filter = st.text_input("Filtrar por RUT:", placeholder="Ej. 12345678-9", key="rut_filter_manual").strip()
            with col_b:
                st.write("")
                st.write("")
                if st.button("🔄 Actualizar"):
                    st.cache_data.clear()
                    st.rerun()
            
            with st.spinner(f"Cargando listado de pacientes SM para {sede_manual}..."):
                # Usamos la nueva función con rango
                todos_pacientes = fetch_todos_pacientes_rango(sede_manual)
            
            if rut_filter:
                pacientes_filtrados = [p for p in todos_pacientes if rut_filter in p['rut']]
            else:
                pacientes_filtrados = todos_pacientes

            if not pacientes_filtrados:
                st.info("No se encontraron pacientes con prestaciones de salud mental en el rango seleccionado (o que coincidan con el filtro).")
            else:
                st.info(f"Mostrando {len(pacientes_filtrados)} pacientes.")
                
                for idx, paciente in enumerate(pacientes_filtrados):
                    rut_p = paciente['rut']
                    nombre_p = paciente['nombre_completo']
                    fecha_p = paciente['fecha']
                    
                    # Convertir fecha para mostrar amigablemente
                    fecha_str = fecha_p.strftime('%Y-%m-%d') if isinstance(fecha_p, (date, datetime)) else str(fecha_p)
                    
                    tests_originales_p = paciente.get('tests_originales', [])

                    assigned_tests = get_combined_assignment_smart(supabase, rut_p, tests_originales_p)
                    
                    # Mostrar fecha en el título del expander
                    expander_title = f"**[{fecha_str}] {nombre_p}** - {rut_p}"
                    if assigned_tests:
                        expander_title += f"  ✅ Asignados: {len(assigned_tests)}"
                    else:
                        expander_title += "  (Sin tests)"
                    
                    with st.expander(expander_title):
                        if assigned_tests:
                            st.info(f"Tests actuales (Agenda + Manual): {', '.join(assigned_tests)}")
                        else:
                            st.warning("Este paciente no tiene tests de salud mental asignados.")

                        st.write("Seleccione los tests a agregar/modificar:")
                        
                        cols_m = st.columns(3)
                        selected_tests_m = []
                        
                        for i, test in enumerate(TESTS_SALUD_MENTAL):
                            is_checked_m = cols_m[i % 3].checkbox(
                                test, 
                                value=(test in assigned_tests), 
                                key=f"manual_{rut_p}_{test}_{idx}"
                            )
                            if is_checked_m:
                                selected_tests_m.append(test)
                        
                        if st.button("Guardar Asignación Manual", key=f"btn_save_manual_{rut_p}_{idx}"):
                            try:
                                response = supabase.from_('asignaciones_manuales').insert({
                                    'rut': rut_p,
                                    'tests_asignados': selected_tests_m
                                }).execute()
                                
                                if response.data:
                                    st.success(f"¡Asignación actualizada para {nombre_p}!")
                                    st.cache_data.clear() 
                                    st.rerun()
                                else:
                                    st.error("Error al guardar en la base de datos.")
                            except Exception as e:
                                st.error(f"Error de conexión: {e}")
                                
    # --- PESTAÑA 4: ESTADO DIARIO (OPTIMIZADA) ---
    with tab4:
        st.header("Estado Diario de Pacientes")
        st.write("Monitoreo del progreso de evaluaciones (Últimos 14 días).")

        sedes_diario = st.session_state.get("user_sedes", [])
        if not sedes_diario:
            st.error("No tiene sedes asignadas.")
        else:
            sede_d = sedes_diario[0]
            if len(sedes_diario) > 1: sede_d = st.selectbox("Sede:", sedes_diario, key="sede_diario_psi")
            
            if st.button("🔄 Actualizar Tabla", key="refresh_diario_psi"):
                st.cache_data.clear()
                st.rerun()

            with st.spinner("Cargando datos masivos..."):
                # 1. Traer pacientes (MySQL)
                pacientes = fetch_todos_pacientes_rango(sede_d)
                
                # 2. Preparar listas de RUTs para carga masiva
                lista_ruts = [p['rut'] for p in pacientes]
                
                # 3. Cargar asignaciones en BATCH (OPTIMIZACIÓN CLAVE)
                manual_map, aero_map = fetch_mapa_asignaciones(supabase, lista_ruts)
                
                # 4. Cargar datos de progreso (Supabase)
                iniciados = fetch_iniciados_recientes(supabase, sede_d)
                progreso = fetch_progreso_tests(supabase, lista_ruts)

            if not pacientes:
                st.info("No hay pacientes agendados en el rango seleccionado.")
            else:
                rows = []
                stats = {"Pendiente": 0, "En Progreso": 0, "Finalizado": 0}
                all_assigned_tests = TESTS_SALUD_MENTAL 

                for p in pacientes:
                    rut = p['rut']
                    fecha_p = p['fecha']
                    fecha_str = fecha_p.strftime('%Y-%m-%d') if isinstance(fecha_p, (date, datetime)) else str(fecha_p)
                    
                    # Usamos la versión optimizada con mapas en memoria
                    tests_finales = get_combined_assignment_smart(
                        supabase, 
                        rut, 
                        p['tests_originales'], 
                        manual_map=manual_map, 
                        aero_map=aero_map
                    )
                    
                    tests_hechos = set(progreso.get(rut, []))
                    
                    num_asignados = len(tests_finales)
                    num_completados = len(tests_hechos.intersection(set(tests_finales)))
                    
                    estado_filtro = "Pendiente"
                    icono_estado = "🟡" 
                    
                    if not tests_finales:
                         estado_filtro = "Sin Tests"
                         icono_estado = "⚪"
                         display_estado = f"{icono_estado} 0/0"
                    elif rut in iniciados:
                        if num_completados >= num_asignados and num_asignados > 0:
                            estado_filtro = "Finalizado"
                            icono_estado = "✅"
                            stats["Finalizado"] += 1
                        elif num_completados > 0:
                            estado_filtro = "En Progreso"
                            icono_estado = "🔵"
                            stats["En Progreso"] += 1
                        else:
                            estado_filtro = "Pendiente"
                            icono_estado = "🟡"
                            stats["Pendiente"] += 1
                    else:
                        estado_filtro = "Pendiente"
                        icono_estado = "🟡"
                        stats["Pendiente"] += 1
                    
                    if estado_filtro != "Sin Tests" and tests_finales:
                        display_estado = f"{icono_estado} {num_completados}/{num_asignados}"
                    elif estado_filtro == "Sin Tests":
                         display_estado = "⚪ Sin Asignación"

                    row_data = {
                        "Fecha": fecha_str, 
                        "RUT": rut,
                        "Nombre": p['nombre_completo'],
                        "Estado": display_estado, 
                        "_filtro": estado_filtro
                    }
                    
                    primer_pendiente_encontrado = False
                    for test in all_assigned_tests:
                        if test not in tests_finales:
                            row_data[test] = '⚪ No Aplica'
                        elif test in tests_hechos:
                            row_data[test] = '✅ Finalizado'
                        else:
                            if estado_filtro == "En Progreso" and not primer_pendiente_encontrado:
                                row_data[test] = '🔵 En Progreso'
                                primer_pendiente_encontrado = True
                            else:
                                row_data[test] = '🟡 Pendiente'

                    rows.append(row_data)
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Pendientes", stats["Pendiente"])
                c2.metric("En Progreso", stats["En Progreso"])
                c3.metric("Finalizados", stats["Finalizado"])
                
                filtro = st.radio("Filtrar:", ["Todos", "Pendientes", "En Progreso", "Finalizados"], horizontal=True, key="filtro_estado_psi")
                
                df = pd.DataFrame(rows)
                if filtro == "Pendientes":
                    df = df[df["_filtro"] == "Pendiente"]
                elif filtro == "En Progreso":
                    df = df[df["_filtro"] == "En Progreso"]
                elif filtro == "Finalizados":
                    df = df[df["_filtro"] == "Finalizado"]
                
                if not df.empty:
                    cols_fixed = ['Fecha', 'RUT', 'Nombre', 'Estado']
                    cols_tests = [c for c in df.columns if c not in cols_fixed and c != '_filtro']
                    final_cols = cols_fixed + cols_tests
                    st.dataframe(df[final_cols], use_container_width=True)
                else:
                    st.info("No hay datos para mostrar con el filtro seleccionado.")