import streamlit as st
from supabase import Client
import io
import pymysql
import json
from datetime import date, datetime, timedelta
import pandas as pd
import plotly.graph_objects as go

BUCKET_NAME = "ficha_ingreso_SM_bucket"
TESTS_SALUD_MENTAL = [
    "EPWORTH", "DISC", "WONDERLIC", "ALERTA", "BARRATT", 
    "PBLL", "16 PF", "KOSTICK", "PSQI", "D-48", "WESTERN", "EPQ-R"
]

# --- Conexión a Base de Datos MySQL (Con reconexión) ---
def get_mysql_connection():
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

# --- Función para buscar pacientes de aeronáutica ---
@st.cache_data(ttl=300)
def fetch_aeronautica_hoy(sede):
    connection = get_mysql_connection()
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
      AND prestacionesSalud LIKE %s
    """
    try:
        # Forzar reconexión si se cayó
        connection.ping(reconnect=True)
        
        with connection.cursor() as cursor:
            cursor.execute(query, (f"%{sede_busqueda}%", '%EVALUACION SALUD MENTAL%'))
            results = cursor.fetchall()
        
        pacientes_aeronautica = []
        
        for row in results:
            try:
                datos_persona = json.loads(row[0])
                # Extraer empresa del JSON
                empresa = datos_persona.get('nombre_contra', 'Empresa no especificada')
                
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
                    "empresa": empresa,
                    "tests_originales": tests_originales
                })
            except json.JSONDecodeError:
                continue 

        return pacientes_aeronautica
    except Exception as e:
        st.error(f"Error al buscar los pacientes de aeronáutica: {e}")
        return []
    finally:
        if connection:
            connection.close()

# --- Función para obtener TODOS los pacientes agendados hoy ---
@st.cache_data(ttl=300)
def fetch_todos_pacientes_hoy(sede):
    connection = get_mysql_connection()
    if not connection:
        return []

    sede_busqueda = sede
    if "SANTIAGO" in sede:
        sede_busqueda = "CENTRO DE SALUD WORKMED SANTIAGO"

    # Consulta amplia: Trae a todos los agendados hoy en la sede
    query = """
    SELECT datosPersona, prestacionesSalud
    FROM `agendaViewPrest`
    WHERE fecha = CURDATE() 
      AND nombre_lab LIKE %s
      AND prestacionesSalud IS NOT NULL
    """
    try:
        connection.ping(reconnect=True)
        with connection.cursor() as cursor:
            cursor.execute(query, (f"%{sede_busqueda}%",))
            results = cursor.fetchall()
        
        todos_pacientes = []
        
        for row in results:
            try:
                datos_persona = json.loads(row[0])
                empresa = datos_persona.get('nombre_contra', 'Empresa no especificada')
                
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

                todos_pacientes.append({
                    "rut": rut,
                    "nombre_completo": nombre_completo,
                    "empresa": empresa,
                    "tests_originales": tests_originales
                })
            except json.JSONDecodeError:
                continue 

        return todos_pacientes
    except Exception as e:
        st.error(f"Error al buscar el listado de pacientes: {e}")
        return []
    finally:
        if connection:
            connection.close()

# --- Función Genérica para obtener última asignación de una tabla específica ---
def get_latest_assignment_generic(supabase: Client, rut: str, table_name: str):
    today_str = date.today().isoformat()
    try:
        response = supabase.from_(table_name).select('tests_asignados').eq('rut', rut).gte('created_at', f'{today_str}T00:00:00').order('created_at', desc=True).limit(1).execute()
        if response.data:
            return response.data[0].get('tests_asignados', [])
    except Exception:
        pass
    return None

# --- Helper para combinar tests originales con los de la tabla manual ---
def get_combined_assignment_manual(supabase: Client, rut: str, tests_originales: list):
    # Consulta a la nueva tabla 'asignaciones_manuales'
    manual_tests = get_latest_assignment_generic(supabase, rut, 'asignaciones_manuales')
    
    if manual_tests is not None:
        return manual_tests # Si hay registro manual, manda sobre la agenda
    else:
        return tests_originales # Si no, muestra lo de la agenda

# --- FUNCIONES PARA ESTADO DIARIO ---
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

@st.cache_data(ttl=60)
def fetch_progreso_tests(_supabase: Client, ruts: list):
    progreso = {rut: [] for rut in ruts}
    if not ruts: return progreso

    try:
        fichas_response = _supabase.from_('ficha_ingreso').select('id, rut').in_('rut', ruts).execute()
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

    # --- PESTAÑA 2: ASIGNACIÓN AERONÁUTICA (Tabla: asignaciones_aeronautica) ---
    with tab2:
        st.header("Asignación Manual para Aeronáutica")
        st.write("Listado de pacientes agendados hoy bajo perfil 'Aeronáutica' en su sede.")
        
        sedes_psicologo = st.session_state.get("user_sedes", [])
        if not sedes_psicologo:
            st.error("No tiene sedes asignadas. Por favor, contacte a un administrador.")
        else:
            sede_seleccionada = sedes_psicologo[0]
            if len(sedes_psicologo) > 1:
                sede_seleccionada = st.selectbox("Seleccione una sede:", options=sedes_psicologo, key="sede_psicologo_aero")

            pacientes_aeronautica = fetch_aeronautica_hoy(sede_seleccionada)

            if not pacientes_aeronautica:
                st.info("No se encontraron pacientes de aeronáutica agendados para hoy en esta sede.")
            else:
                st.success(f"Se encontraron {len(pacientes_aeronautica)} pacientes de aeronáutica.")
                
                for idx, paciente in enumerate(pacientes_aeronautica):
                    rut_p = paciente['rut']
                    nombre_p = paciente['nombre_completo']
                    
                    # Consulta tabla específica de aeronautica
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

    # --- PESTAÑA 3: AGENDAMIENTO MANUAL (Tabla: asignaciones_manuales) ---
    with tab3:
        st.header("Agendamiento Manual de Pacientes (Todos)")
        st.write("Listado de pacientes agendados hoy con prestaciones de Salud Mental. Use el buscador para filtrar.")

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
                todos_pacientes = fetch_todos_pacientes_hoy(sede_manual)
            
            if rut_filter:
                pacientes_filtrados = [p for p in todos_pacientes if rut_filter in p['rut']]
            else:
                pacientes_filtrados = todos_pacientes

            if not pacientes_filtrados:
                st.info("No se encontraron pacientes con prestaciones de salud mental agendados para hoy (o que coincidan con el filtro).")
            else:
                st.info(f"Mostrando {len(pacientes_filtrados)} pacientes agendados hoy en {sede_manual}.")
                
                for idx, paciente in enumerate(pacientes_filtrados):
                    rut_p = paciente['rut']
                    nombre_p = paciente['nombre_completo']
                    tests_originales_p = paciente.get('tests_originales', [])

                    # Combina asignaciones manuales (tabla nueva) con agenda
                    assigned_tests = get_combined_assignment_manual(supabase, rut_p, tests_originales_p)
                    
                    expander_title = f"**{nombre_p}** - {rut_p}"
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
                                # Guardar en 'asignaciones_manuales' (prioridad máxima)
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
                                
    # --- PESTAÑA 4: ESTADO DIARIO (NUEVA) ---
    with tab4:
        st.header("Estado Diario de Pacientes")
        st.write("Monitoreo en tiempo real del progreso de evaluaciones de hoy.")

        sedes_diario = st.session_state.get("user_sedes", [])
        if not sedes_diario:
            st.error("No tiene sedes asignadas.")
        else:
            sede_d = sedes_diario[0]
            if len(sedes_diario) > 1: sede_d = st.selectbox("Sede:", sedes_diario, key="sede_diario_psi")
            
            if st.button("🔄 Actualizar Tabla", key="refresh_diario_psi"):
                st.cache_data.clear()
                st.rerun()

            with st.spinner("Cargando datos..."):
                # 1. Traer todos los pacientes de hoy (usando la misma lógica de agendamiento manual)
                pacientes = fetch_todos_pacientes_hoy(sede_d)
                # 2. Traer quiénes ya iniciaron ficha
                iniciados = fetch_iniciados_hoy(supabase, sede_d)
                # 3. Traer progreso de tests
                progreso = fetch_progreso_tests(supabase, [p['rut'] for p in pacientes])

            if not pacientes:
                st.info("No hay pacientes agendados hoy.")
            else:
                # Construir DataFrame
                rows = []
                stats = {"Pendiente": 0, "En Progreso": 0, "Finalizado": 0}
                
                for p in pacientes:
                    rut = p['rut']
                    # Determinar tests finales (Agenda + Manuales)
                    tests_finales = get_combined_assignment_manual(supabase, rut, p['tests_originales'])
                    tests_hechos = set(progreso.get(rut, []))
                    
                    estado = "🟡 Pendiente"
                    if rut in iniciados:
                        # Si tiene tests asignados y los completó todos
                        if tests_finales and tests_hechos.issuperset(set(tests_finales)):
                            estado = "✅ Finalizado"
                        else:
                            estado = "🔵 En Progreso"
                    
                    # --- CORRECCIÓN APLICADA: Mapeo directo sin .split() ---
                    if "Pendiente" in estado:
                        stats["Pendiente"] += 1
                    elif "En Progreso" in estado:
                        stats["En Progreso"] += 1
                    elif "Finalizado" in estado:
                        stats["Finalizado"] += 1
                    
                    # Detalle de tests (Visualización compacta)
                    detalle_tests = []
                    for t in tests_finales:
                        icon = "✅" if t in tests_hechos else "⏳"
                        detalle_tests.append(f"{icon} {t}")
                    
                    rows.append({
                        "RUT": rut,
                        "Nombre": p['nombre_completo'],
                        "Estado": estado,
                        "Tests Asignados": ", ".join(detalle_tests) if detalle_tests else "Sin asignación"
                    })
                
                # Mostrar Métricas
                c1, c2, c3 = st.columns(3)
                c1.metric("Pendientes", stats["Pendiente"])
                c2.metric("En Progreso", stats["En Progreso"])
                c3.metric("Finalizados", stats["Finalizado"])
                
                st.dataframe(pd.DataFrame(rows), use_container_width=True)