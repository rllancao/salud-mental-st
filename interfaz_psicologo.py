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

# --- Función para buscar pacientes de aeronáutica ---
@st.cache_data(ttl=300)
def fetch_aeronautica_hoy(sede):
    connection = connect_to_mysql()
    if not connection:
        return []

    sede_busqueda = sede
    if "SANTIAGO" in sede:
        sede_busqueda = "CENTRO DE SALUD WORKMED SANTIAGO"

    query = """
    SELECT datosPersona
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
            datos_persona = json.loads(row[0])
            nombre_completo = " ".join(filter(None, [
                datos_persona.get('nombre', '').strip(),
                datos_persona.get('nombre2', '').strip(),
                datos_persona.get('apellidoP', '').strip(),
                datos_persona.get('apellidoM', '').strip()
            ]))
            pacientes_aeronautica.append({
                "rut": datos_persona.get('rut'),
                "nombre_completo": nombre_completo
            })
        return pacientes_aeronautica
    except Exception as e:
        st.error(f"Error al buscar los pacientes de aeronáutica: {e}")
        return []

# --- Función para obtener la última asignación de un paciente ---
def get_latest_assignment(supabase: Client, rut: str):
    today_str = date.today().isoformat()
    response = supabase.from_('asignaciones_aeronautica').select('tests_asignados').eq('rut', rut).gte('created_at', f'{today_str}T00:00:00').order('created_at', desc=True).limit(1).execute()
    if response.data:
        return response.data[0].get('tests_asignados', [])
    return []


def crear_interfaz_psicologo(supabase: Client):
    st.title("Panel del Psicólogo")
    
    tab1, tab2 = st.tabs(["Búsqueda de Informes", "Asignación Manual para Aeronáutica"])

    with tab1:
        st.header("Búsqueda y Descarga de Informes de Pacientes")
        st.write("Ingrese el RUT del paciente para buscar todos sus informes de salud mental asociados.")
        rut_busqueda = st.text_input("RUT del Paciente", placeholder="Ej. 12345678-9", key="rut_busqueda_psicologo")

        if st.button("Buscar Informes"):
            if not rut_busqueda:
                st.warning("Por favor, ingrese un RUT para buscar.")
            else:
                with st.spinner("Buscando todos los informes del paciente..."):
                    try:
                        todos_los_paths = set()
                        nombre_paciente = ""

                        # 1. Buscar en 'registros_fichas_sm'
                        fichas_response = supabase.from_('registros_fichas_sm').select('nombre_completo, pdf_path').eq('rut', rut_busqueda).execute()
                        if fichas_response.data:
                            if not nombre_paciente:
                                nombre_paciente = fichas_response.data[0]['nombre_completo']
                            for ficha in fichas_response.data:
                                if ficha.get('pdf_path'):
                                    todos_los_paths.add(ficha['pdf_path'])
                        
                        # 2. Buscar en las tablas de tests
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

                        # 3. Procesar y mostrar los informes únicos
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
                                    st.download_button(label=f"Descargar {tipo_informe}", data=pdf_bytes, file_name=nombre_archivo, mime="application/pdf", key=path)
                                    st.markdown("---")
                                except Exception as download_error:
                                    st.error(f"No se pudo descargar el archivo '{nombre_archivo}': {download_error}")
                        else:
                            st.warning(f"No se encontró ningún informe para el RUT: {rut_busqueda}")
                    except Exception as db_error:
                        st.error(f"Error al consultar la base de datos: {db_error}")

    with tab2:
        st.header("Asignación Manual para Aeronáutica")
        st.write("Aquí puede asignar tests específicos a los pacientes de aeronáutica agendados para hoy.")
        
        sedes_psicologo = st.session_state.get("user_sedes", [])
        if not sedes_psicologo:
            st.error("No tiene sedes asignadas. Por favor, contacte a un administrador.")
        else:
            sede_seleccionada = sedes_psicologo[0]
            if len(sedes_psicologo) > 1:
                sede_seleccionada = st.selectbox("Seleccione una sede:", options=sedes_psicologo, key="sede_psicologo")

            pacientes_aeronautica = fetch_aeronautica_hoy(sede_seleccionada)

            if not pacientes_aeronautica:
                st.info("No se encontraron pacientes de aeronáutica agendados para hoy.")
            else:
                st.success(f"Se encontraron {len(pacientes_aeronautica)} pacientes de aeronáutica.")
                
                for paciente in pacientes_aeronautica:
                    # --- MEJORA: Se obtienen los tests asignados ANTES de crear el expander ---
                    assigned_tests = get_latest_assignment(supabase, paciente['rut'])
                    
                    # Se crea el título del expander dinámicamente
                    expander_title = f"**{paciente['nombre_completo']}** - {paciente['rut']}"
                    if assigned_tests:
                        expander_title += f"  (Asignados: {', '.join(assigned_tests)})"
                    
                    with st.expander(expander_title):
                        st.write("Seleccione los tests a asignar:")
                        
                        cols = st.columns(3)
                        selected_tests = []
                        
                        for i, test in enumerate(TESTS_SALUD_MENTAL):
                            # Se reutiliza la variable 'assigned_tests' para marcar los checkboxes
                            is_checked = cols[i % 3].checkbox(test, value=(test in assigned_tests), key=f"{paciente['rut']}_{test}")
                            if is_checked:
                                selected_tests.append(test)
                        
                        if st.button("Guardar Asignación", key=f"guardar_{paciente['rut']}"):
                            if not selected_tests:
                                st.warning("Debe seleccionar al menos un test.")
                            else:
                                try:
                                    response = supabase.from_('asignaciones_aeronautica').insert({
                                        'rut': paciente['rut'],
                                        'tests_asignados': selected_tests
                                    }).execute()
                                    if response.data:
                                        st.success(f"Asignación para {paciente['nombre_completo']} guardada con éxito.")
                                        st.rerun() 
                                    else:
                                        st.error(f"Error al guardar: {response.error.message if response.error else 'Error desconocido'}")
                                except Exception as e:
                                    st.error(f"Ocurrió una excepción al guardar: {e}")

