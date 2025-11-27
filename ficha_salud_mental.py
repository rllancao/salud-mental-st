import streamlit as st
from supabase import Client
import pymysql
import pandas as pd
import json
from datetime import datetime, date
from fpdf import FPDF
import io
from PIL import Image
import tempfile 
import os       

TESTS_SALUD_MENTAL = [
    "EPWORTH", "DISC", "WONDERLIC", "ALERTA", "BARRATT", 
    "PBLL", "16 PF", "KOSTICK", "PSQI", "D-48", "WESTERN", "EPQ-R"
]

class PDF(FPDF):
    def header(self):
        try:
            self.image('workmed_logo.png', x=10, y=8, w=40)
        except RuntimeError:
            pass
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
            display_value = str(value) if value is not None else "N/A"
            self.set_x(10)
            self.cell(0, 7, f"- {key}: {display_value}", 0, 1)
        self.ln(5)
        
    def show_kostick_factor(self, factor_name, factor_data_json):
        try:
            factor_data = json.loads(factor_data_json)
            descripcion = factor_data.get("descripcion", "N/A")
            observacion = factor_data.get("observacion", "N/A")

            self.set_font('Arial', 'B', 11)
            self.cell(0, 7, f"Factor {factor_name.upper()}: {descripcion}", 0, 1)
            self.set_font('Arial', '', 10)
            self.multi_cell(0, 5, f"Observación: {observacion}")
            self.ln(3) # Espacio entre factores
        except json.JSONDecodeError:
            self.set_font('Arial', 'I', 10)
            self.set_text_color(255, 0, 0)
            self.multi_cell(0, 5, f"Error al procesar datos del Factor {factor_name.upper()}")
            self.set_text_color(0, 0, 0) # Reset color
            self.ln(3)
            
    def draw_psqi_table(self, puntuaciones, resultado):
        self.set_font('Arial', 'B', 11)
        self.set_fill_color(0, 0, 139) # Azul oscuro
        self.set_text_color(255, 255, 255) # Texto blanco
        
        # Encabezado de la tabla de puntos
        self.cell(150, 10, "Tabla de puntos", 1, 0, 'L', 1)
        self.cell(40, 10, "Puntaje", 1, 1, 'C', 1)

        self.set_font('Arial', '', 10)
        self.set_text_color(0, 0, 0) # Texto negro
        self.set_fill_color(230, 230, 255) # Azul claro
        
        componentes = [
            "Calidad subjetiva del sueño", "Latencia del sueño", "Duración del sueño",
            "Eficiencia de sueño habitual", "Perturbaciones del sueño",
            "Uso de medicación hipnótica", "Disfunción diurna"
        ]
        
        fill = True
        for componente in componentes:
            puntaje = puntuaciones.get(componente, "N/A")
            self.cell(150, 8, componente, 1, 0, 'L', fill)
            self.cell(40, 8, str(puntaje), 1, 1, 'C', fill)
            fill = not fill # Alternar color de fondo

        # Sección de Puntaje Total
        self.ln(5)
        self.set_font('Arial', 'B', 11)
        self.set_fill_color(0, 0, 139) # Azul oscuro
        self.set_text_color(255, 255, 255) # Texto blanco
        self.cell(190, 10, "Puntaje Total", 1, 1, 'L', 1)

        self.set_font('Arial', '', 10)
        self.set_text_color(0, 0, 0) # Texto negro
        self.set_fill_color(230, 230, 255) # Azul claro
        
        self.cell(150, 8, "Total de puntos", 1, 0, 'L', 1)
        self.cell(40, 8, str(resultado.get("Puntaje Total", "N/A")), 1, 1, 'C', 1)
        self.cell(150, 8, "Descripción según puntaje", 1, 0, 'L', 0)
        self.cell(40, 8, resultado.get("Interpretacion", "N/A"), 1, 1, 'C', 0)
        
    def draw_16pf_table(self, interpretaciones, decatipos):
        self.set_font('Arial', 'B', 11)
        self.set_fill_color(200, 220, 255) # Azul claro
        self.set_text_color(0, 0, 0) # Texto negro

        self.cell(30, 10, "Factor", 1, 0, 'C', 1)
        self.cell(30, 10, "Decatipo", 1, 0, 'C', 1)
        self.cell(130, 10, "Interpretación", 1, 1, 'C', 1)

        self.set_font('Arial', '', 10)
        
        factores_primarios = ['A', 'B', 'C', 'E', 'F', 'G', 'H', 'I', 'L', 'M', 'N', 'O', 'Q1', 'Q2', 'Q3', 'Q4']
        
        for factor in factores_primarios:
            interp = interpretaciones.get(factor, "N/A")
            decatipo = decatipos.get(factor, "N/A")
            self.cell(30, 7, factor, 1, 0, 'C')
            self.cell(30, 7, str(decatipo), 1, 0, 'C')
            self.cell(130, 7, interp, 1, 1, 'L')
            
        # Factores secundarios (MI, IN, AQ)
        self.ln(5)
        self.set_font('Arial', 'B', 11)
        for factor in ['MI', 'IN', 'AQ']:
            interp = interpretaciones.get(factor, "N/A")
            decatipo = decatipos.get(factor, "N/A")
            self.cell(30, 7, factor, 1, 0, 'C')
            self.cell(30, 7, str(decatipo), 1, 0, 'C')
            self.cell(130, 7, interp, 1, 1, 'L')
            
    def draw_big_five_table(self, decatipos_big_five, interpretaciones_big_five):
        self.ln(5)
        self.set_font('Arial', 'B', 11)
        self.set_fill_color(50, 50, 50) # Gris oscuro
        self.set_text_color(255, 255, 255) # Texto blanco
        
        self.cell(50, 10, "Factor 'Big Five'", 1, 0, 'C', 1)
        self.cell(30, 10, "Decatipo", 1, 0, 'C', 1)
        self.cell(110, 10, "Interpretación", 1, 1, 'C', 1)
        
        self.set_font('Arial', '', 10)
        self.set_text_color(0, 0, 0)
        
        for factor, decatipo in decatipos_big_five.items():
            interp = interpretaciones_big_five.get(factor, "N/A")
            self.cell(50, 7, factor, 1, 0, 'L')
            self.cell(30, 7, str(decatipo), 1, 0, 'C')
            self.cell(110, 7, interp, 1, 1, 'L')

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
def fetch_patient_data(_supabase_client: Client, _rut_paciente):
    connection = connect_to_mysql()
    if not connection: return None
    query = "SELECT datosPersona, nombre_lab, prestacionesSalud FROM `agendaViewPrest` WHERE fecha <= CURDATE() AND fecha > DATE_SUB(CURDATE(), INTERVAL 14 DAY)"
    try:
        df = pd.read_sql(query, connection)
        for _, row in df.iterrows():
            datos_persona = json.loads(row['datosPersona'])
            if datos_persona.get('rut') == _rut_paciente:
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
                
                sexo = datos_persona.get('sexo', '').strip().upper()
                prestaciones_str = row.get('prestacionesSalud','') or ""
                
                # --- LÓGICA DE PRIORIDADES DE ASIGNACIÓN ---
                today_str = date.today().isoformat()
                
                # 1. Verificar si existe ASIGNACIÓN MANUAL (Nueva tabla) - Prioridad Alta
                manual_response = _supabase_client.from_('asignaciones_manuales').select('tests_asignados').eq('rut', _rut_paciente).gte('created_at', f'{today_str}T00:00:00').order('created_at', desc=True).limit(1).execute()
                
                tests_manuales = []
                if manual_response.data:
                    tests_manuales = manual_response.data[0].get('tests_asignados', [])
                
                if tests_manuales:
                    tests_filtrados = tests_manuales
                else:
                    # 2. Si no hay manual, verificar Aeronáutica (Tabla original) - Prioridad Media
                    is_aeronautica = 'evaluacion salud mental' in prestaciones_str.lower()
                    
                    if is_aeronautica:
                        aero_response = _supabase_client.from_('asignaciones_aeronautica').select('tests_asignados').eq('rut', _rut_paciente).gte('created_at', f'{today_str}T00:00:00').order('created_at', desc=True).limit(1).single().execute()
                        
                        if aero_response.data and aero_response.data.get('tests_asignados'):
                            tests_filtrados = aero_response.data['tests_asignados']
                        else:
                            warnings.append("Paciente de aeronáutica pendiente de asignación de tests por parte del psicólogo.")
                    else:
                        # 3. Si no hay nada, usar lo que viene de la agenda (MySQL) - Prioridad Baja
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
                        "cargo": datos_persona.get('cargo', ''), "sucursal_workmed": row.get('nombre_lab', ''),
                        "sexo": sexo
                    },
                    "warnings": warnings, "tests": tests_filtrados
                }
        return "not_found"
    except Exception as e:
        st.error(f"Error al buscar los datos del paciente: {e}")
        return None

