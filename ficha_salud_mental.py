import streamlit as st
from fpdf import FPDF
from datetime import datetime, date
from supabase import Client
import pymysql
import pandas as pd
import json

# --- NUEVO: Lista de tests de salud mental relevantes ---
TESTS_SALUD_MENTAL = [
    "EPWORTH", "DISC", "WONDERLIC", "ALERTA", "BARRATT", 
    "PBLL", "16 PF", "KOSTICK", "PSQI", "D-48", "WESTERN"
]

# --- Clase PDF ---
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
            self.set_x(10)
            self.cell(0, 7, f"- {key}: {value}", 0, 1)
        self.ln(5)

# --- Función para Normalizar Teléfono ---
def normalize_phone_number(phone_str):
    if not phone_str or not isinstance(phone_str, str):
        return ""
    digits = "".join(filter(str.isdigit, phone_str))
    if len(digits) > 9:
        potential_number = digits[-9:]
        if potential_number.startswith('9'):
            return potential_number
    elif len(digits) == 9 and digits.startswith('9'):
        return digits
    return ""

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

# --- Función para buscar datos del paciente (MODIFICADA) ---
@st.cache_data(ttl=600)
def fetch_patient_data(rut_paciente):
    connection = connect_to_mysql()
    if not connection:
        return None

    query = """
    SELECT datosPersona, nombre_lab, prestacionesSalud
    FROM `agendaViewPrest`
    WHERE fecha <= CURDATE() AND fecha > DATE_SUB(CURDATE(), INTERVAL 14 DAY)
    """
    try:
        df = pd.read_sql(query, connection)
        
        for index, row in df.iterrows():
            datos_persona = json.loads(row['datosPersona'])
            if datos_persona.get('rut') == rut_paciente:
                warnings = []
                
                fecha_nac_str = datos_persona.get('fecha_nac')
                edad = None
                if fecha_nac_str:
                    cleaned_date_str = fecha_nac_str.replace(" ", "").strip()
                    if cleaned_date_str and cleaned_date_str != '0000-00-00':
                        try:
                            fecha_nac = datetime.strptime(cleaned_date_str, '%Y-%m-%d')
                            edad = datetime.now().year - fecha_nac.year - ((datetime.now().month, datetime.now().day) < (fecha_nac.month, fecha_nac.day))
                        except ValueError:
                            warnings.append("Fecha de Nacimiento (formato inválido)")
                
                nombre_completo = " ".join(filter(None, [datos_persona.get('nombre', '').strip(), datos_persona.get('nombre2', '').strip(), datos_persona.get('apellidoP', '').strip(), datos_persona.get('apellidoM', '').strip()]))
                telefono_normalizado = normalize_phone_number(datos_persona.get('telefono', '').strip())
                if not telefono_normalizado:
                    warnings.append("Teléfono (formato inválido)")

                correo = datos_persona.get('correo', '').strip()
                if correo and '@' not in correo:
                    warnings.append("Correo Electrónico (formato inválido)")
                    correo = "" 

                empresa = datos_persona.get('nombre_contra', '').strip()
                cargo = datos_persona.get('cargo', '').strip()
                sucursal = row.get('nombre_lab', '').strip()
                
                # --- CAMBIO CLAVE: Filtrar las prestaciones para quedarnos solo con las de salud mental ---
                prestaciones_str = row.get('prestacionesSalud')
                tests_filtrados = []
                if prestaciones_str:
                    try:
                        lista_prestaciones_raw = json.loads(prestaciones_str)
                        # Iteramos y comparamos en mayúsculas para evitar errores de case
                        for prestacion in lista_prestaciones_raw:
                            for test_valido in TESTS_SALUD_MENTAL:
                                if test_valido in prestacion.upper():
                                    if test_valido not in tests_filtrados: # Evita duplicados
                                        tests_filtrados.append(test_valido) # Guardamos el nombre normalizado
                    except (json.JSONDecodeError, TypeError):
                        warnings.append("Prestaciones de Salud (formato inválido)")

                patient_data = {
                    "nombre_completo": nombre_completo, "rut": datos_persona.get('rut'),
                    "edad": edad, "telefono": telefono_normalizado,
                    "correo": correo, "empresa": empresa,
                    "cargo": cargo, "sucursal_workmed": sucursal
                }
                
                return {"data": patient_data, "warnings": warnings, "tests": tests_filtrados}
        return "not_found"
    except Exception as e:
        st.error(f"Error al buscar los datos del paciente: {e}")
        return None

