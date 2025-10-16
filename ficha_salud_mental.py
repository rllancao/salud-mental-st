import streamlit as st
from supabase import Client
import pymysql
import pandas as pd
import json
from datetime import datetime, date
from fpdf import FPDF

TESTS_SALUD_MENTAL = [
    "EPWORTH", "DISC", "WONDERLIC", "ALERTA", "BARRATT", 
    "PBLL", "16 PF", "KOSTICK", "PSQI", "D-48", "WESTERN"
]

class PDF(FPDF):
    def header(self):
        self.image('workmed_logo.png', x=10, y=8, w=40)
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, 'Ficha de Ingreso Salud Mental', 0, 1, 'C')
        self.ln(10)

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(4)

    def create_table_section(self, data):
        self.set_font('Arial', '', 10)
        for key, value in data.items():
            # Asegurarse que el valor no sea None para evitar errores
            display_value = str(value) if value is not None else "N/A"
            self.set_x(10)
            self.cell(0, 7, f"- {key}: {display_value}", 0, 1)
        self.ln(5)

def normalize_phone_number(phone_str):
    if not phone_str or not isinstance(phone_str, str): return ""
    digits = "".join(filter(str.isdigit, phone_str))
    if len(digits) > 9 and digits.startswith('569'): return digits[-9:]
    elif len(digits) == 9 and digits.startswith('9'): return digits
    return ""

@st.cache_resource
def connect_to_mysql():
    try:
        connection = pymysql.connect(
            host=st.secrets["mysql"]["host"], user=st.secrets["mysql"]["user"],
            password=st.secrets["mysql"]["password"], database=st.secrets["mysql"]["database"],
            port=st.secrets["mysql"]["port"]
        )
        return connection
    except Exception as e:
        st.error(f"No se pudo conectar a la base de datos de WorkmedFlow: {e}")
        return None

@st.cache_data(ttl=600)
def fetch_patient_data(rut_paciente):
    connection = connect_to_mysql()
    if not connection: return None
    query = "SELECT datosPersona, nombre_lab, prestacionesSalud FROM `agendaViewPrest` WHERE fecha <= CURDATE() AND fecha > DATE_SUB(CURDATE(), INTERVAL 14 DAY)"
    try:
        df = pd.read_sql(query, connection)
        for _, row in df.iterrows():
            datos_persona = json.loads(row['datosPersona'])
            if datos_persona.get('rut') == rut_paciente:
                warnings, tests_filtrados = [], []
                fecha_nac_str = datos_persona.get('fecha_nac')
                edad = None
                if fecha_nac_str and "0000-00-00" not in fecha_nac_str:
                    try:
                        fecha_nac = datetime.strptime(fecha_nac_str.strip(), '%Y-%m-%d')
                        edad = (datetime.now() - fecha_nac).days // 365
                    except ValueError: warnings.append("Fecha de Nacimiento (formato inválido)")
                
                nombre_completo = " ".join(filter(None, [datos_persona.get('nombre', ''), datos_persona.get('nombre2', ''), datos_persona.get('apellidoP', ''), datos_persona.get('apellidoM', '')])).strip()
                telefono = normalize_phone_number(datos_persona.get('telefono', ''))
                if not telefono: warnings.append("Teléfono (formato inválido)")
                
                correo = datos_persona.get('correo', '').strip()
                if correo and '@' not in correo:
                    warnings.append("Correo (formato inválido)")
                    correo = ""
                
                prestaciones_str = row.get('prestacionesSalud')
                if prestaciones_str:
                    try:
                        lista_prestaciones_raw = json.loads(prestaciones_str)
                        for prestacion in lista_prestaciones_raw:
                            for test in TESTS_SALUD_MENTAL:
                                if test in prestacion.upper() and test not in tests_filtrados:
                                    tests_filtrados.append(test)
                    except (json.JSONDecodeError, TypeError): pass

                return {
                    "data": {
                        "nombre_completo": nombre_completo, "rut": datos_persona.get('rut'), "edad": edad,
                        "telefono": telefono, "correo": correo, "empresa": datos_persona.get('nombre_contra', ''),
                        "cargo": datos_persona.get('cargo', ''), "sucursal_workmed": row.get('nombre_lab', '')
                    },
                    "warnings": warnings, "tests": tests_filtrados
                }
        return "not_found"
    except Exception as e:
        st.error(f"Error al buscar los datos del paciente: {e}")
        return None