# --- MODIFICADO: generar_pdf ahora solo muestra resultados ---
def generar_pdf(supabase_client: Client, form_data, wonderlic_data=None, disc_data=None, pbll_data=None, alerta_data=None,
                barratt_data=None, kostick_data=None, psqi_data=None, western_data=None, d48_data=None, _16pf_data=None) -> bytes:
    if not form_data: return b''
    pdf_data = form_data.copy()
    fecha_vencimiento = pdf_data.get("fecha_vencimiento_licencia")
    pdf_data["fecha_vencimiento_licencia"] = fecha_vencimiento if fecha_vencimiento else "N/A"

    pdf = PDF()
    pdf.add_page()
    
    personal_data = {k: pdf_data.get(k) for k in ["nombre_completo", "rut", "edad", "telefono", "correo", "empresa", "sucursal_workmed", "cargo", "sexo"]}
    academic_data = {k: pdf_data.get(k) for k in ["tipo_licencia", "fecha_vencimiento_licencia", "experiencia", "educacion"]}
    health_data = {k: pdf_data.get(k) for k in ["red_apoyo", "horas_sueño", "tratamiento", "fortaleza", "debilidad"]}
    security_data = {k: pdf_data.get(k) for k in ["elementos_proteccion", "estrategia_prev_accidente", "riesgos_trabajo", "accidentes_laborales"]}

    pdf.chapter_title("Datos Personales"); pdf.create_table_section(personal_data)
    pdf.chapter_title("Antecedentes Académicos y Laborales"); pdf.create_table_section(academic_data)
    pdf.chapter_title("Antecedentes Personales y Salud"); pdf.create_table_section(health_data)
    pdf.chapter_title("Antecedentes de Seguridad y Prevención"); pdf.create_table_section(security_data)
    
    # --- WONDERLIC ---
    if wonderlic_data:
        pdf.add_page()
        pdf.chapter_title("Resultados Test de Habilidad Cognitiva (Wonderlic)")
        # Se leen los resultados ya calculados desde el diccionario
        puntaje_total = wonderlic_data.get("puntaje_total", "N/A")
        interpretacion = wonderlic_data.get("interpretacion", "N/A")
        pdf.set_font('Arial', 'B', 12); pdf.cell(0, 10, f"Puntaje Total Obtenido: {puntaje_total} / 50", 0, 1)
        pdf.set_font('Arial', '', 10); pdf.multi_cell(0, 7, f"Interpretación: {interpretacion}")

    # --- DISC ---
    if disc_data:
        pdf.ln(10)
        pdf.chapter_title("Resultados Test de Comportamiento (DISC)")
        # Se leen los resultados ya calculados desde el diccionario
        perfil = disc_data.get('profile_name', 'No determinado')
        pdf.set_font('Arial', 'B', 12); pdf.cell(0, 10, f"Perfil de Personalidad: {perfil}", 0, 1)
        profile_details = disc_data.get("profile_details", {})
        # Mostrar detalles como antes
        if profile_details:
             pdf.set_font('Arial', '', 10)
             for key, value in profile_details.items():
                 if value:
                     pdf.set_font('Arial', 'B', 10); pdf.multi_cell(0, 5, f"{key.replace('_', ' ').title()}:")
                     pdf.set_font('Arial', '', 10); pdf.multi_cell(0, 5, str(value)); pdf.ln(2)
                    
    # --- ALERTA ---
    if alerta_data:
        pdf.add_page()
        pdf.chapter_title("Resultados Test de Alerta")
        # Se leen los resultados ya calculados desde el diccionario
        puntaje_total = alerta_data.get("puntaje_total", "N/A")
        interpretacion = alerta_data.get("interpretacion", "N/A")
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, f"Puntaje Total Obtenido: {puntaje_total} / 36", 0, 1)
        pdf.set_font('Arial', '', 10)
        pdf.multi_cell(0, 7, f"Interpretación: {interpretacion}")
        
    # --- BARRATT ---
    if barratt_data:
        pdf.add_page()
        pdf.chapter_title("Resultados Escala de Impulsividad de Barratt (BIS-11)")
        # Se leen los resultados ya calculados desde el diccionario
        pdf.create_table_section({
            "Impulsividad Cognitiva": f"{barratt_data.get('puntaje_cognitiva', 'N/A')} puntos (Nivel: {barratt_data.get('nivel_cognitiva', 'N/A')})",
            "Impulsividad Motora": f"{barratt_data.get('puntaje_motora', 'N/A')} puntos (Nivel: {barratt_data.get('nivel_motora', 'N/A')})",
            "Impulsividad No Planeada": f"{barratt_data.get('puntaje_no_planeada', 'N/A')} puntos (Nivel: {barratt_data.get('nivel_no_planeada', 'N/A')})",
        })
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, f"Puntaje Total de Impulsividad: {barratt_data.get('puntaje_total', 'N/A')} (Nivel: {barratt_data.get('nivel_total', 'N/A')})", 0, 1)
        
    if kostick_data:
        pdf.add_page()
        pdf.chapter_title("Resultados Test de Preferencias Personales Kostick")
        
        # Orden deseado de los factores para el PDF
        factor_order = ['g', 'l', 'i', 't', 'v', 's', 'r', 'd', 'c', 'z', 
                        'n', 'a', 'p', 'x', 'b', 'o', 'e', 'k', 'f', 'w']
        
        for factor_key in factor_order:
            factor_json = kostick_data.get(f"factor_{factor_key}")
            if factor_json:
                pdf.show_kostick_factor(factor_key, factor_json)
                
    if psqi_data:
        pdf.add_page()
        pdf.chapter_title("Resultados Índice de Calidad del Sueño de Pittsburgh (PSQI)")
        
        try:
            # Los datos ya vienen calculados desde el test
            if isinstance(psqi_data.get('puntuaciones'), str):
                puntuaciones = json.loads(psqi_data.get('puntuaciones', '{}'))
            else:
                puntuaciones = psqi_data.get('puntuaciones', {})
            
            if isinstance(psqi_data.get('resultado'), str):
                resultado = json.loads(psqi_data.get('resultado', '{}'))
            else:
                resultado = psqi_data.get('resultado', {})

            if not puntuaciones or not resultado:
                 pdf.chapter_body("Los resultados del PSQI aún no han sido calculados.")
            else:
                pdf.draw_psqi_table(puntuaciones, resultado)

        except Exception as e:
            pdf.set_font('Arial', 'I', 10)
            pdf.set_text_color(255, 0, 0)
            pdf.multi_cell(0, 5, f"Error al procesar los datos del PSQI: {e}")
            
    if western_data:
        pdf.add_page()
        pdf.chapter_title("Resultados Test de Aptitudes Mentales (Western)")
        
        puntaje_total = western_data.get("puntaje", "N/A")
        interpretacion = western_data.get("interpretacion", "N/A")
        
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, f"Puntaje Total Obtenido: {puntaje_total} / 24", 0, 1)
        pdf.set_font('Arial', '', 10)
        pdf.multi_cell(0, 7, f"Interpretación: {interpretacion}")
        
    if d48_data:
        pdf.add_page()
        pdf.chapter_title("Resultados Test de Funciones Ejecutivas (D-48)")
        
        puntaje_total = d48_data.get("puntaje", "N/A")
        interpretacion = d48_data.get("interpretacion", "N/A")
        
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, f"Puntaje Total Obtenido: {puntaje_total}", 0, 1)
        pdf.set_font('Arial', '', 10)
        pdf.multi_cell(0, 7, f"Interpretación: {interpretacion}")
        
    if _16pf_data:
        pdf.add_page()
        pdf.chapter_title("Resultados Cuestionario de Personalidad 16PF")
        
        try:
            if isinstance(_16pf_data.get('resultados'), str):
                resultados = json.loads(_16pf_data.get('resultados', '{}'))
            else:
                resultados = _16pf_data.get('resultados', {})
            
            interpretaciones = resultados.get("interpretaciones", {})
            decatipos = resultados.get("decatipos", {})
            decatipos_big_five = resultados.get("decatipos_big_five", {})
            interpretaciones_big_five = resultados.get("interpretaciones_big_five", {})
            
            if not interpretaciones:
                pdf.set_font('Arial', '', 10)
                pdf.multi_cell(0, 5, "Los resultados del 16PF aún no han sido calculados o no se encontraron.")
            else:
                pdf.draw_16pf_table(interpretaciones, decatipos)
                pdf.draw_big_five_table(decatipos_big_five, interpretaciones_big_five)
                
        except Exception as e:
            pdf.set_font('Arial', 'I', 10)
            pdf.set_text_color(255, 0, 0)
            pdf.multi_cell(0, 5, f"Error al procesar los datos del 16PF: {e}")
    

    
    # --- PBLL ---
    if pbll_data and pbll_data.get("image_path"):
        pdf.add_page()
        pdf.chapter_title("Resultados Test Proyectivo PBLL (Persona Bajo la Lluvia)")
        
        temp_file_path = None
        try:
            image_path = pbll_data["image_path"]
            res = supabase_client.storage.from_("ficha_ingreso_SM_bucket").download(path=image_path)
            
            file_extension = image_path.split('.')[-1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}") as temp_file:
                temp_file.write(res)
                temp_file_path = temp_file.name

            pdf.image(temp_file_path, x=10, y=pdf.get_y(), w=190)

        except Exception as e:
            pdf.set_font('Arial', 'I', 10)
            pdf.set_text_color(255, 0, 0)
            pdf.multi_cell(0, 7, f"Error al cargar la imagen del dibujo: {e}")
        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    return pdf.output(dest='S').encode('latin1')
    
