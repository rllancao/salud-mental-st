import streamlit as st
from supabase import Client
import io
import pymysql
import json
from datetime import date

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

# --- Función para buscar pacientes de aeronáutica (Filtra por prestación) ---
@st.cache_data(ttl=300)
def fetch_aeronautica_hoy(sede):
    connection = connect_to_mysql()
    if not connection:
        return []

    sede_busqueda = sede
    if "SANTIAGO" in sede:
        sede_busqueda = "CENTRO DE SALUD WORKMED SANTIAGO"

    # Busca solo los que tienen EVALUACION SALUD MENTAL en sus prestaciones
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

# --- Función para obtener PACIENTES CON PRESTACIONES SM agendados hoy ---
@st.cache_data(ttl=300)
def fetch_todos_pacientes_hoy(sede):
    connection = connect_to_mysql()
    if not connection:
        return []

    sede_busqueda = sede
    if "SANTIAGO" in sede:
        sede_busqueda = "CENTRO DE SALUD WORKMED SANTIAGO"

    # Traemos pacientes de la sede que tengan ALGUNA prestación definida
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
        
        todos_pacientes = []
        
        for row in results:
            try:
                datos_persona = json.loads(row[0])
                prestaciones_str = row[1] or ""
                
                # Parsear prestaciones y filtrar: ¿Tiene algún test de salud mental?
                tests_originales = []
                tiene_prestacion_sm = False
                
                if prestaciones_str:
                    try:
                        lista_prest = json.loads(prestaciones_str)
                        for p in lista_prest:
                            # Chequeo 1: Si es explícitamente 'EVALUACION SALUD MENTAL' (caso aeronáutica o batería)
                            if 'EVALUACION SALUD MENTAL' in p.upper():
                                tiene_prestacion_sm = True
                            
                            # Chequeo 2: Si contiene alguno de los tests individuales definidos
                            for t in TESTS_SALUD_MENTAL:
                                if t in p.upper():
                                    tiene_prestacion_sm = True
                                    if t not in tests_originales:
                                        tests_originales.append(t)
                    except: pass 

                # SOLO AGREGAR SI TIENE PRESTACIONES DE SALUD MENTAL
                if tiene_prestacion_sm:
                    rut = datos_persona.get('rut')
                    nombre_completo = " ".join(filter(None, [
                        datos_persona.get('nombre', '').strip(),
                        datos_persona.get('nombre2', '').strip(),
                        datos_persona.get('apellidoP', '').strip(),
                        datos_persona.get('apellidoM', '').strip()
                    ]))

                    todos_pacientes.append({
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

def crear_interfaz_psicologo(supabase: Client):
    st.title("Panel del Psicólogo")
    
    tab1, tab2, tab3 = st.tabs(["Búsqueda de Informes", "Asignación Aeronáutica", "Agendamiento Manual"])

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

                        fichas_response = supabase.from_('registros_fichas_sm').select('nombre_completo, pdf_path').eq('rut', rut_busqueda).execute()
                        if fichas_response.data:
                            if not nombre_paciente:
                                nombre_paciente = fichas_response.data[0]['nombre_completo']
                            for ficha in fichas_response.data:
                                if ficha.get('pdf_path'):
                                    todos_los_paths.add(ficha['pdf_path'])
                        
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
            
            rut_filter = st.text_input("Filtrar por RUT:", placeholder="Ej. 12345678-9", key="rut_filter_manual").strip()
            
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
                                # --- CAMBIO CLAVE: Se guarda en 'asignaciones_manuales' ---
                                response = supabase.from_('asignaciones_manuales').insert({
                                    'rut': rut_p,
                                    'tests_asignados': selected_tests_m
                                }).execute()
                                
                                if response.data:
                                    st.success(f"¡Asignación actualizada para {nombre_p}!")
                                    st.cache_data.clear() 
                                else:
                                    st.error("Error al guardar en la base de datos.")
                            except Exception as e:
                                st.error(f"Error de conexión: {e}")