def generar_pdf(form_data, wonderlic_data=None, disc_data=None):
    if not form_data: return b''
    pdf_data = form_data.copy()
    fecha_vencimiento = pdf_data.get("fecha_vencimiento_licencia")
    pdf_data["fecha_vencimiento_licencia"] = fecha_vencimiento if fecha_vencimiento else "N/A"

    pdf = PDF()
    pdf.add_page()
    
    personal_data = {k: pdf_data.get(k) for k in ["nombre_completo", "rut", "edad", "telefono", "correo", "empresa", "sucursal_workmed", "cargo"]}
    academic_data = {k: pdf_data.get(k) for k in ["tipo_licencia", "fecha_vencimiento_licencia", "experiencia", "educacion"]}
    health_data = {k: pdf_data.get(k) for k in ["red_apoyo", "horas_sueño", "tratamiento", "fortaleza", "debilidad"]}
    security_data = {k: pdf_data.get(k) for k in ["elementos_proteccion", "estrategia_prev_accidente", "riesgos_trabajo", "accidentes_laborales"]}

    pdf.chapter_title("Datos Personales"); pdf.create_table_section(personal_data)
    pdf.chapter_title("Antecedentes Académicos y Laborales"); pdf.create_table_section(academic_data)
    pdf.chapter_title("Antecedentes Personales y Salud"); pdf.create_table_section(health_data)
    pdf.chapter_title("Antecedentes de Seguridad y Prevención"); pdf.create_table_section(security_data)
    
    if wonderlic_data:
        pdf.add_page()
        pdf.chapter_title("Resultados Test de Habilidad Cognitiva (Wonderlic)")
        total_score_raw = sum(v for k, v in wonderlic_data.items() if k.startswith('pregunta_'))
        edad_paciente = personal_data.get("edad", 0)
        
        ajuste = 0
        if 30 <= edad_paciente <= 39: ajuste = 1
        elif 40 <= edad_paciente <= 49: ajuste = 2
        elif 50 <= edad_paciente <= 54: ajuste = 3
        elif 55 <= edad_paciente <= 60: ajuste = 4
        elif edad_paciente > 60: ajuste = 5
        total_score = total_score_raw + ajuste

        interpretacion = ""
        if total_score <= 15: interpretacion = "Capacidad regular para actividades nuevas, pero exitoso en tareas rutinarias."
        elif 16 <= total_score <= 19: interpretacion = "Capaz de desarrollar actividades simples y repetitivas con efectividad."
        elif 20 <= total_score <= 24: interpretacion = "Aprende rutinas rápidamente y se desempeña bien en tareas de mediana complejidad."
        elif 25 <= total_score <= 34: interpretacion = "Muy buena capacidad de autoaprendizaje y análisis de problemas."
        else: interpretacion = "Excelente capacidad para sintetizar información, solucionar problemas y aprender rápidamente."

        pdf.set_font('Arial', 'B', 12); pdf.cell(0, 10, f"Puntaje Total Obtenido: {total_score} / 50", 0, 1)
        pdf.set_font('Arial', '', 10); pdf.multi_cell(0, 7, f"Interpretación: {interpretacion}")

    if disc_data:
        pdf.ln(10)
        pdf.chapter_title("Resultados Test de Comportamiento (DISC)")
        pdf.set_font('Arial', 'B', 12); pdf.cell(0, 10, f"Perfil de Personalidad: {disc_data.get('profile_name', 'No determinado')}", 0, 1)
        
        profile_details = disc_data.get("profile_details", {})
        if profile_details:
            pdf.set_font('Arial', '', 10)
            for key, value in profile_details.items():
                if value:
                    pdf.set_font('Arial', 'B', 10); pdf.multi_cell(0, 5, f"{key.replace('_', ' ').title()}:")
                    pdf.set_font('Arial', '', 10); pdf.multi_cell(0, 5, str(value)); pdf.ln(2)
    
    return pdf.output(dest='S').encode('latin1')