def crear_interfaz_paciente(supabase: Client):
    st.title("Paso 1: Ficha de Ingreso Salud Mental")
    st.write("Por favor, ingrese su RUT para cargar sus datos y luego complete el resto del formulario.")

    if 'datos_paciente' not in st.session_state: st.session_state.datos_paciente = {}

    rut_a_buscar = st.text_input("Ingrese su RUT", placeholder="Ej. 12345678-9", help="Ingrese su RUT sin puntos y con guión.")
    if st.button("Buscar Datos"):
        if rut_a_buscar:
            with st.spinner("Buscando información..."):
                response = fetch_patient_data(supabase, rut_a_buscar)
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
        
        edad = st.number_input("Edad", min_value=17, max_value=100, value=st.session_state.datos_paciente.get("edad") or 17)
        
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
                    "sexo": st.session_state.datos_paciente.get("sexo", "NO ESPECIFICADO"),
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
                            # Guardar también en form_data para uso inmediato si es necesario
                            st.session_state.form_data['ficha_ingreso'] = form_data_to_save 
                            st.session_state.step = "test"
                            
                            st.query_params["ficha_id"] = ficha_id
                            st.rerun()
                        else:
                            st.error(f"Hubo un error al guardar la ficha: {response.error.message if response.error else 'Error desconocido'}")
                    except Exception as e:
                        st.error(f"Ocurrió una excepción al guardar: {e}")