# --- Función para generar PDF ---
def generar_pdf(form_data, wonderlic_data = None, disc_data = None):
    if not form_data: return b''
    
    pdf_data = form_data.copy()
    
    fecha_vencimiento = pdf_data.get("fecha_vencimiento_licencia")
    if isinstance(fecha_vencimiento, date):
        pdf_data["fecha_vencimiento_licencia"] = fecha_vencimiento.strftime("%d-%m-%Y")
    else:
        pdf_data["fecha_vencimiento_licencia"] = "N/A"

    pdf = PDF()
    pdf.add_page()
    
    pdf.chapter_title("Datos Personales")
    pdf.create_table_section({
        "Nombre Completo": pdf_data.get("nombre_completo"), "RUT": pdf_data.get("rut"),
        "Edad": pdf_data.get("edad"), "Teléfono": pdf_data.get("telefono"),
        "Correo": pdf_data.get("correo"), "Empresa": pdf_data.get("empresa"),
        "Sucursal Workmed": pdf_data.get("sucursal_workmed"), "Cargo": pdf_data.get("cargo"),
    })
    
    pdf.chapter_title("Antecedentes Académicos y Laborales")
    pdf.create_table_section({
        "Tipo de Licencia": pdf_data.get("tipo_licencia"),
        "Fecha de Vencimiento de Licencia": pdf_data.get("fecha_vencimiento_licencia"),
        "Experiencia Laboral": pdf_data.get("experiencia"), "Educación": pdf_data.get("educacion"),
    })

    pdf.chapter_title("Antecedentes Personales y Salud")
    pdf.create_table_section({
        "Red de Apoyo": pdf_data.get("red_apoyo"), "Horas de Sueño": pdf_data.get("horas_sueño"),
        "Tratamiento Psicológico/Psiquiátrico": pdf_data.get("tratamiento"),
        "Fortaleza": pdf_data.get("fortaleza"), "Debilidad": pdf_data.get("debilidad"),
    })

    pdf.chapter_title("Antecedentes de Seguridad y Prevención")
    pdf.create_table_section({
        "Elementos de Protección Personal": pdf_data.get("elementos_proteccion"),
        "Estrategia de Prevención de Accidentes": pdf_data.get("estrategia_prev_accidente"),
        "Riesgos en el Trabajo": pdf_data.get("riesgos_trabajo"),
        "Accidentes Laborales Anteriores": pdf_data.get("accidentes_laborales"),
    })
    
    # --- CAMBIO CLAVE: Añadir sección de resultados Wonderlic si existen ---
    if wonderlic_data:
        pdf.add_page()
        pdf.chapter_title("Resultados Test de Habilidad Cognitiva (Wonderlic)")

        # Calcular el puntaje total
        if 15 <= pdf_data.get("edad") <= 29:
            total_score = sum(v for k, v in wonderlic_data.items() if k.startswith('pregunta_'))
        elif 30 <= pdf_data.get("edad") <= 39:
            total_score = sum(v for k, v in wonderlic_data.items() if k.startswith('pregunta_')) + 1
        elif 40 <= pdf_data.get("edad") <= 49:
            total_score = sum(v for k, v in wonderlic_data.items() if k.startswith('pregunta_')) + 2
        elif 50 <= pdf_data.get("edad") <= 54:
            total_score = sum(v for k, v in wonderlic_data.items() if k.startswith('pregunta_')) + 3
        elif 55 <= pdf_data.get("edad") <= 60:
            total_score = sum(v for k, v in wonderlic_data.items() if k.startswith('pregunta_')) + 4
        else:
            total_score = sum(v for k, v in wonderlic_data.items() if k.startswith('pregunta_')) + 5
 
        # Determinar la interpretación del puntaje
        interpretacion = ""
        if total_score <= 15:
            interpretacion = "Personas que poseen una capacidad regular para desarrollar actividades nuevas, sin embargo, logran desempeñar tareas rutinarias y monótonas con éxito. Pueden operar equipos de fácil manejo sin inconvenientes. Se recomienda de supervisión inicial en cargos nuevos, con el fin de facilitar el desempeño favorable y positivo."
        elif 16 <= total_score <= 19:
            interpretacion = "Personas capaces de desarrollar actividades simples sin dificultades. Con habilidades para desempeñarse en tareas repetitivas con efectividad, manteniendo un ritmo estable de trabajo. Frente a la toma de decisiones más complejas, es probable que se apoyen de sus compañeros de trabajo o de jefaturas. Tienen bastante éxito en situaciones elementales dentro del trabajo."
        elif 20 <= total_score <= 24:
            interpretacion = "Logran aprender rutinas de trabajo rápidamente contando con una buena capacidad para desarrollarse en tareas de mediana complejidad. En este sentido, tienden a apoyarse de materiales escritos y de experiencias pasadas. Podrían eventualmente pedir ayuda frente a problemas más complejos y tomar decisiones importantes."
        elif 25 <= total_score <= 34:
            interpretacion = "Cuentan con una muy buena capacidad para aprender por su cuenta, pueden recopilar información para tomar decisiones con poca o escasa ayuda. Poseen habilidades para analizar los problemas que se les presentan con un número limitado de  alternativas."
        else: # >= 35
            interpretacion = "Personas capaces de reunir y sintetizar información fácilmente, pueden inferir información y llegar a conclusiones sobre sus situaciones de trabajo. Poseen excelentes habilidades para solucionar problemas. Son de aprendizaje rápido y tienen mucha facilidad para tomar decisiones cuando falta información. "

        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, f"Puntaje Total Obtenido: {total_score} / 50", 0, 1)
        pdf.set_font('Arial', '', 10)
        pdf.multi_cell(0, 7, f"Interpretación: {interpretacion}")
        
        if disc_data:
            # No se añade página nueva para que continúe en la misma hoja si cabe
            pdf.ln(10) # Espacio antes de la nueva sección
            pdf.chapter_title("Resultados Test de Comportamiento (DISC)")

            profile_name = disc_data.get("profile_name", "No determinado")
            profile_details = disc_data.get("profile_details", {})

            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 10, f"Perfil de Personalidad: {profile_name}", 0, 1)
            
            if profile_details:
                pdf.set_font('Arial', '', 10)
                for key, value in profile_details.items():
                    if value: # Solo mostrar si hay contenido
                        pdf.set_font('Arial', 'B', 10)
                        # Usamos multi_cell para las claves y valores por si son largos
                        pdf.multi_cell(0, 5, f"{key.replace('_', ' ').title()}:")
                        pdf.set_font('Arial', '', 10)
                        pdf.multi_cell(0, 5, str(value))
                        pdf.ln(2) # Espacio entre cada característica
    
    return pdf.output(dest='S').encode('latin1')