def crear_interfaz_paciente(supabase: Client):
    st.title("Paso 1: Ficha de Ingreso Salud Mental")
    st.write("Por favor, ingrese su RUT para cargar sus datos y luego complete el resto del formulario.")

    if 'datos_paciente' not in st.session_state: st.session_state.datos_paciente = {}

    rut_a_buscar = st.text_input("Ingrese su RUT", placeholder="Ej. 12345678-9", help="Ingrese su RUT sin puntos y con guión.")
    if st.button("Buscar Datos"):
        if rut_a_buscar:
            with st.spinner("Buscando información..."):
                response = fetch_patient_data(rut_a_buscar)
                if response and response != "not_found":
                    st.session_state.datos_paciente = response.get("data", {})
                    st.session_state.lista_tests = response.get("tests", [])
                    st.session_state.current_test_index = 0
                    st.session_state.form_data = {}
                    st.success("¡Datos encontrados y cargados!")
                    if response.get("warnings"):
                        st.warning("Por favor, revise y complete: " + ", ".join(response["warnings"]) + ".")
                elif response == "not_found":
                    st.warning("RUT no encontrado. Por favor, complete el formulario manualmente.")
                    st.session_state.datos_paciente = {}
                else: st.error("Ocurrió un error al buscar los datos.")
        else: st.warning("Por favor, ingrese un RUT.")

    with st.form(key="salud_mental_form"):
        st.header("Datos Personales")
        nombre_completo = st.text_input("Nombre Completo", value=st.session_state.datos_paciente.get("nombre_completo", ""))
        rut = st.text_input("RUT", value=st.session_state.datos_paciente.get("rut", rut_a_buscar))
        edad = st.number_input("Edad", min_value=18, max_value=100, value=st.session_state.datos_paciente.get("edad") or 18)
        telefono = st.text_input("Teléfono", value=st.session_state.datos_paciente.get("telefono", ""))
        correo = st.text_input("Correo", value=st.session_state.datos_paciente.get("correo", ""))
        empresa = st.text_input("Empresa", value=st.session_state.datos_paciente.get("empresa", ""))
        
        sucursales_options = ["CENTRO DE SALUD WORKMED SANTIAGO", "CENTRO DE SALUD WORKMED ANTOFAGASTA", "CENTRO DE SALUD WORKMED CALAMA", "LOS ANDES (VIDA SALUD )", "CENTRO DE SALUD WORKMED SANTIAGO PISO 6", "CENTRO DE SALUD WORKMED CONCEPCION", "CENTRO DE SALUD WORKMED CALAMA GRANADEROS", "CENTRO DE SALUD WORKMED COPIAPÓ", "CENTRO DE SALUD WORKMED VIÑA DEL MAR", "CENTRO DE SALUD WORKMED IQUIQUE", "CENTRO DE SALUD WORKMED RANCAGUA", "CENTRO DE SALUD WORKMED LA SERENA", "CENTRO DE SALUD WORKMED TERRENO", "CENTRO DE SALUD WORKMED TELECONSULTA","CENTRO DE SALUD WORKMED AREQUIPA", "PERÚ", "CENTRO DE SALUD WORKMED DIEGO DE ALMAGRO", "CENTRO DE SALUD WORKMED COPIAPÓ (VITALMED)", "CENTRO DE SALUD WORKMED ARICA", "CENTRO DE SALUD WORKMED - BIONET CURICO", "CENTRO DE SALUD WORKMED - BIONET RENGO", "CENTRO DE SALUD WORKMED PUERTO MONTT", "WORKMED ITINERANTE", "CENTRO DE SALUD WORKMED - BIONET TALCA", "CENTRO DE SALUD WORKMED - BIONET TOCOPILLA", "CENTRO DE SALUD WORKMED - BIONET QUILLOTA", "CENTRO DE SALUD WORKMED - BIONET SAN ANTONIO", "CENTRO DE SALUD WORKMED - BIONET OVALLE", "CENTRO DE SALUD WORKMED - BIONET ILLAPEL", "CENTRO DE SALUD WORKMED SAN FELIPE", "CENTRO DE SALUD WORKMED - BIONET SALAMANCA", "CENTRO DE SALUD WORKMED - BIONET VIÑA DEL MAR", "CENTRO DE SALUD WORKMED - BIONET LOS ANDES", "CENTRO DE SALUD WORKMED - BIONET VALDIVIA", "CENTRO DE SALUD WORKMED - BIONET IQUIQUE", "CENTRO DE SALUD WORKMED PUNTA ARENAS"]
        sucursal_encontrada = st.session_state.datos_paciente.get("sucursal_workmed")
        if sucursal_encontrada and sucursal_encontrada not in sucursales_options:
            sucursales_options.insert(0, sucursal_encontrada)
        default_index = sucursales_options.index(sucursal_encontrada) if sucursal_encontrada and sucursal_encontrada in sucursales_options else 0
        sucursal_workmed = st.selectbox("Sucursal Workmed", sucursales_options, index=default_index)
        
        cargo = st.text_input("Cargo", value=st.session_state.datos_paciente.get("cargo", ""))

        st.header("Antecedentes Académicos y Laborales")
        tipo_licencia = st.multiselect("Tipo de Licencia", ["D", "B", "A1", "A2", "A3", "A4", "A5", "Otras", "No tengo"])
        fecha_vencimiento_licencia = st.date_input("Fecha Vencimiento Licencia", value=None, min_value=date(1950, 1, 1))
        experiencia = st.selectbox("Experiencia Laboral", ["No tengo", "Menos de 2 años", "2-5 años", "Más de 5 años", "Más de 20 años"])
        educacion = st.selectbox("Educación", ["Básica", "Media", "Técnico Nivel Medio", "Técnico Superior", "Universitaria"])

        st.header("Antecedentes Personales y Salud")
        red_apoyo = st.selectbox("Red de Apoyo", ["Familia", "Hijos", "Amigos", "No tengo"])
        horas_sueño = st.selectbox("Horas de Sueño", ["Menos de 6", "Entre 6 y 8", "Más de 8"])
        tratamiento = st.text_area("Tratamiento Psicológico/Psiquiátrico")
        fortaleza = st.text_area("Fortaleza")
        debilidad = st.text_area("Debilidad")

        st.header("Antecedentes de Seguridad y Prevención")
        elementos_proteccion = st.text_area("Elementos de Protección Personal que utiliza")
        estrategia_prev_accidente = st.text_area("Estrategia de Prevención de Accidentes que conoce")
        riesgos_trabajo = st.text_area("Riesgos en el Trabajo")
        accidentes_laborales = st.text_area("Accidentes Laborales Anteriores")

        siguiente_button = st.form_submit_button("Siguiente")

        if siguiente_button:
            if not all([nombre_completo, rut, edad, telefono, correo, empresa, cargo]):
                st.error("Por favor, complete todos los campos de datos personales.")
            else:
                form_data_to_save = {
                    "nombre_completo": nombre_completo, "rut": rut, "edad": edad, "telefono": telefono,
                    "correo": correo, "empresa": empresa, "sucursal_workmed": sucursal_workmed, "cargo": cargo,
                    "tipo_licencia": ", ".join(tipo_licencia), "fecha_vencimiento_licencia": str(fecha_vencimiento_licencia) if fecha_vencimiento_licencia else None, 
                    "experiencia": experiencia, "educacion": educacion, "red_apoyo": red_apoyo,
                    "horas_sueño": horas_sueño, "tratamiento": tratamiento, "fortaleza": fortaleza,
                    "debilidad": debilidad, "elementos_proteccion": elementos_proteccion,
                    "estrategia_prev_accidente": estrategia_prev_accidente, "riesgos_trabajo": riesgos_trabajo,
                    "accidentes_laborales": accidentes_laborales,
                }
                
                with st.spinner("Guardando y preparando el siguiente paso..."):
                    try:
                        response = supabase.from_('ficha_ingreso').insert(form_data_to_save).execute()
                        if response.data:
                            ficha_id = response.data[0]['id']
                            st.session_state.ficha_id = ficha_id
                            st.session_state.form_data['ficha_ingreso'] = form_data_to_save
                            st.session_state.step = "test"
                            
                            # --- NUEVO: Añadir ficha_id a la URL para persistencia ---
                            st.query_params["ficha_id"] = ficha_id
                            st.rerun()
                        else:
                            st.error(f"Hubo un error al guardar la ficha: {response.error.message if response.error else 'Error desconocido'}")
                    except Exception as e:
                        st.error(f"Ocurrió una excepción al guardar: {e}")