# --- Interfaz de usuario (paciente) ---
def crear_interfaz_paciente(supabase: Client):
    st.title("Paso 1: Ficha de Ingreso Salud Mental")
    st.write("Por favor, ingrese su RUT para cargar sus datos y luego complete el resto del formulario.")

    if 'datos_paciente' not in st.session_state:
        st.session_state.datos_paciente = {}

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
                    
                    warnings = response.get("warnings", [])
                    st.success("¡Datos encontrados y cargados!")
                    if warnings:
                        st.warning("Por favor, revise y complete manualmente los siguientes campos: " + ", ".join(warnings) + ".")
                elif response == "not_found":
                    st.warning("RUT no encontrado. Por favor, complete el formulario manualmente.")
                    st.session_state.datos_paciente = {}
                else:
                    st.error("Ocurrió un error al buscar los datos.")
        else:
            st.warning("Por favor, ingrese un RUT.")

    with st.form(key="salud_mental_form"):
        st.header("Datos Personales")
        nombre_completo = st.text_input("Nombre Completo", value=st.session_state.datos_paciente.get("nombre_completo", ""))
        rut = st.text_input("RUT", value=st.session_state.datos_paciente.get("rut", rut_a_buscar))
        edad_val = st.session_state.datos_paciente.get("edad")
        edad = st.number_input("Edad", min_value=18, max_value=100, value=int(edad_val) if edad_val is not None else 18)
        telefono = st.text_input("Teléfono", value=st.session_state.datos_paciente.get("telefono", ""))
        correo = st.text_input("Correo Electrónico", value=st.session_state.datos_paciente.get("correo", ""))
        empresa = st.text_input("Empresa", value=st.session_state.datos_paciente.get("empresa", ""))
        
        sucursales_options = ["CENTRO DE SALUD WORKMED SANTIAGO", "CENTRO DE SALUD WORKMED ANTOFAGASTA", "CENTRO DE SALUD WORKMED CALAMA", "LOS ANDES (VIDA SALUD )", "CENTRO DE SALUD WORKMED SANTIAGO PISO 6", "CENTRO DE SALUD WORKMED CONCEPCION", "CENTRO DE SALUD WORKMED CALAMA GRANADEROS", "CENTRO DE SALUD WORKMED COPIAPÓ", "CENTRO DE SALUD WORKMED VIÑA DEL MAR", "CENTRO DE SALUD WORKMED IQUIQUE", "CENTRO DE SALUD WORKMED RANCAGUA", "CENTRO DE SALUD WORKMED LA SERENA", "CENTRO DE SALUD WORKMED TERRENO", "CENTRO DE SALUD WORKMED TELECONSULTA","CENTRO DE SALUD WORKMED AREQUIPA", "PERÚ", "CENTRO DE SALUD WORKMED DIEGO DE ALMAGRO", "CENTRO DE SALUD WORKMED COPIAPÓ (VITALMED)", "CENTRO DE SALUD WORKMED ARICA", "CENTRO DE SALUD WORKMED - BIONET CURICO", "CENTRO DE SALUD WORKMED - BIONET RENGO", "CENTRO DE SALUD WORKMED PUERTO MONTT", "WORKMED ITINERANTE", "CENTRO DE SALUD WORKMED - BIONET TALCA", "CENTRO DE SALUD WORKMED - BIONET TOCOPILLA", "CENTRO DE SALUD WORKMED - BIONET QUILLOTA", "CENTRO DE SALUD WORKMED - BIONET SAN ANTONIO", "CENTRO DE SALUD WORKMED - BIONET OVALLE", "CENTRO DE SALUD WORKMED - BIONET ILLAPEL", "CENTRO DE SALUD WORKMED SAN FELIPE", "CENTRO DE SALUD WORKMED - BIONET SALAMANCA", "CENTRO DE SALUD WORKMED - BIONET VIÑA DEL MAR", "CENTRO DE SALUD WORKMED - BIONET LOS ANDES", "CENTRO DE SALUD WORKMED - BIONET VALDIVIA", "CENTRO DE SALUD WORKMED - BIONET IQUIQUE", "CENTRO DE SALUD WORKMED PUNTA ARENAS"]
        sucursal_encontrada = st.session_state.datos_paciente.get("sucursal_workmed")
        if sucursal_encontrada and sucursal_encontrada not in sucursales_options:
            sucursales_options.insert(0, sucursal_encontrada)
        default_index = sucursales_options.index(sucursal_encontrada) if sucursal_encontrada in sucursales_options else 0
        sucursal_workmed = st.selectbox("Sucursal Workmed", sucursales_options, index=default_index)
        
        cargo = st.text_input("Cargo", value=st.session_state.datos_paciente.get("cargo", ""))

        st.header("Antecedentes Académicos y Laborales")
        tipos_licencia_opciones = ["D", "B", "A1", "A2", "A3", "A4", "A5", "Otras", "No tengo Licencia de conducir"]
        tipo_licencia = st.multiselect("Tipo de Licencia", tipos_licencia_opciones)
        fecha_vencimiento_licencia = st.date_input("Fecha de Vencimiento de Licencia", value=None)
        experiencia = st.selectbox("Experiencia Laboral", ["No tengo experiencia", "Menos de 2 años", "Entre 2 y 5 años", "Más de 5 años ", "Más de 20 años"])
        educacion = st.selectbox("Educación", ["Educación básica completa", "Educación media completa", "Educación de nivel técnico superior completo", "Educación de nivel universitario completo", "Educación técnico nivel medio completo"])

        st.header("Antecedentes Personales y Salud")
        red_apoyo = st.selectbox("Red de Apoyo", ["Familia", "Hijos", "Amigos", "No tengo redes de apoyo"])
        horas_sueño = st.selectbox("Horas de Sueño", ["Menos de 6 horas", "Entre 6 y 8 horas", "Más de 8 horas"])
        tratamiento = st.text_area("Tratamiento Psicológico/Psiquiátrico (Si lo posee)")
        fortaleza = st.text_area("Fortaleza")
        debilidad = st.text_area("Debilidad")

        st.header("Antecedentes de Seguridad y Prevención")
        elementos_proteccion = st.text_area("Elementos de Protección Personal que utiliza en su trabajo")
        estrategia_prev_accidente = st.text_area("Estrategia de Prevención de Accidentes que conoce o aplica")
        riesgos_trabajo = st.text_area("Riesgos en el Trabajo")
        accidentes_laborales = st.text_area("Accidentes Laborales Anteriores (describir brevemente)")

        siguiente_button = st.form_submit_button("Siguiente")

        if siguiente_button:
            if not all([nombre_completo, rut, edad, telefono, correo, empresa, cargo]):
                st.error("Por favor, complete todos los campos obligatorios.")
            else:
                st.session_state.form_data['ficha_ingreso'] = {
                    "nombre_completo": nombre_completo, "rut": rut, "edad": edad, "telefono": telefono,
                    "correo": correo, "empresa": empresa, "sucursal_workmed": sucursal_workmed, "cargo": cargo,
                    "tipo_licencia": ", ".join(tipo_licencia), "fecha_vencimiento_licencia": fecha_vencimiento_licencia, 
                    "experiencia": experiencia, "educacion": educacion, "red_apoyo": red_apoyo,
                    "horas_sueño": horas_sueño, "tratamiento": tratamiento, "fortaleza": fortaleza,
                    "debilidad": debilidad, "elementos_proteccion": elementos_proteccion,
                    "estrategia_prev_accidente": estrategia_prev_accidente, "riesgos_trabajo": riesgos_trabajo,
                    "accidentes_laborales": accidentes_laborales,
                }
                st.session_state.step = "test" 
                st.rerun()

