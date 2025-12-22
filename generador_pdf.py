from fpdf import FPDF
from datetime import datetime
import base64

# --- Tablas de Puntuación T para EPQ-R ---
PUNTAJE_T_VARONES = {
    'E': {0:1, 1:1, 2:1, 3:2, 4:4, 5:5, 6:10, 7:10, 8:15, 9:20, 10:25, 11:30, 12:40, 13:45, 14:55, 15:65, 16:75, 17:85, 18:90, 19:98, 20:98, 21:98, 22:98, 23:98},
    'M': {0:1, 1:3, 2:4, 3:5, 4:10, 5:15, 6:20, 7:20, 8:25, 9:30, 10:35, 11:45, 12:50, 13:55, 14:65, 15:70, 16:75, 17:80, 18:85, 19:90, 20:95, 21:97, 22:99, 23:99},
    'D': {0:2, 1:5, 2:10, 3:20, 4:30, 5:40, 6:55, 7:65, 8:75, 9:80, 10:85, 11:90, 12:95, 13:95, 14:97, 15:99, 16:99, 17:99, 18:99, 19:99, 20:99, 21:99, 22:99, 23:99},
    'S': {0:1, 1:2, 2:4, 3:10, 4:15, 5:20, 6:30, 7:40, 8:50, 9:65, 10:70, 11:80, 12:85, 13:90, 14:90, 15:95, 16:97, 17:99, 18:99, 19:99}
}

PUNTAJE_T_MUJERES = {
    'E': {0:1, 1:1, 2:1, 3:2, 4:4, 5:5, 6:5, 7:10, 8:15, 9:20, 10:25, 11:30, 12:40, 13:50, 14:60, 15:70, 16:80, 17:90, 18:95, 19:99, 20:99, 21:99},
    'M': {0:1, 1:1, 2:2, 3:3, 4:4, 5:5, 6:10, 7:10, 8:15, 9:15, 10:20, 11:25, 12:35, 13:40, 14:45, 15:50, 16:55, 17:65, 18:70, 19:80, 20:85, 21:90, 22:96, 23:99},
    'D': {0:3, 1:10, 2:15, 3:25, 4:40, 5:50, 6:60, 7:75, 8:80, 9:85, 10:90, 11:95, 12:97, 13:98, 14:99, 15:99, 16:99, 17:99, 18:99},
    'S': {0:1, 1:1, 2:3, 3:5, 4:10, 5:15, 6:25, 7:35, 8:45, 9:55, 10:65, 11:70, 12:80, 13:85, 14:90, 15:95, 16:97, 17:99, 18:99}
}

# Clase base para los informes, con el logo
class PDFReport(FPDF):
    def header(self):
        try:
            self.image('workmed_logo.png', x=10, y=8, w=40)
        except RuntimeError:
            pass
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, self.title, 0, 1, 'C')
        self.ln(10)

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(4)

    def chapter_body(self, content):
        self.set_font('Arial', '', 10)
        self.multi_cell(0, 7, content)
        self.ln()

    def create_table_section(self, data):
        self.set_font('Arial', '', 10)
        for key, value in data.items():
            self.set_x(10)
            self.cell(90, 7, f"- {key}:", 0, 0)
            self.cell(0, 7, str(value), 0, 1)
        self.ln(5)
    
    def draw_results_table(self, scores_data):
        self.set_font('Arial', 'B', 10)
        col_width = (self.w - 20) / 6 # 1 para Dimensión, 5 para categorías
        self.cell(col_width, 10, 'DIMENSIONES', 1, 0, 'C')
        self.cell(col_width, 10, 'MUY POCA', 1, 0, 'C')
        self.cell(col_width, 10, 'POCA', 1, 0, 'C')
        self.cell(col_width, 10, 'MODERADO', 1, 0, 'C')
        self.cell(col_width, 10, 'BASTANTE', 1, 0, 'C')
        self.cell(col_width, 10, 'MUY ALTO', 1, 1, 'C')

        self.set_font('Arial', '', 9)
        for dimension, data in scores_data.items():
            self.cell(col_width, 10, dimension, 1, 0, 'L')
            categorias = ["MUY POCA", "POCA", "MODERADO", "BASTANTE", "MUY ALTO"]
            for cat in categorias:
                if data["categoria"] == cat:
                    self.set_font('Arial', 'B', 9)
                    self.cell(col_width, 10, data["descripcion"], 1, 0, 'C')
                    self.set_font('Arial', '', 9)
                else:
                    self.cell(col_width, 10, '', 1, 0, 'C')
            self.ln()

    def draw_detailed_scores_table(self, detailed_scores, sexo_paciente_display):
        self.set_font('Arial', 'B', 10)
        self.set_fill_color(200, 220, 255) # Light blue background for header

        # Headers
        self.cell(40, 10, 'Dimensiones', 1, 0, 'C', 1)
        self.cell(20, 10, 'PD', 1, 0, 'C', 1)
        self.cell(25, 10, 'Puntaje T H', 1, 0, 'C', 1)
        self.cell(25, 10, 'Puntaje T M', 1, 0, 'C', 1)
        self.cell(25, 10, 'Puntaje T Final', 1, 1, 'C', 1) # Line break

        self.set_font('Arial', '', 10)
        for dim, scores in detailed_scores.items():
            if dim != "Sexo":
                self.cell(40, 7, dim, 1, 0, 'L')
                self.cell(20, 7, str(scores['PD']), 1, 0, 'C')
                self.cell(25, 7, str(scores['Puntaje T H']), 1, 0, 'C')
                self.cell(25, 7, str(scores['Puntaje T M']), 1, 0, 'C')
                self.cell(25, 7, str(scores['Puntaje T Final']), 1, 1, 'C')
        
        # Sexo row
        self.cell(40, 7, 'Sexo', 1, 0, 'L')
        self.cell(20, 7, sexo_paciente_display, 1, 0, 'C')
        self.cell(25, 7, '', 1, 0, 'C') # Empty cells for H and M T-scores
        self.cell(25, 7, '', 1, 0, 'C')
        self.cell(25, 7, '', 1, 1, 'C') # Final empty cell
        self.ln(5)


# --- Generador de PDF para el Test de Epworth ---
def generar_pdf_epworth(epworth_data, ficha_data):
    pdf = PDFReport()
    pdf.title = 'Informe de Somnolencia de Epworth'
    pdf.add_page()
    pdf.chapter_title("Datos del Paciente")
    pdf.create_table_section({
        "Nombre Completo": ficha_data.get('nombre_completo', 'N/A'),
        "RUT": ficha_data.get('rut', 'N/A'),
        "Fecha de Evaluación": datetime.now().strftime('%d-%m-%Y'),
    })
    pdf.chapter_title("Resultados del Test")
    
    preguntas = {
        "sentado_leyendo": "Sentado y leyendo", "viendo_tv": "Viendo televisión",
        "sentado_publico": "Sentado en un lugar público", "pasajero_auto": "Como pasajero en un auto por 1 hora",
        "descansando_tarde": "Descansando en la tarde", "sentado_conversando": "Sentado y conversando con alguien",
        "post_almuerzo": "Sentado después del almuerzo (sin alcohol)", "auto_detenido": "En un auto, detenido por el tráfico"
    }
    
    total_score = sum(epworth_data.get(key, 0) for key in preguntas)
    resultados_data = {pregunta: epworth_data.get(key, 0) for key, pregunta in preguntas.items()}
    
    pdf.create_table_section(resultados_data)
    pdf.chapter_title("Puntaje Total e Interpretación")
    pdf.set_font('Arial', 'B', 12); pdf.cell(0, 10, f"Puntaje Total: {total_score}", 0, 1)

    interpretacion = "Normal."
    if 11 <= total_score <= 15: interpretacion = "Somnolencia diurna excesiva leve a moderada."
    elif total_score > 15: interpretacion = "Somnolencia diurna excesiva severa."
    
    pdf.chapter_body(interpretacion)
    return pdf.output(dest='S').encode('latin1')

# --- Generador de PDF para el Test EPQ-R (MODIFICADO) ---
def generar_pdf_epq_r(epq_r_data, ficha_data):
    pdf = PDFReport()
    pdf.title = 'Informe Test de Personalidad EPQ-R'
    pdf.add_page()
    pdf.chapter_title("Datos del Paciente")
    pdf.create_table_section({
        "Nombre Completo": ficha_data.get('nombre_completo', 'N/A'),
        "RUT": ficha_data.get('rut', 'N/A'),
        "Fecha de Evaluación": datetime.now().strftime('%d-%m-%Y'),
    })

    # --- Lógica de Puntuación ---
    sexo_paciente = ficha_data.get('sexo', 'MASCULINO').upper()
    tabla_puntaje_t_final = PUNTAJE_T_VARONES if sexo_paciente == 'MASCULINO' else PUNTAJE_T_MUJERES

    conteos = {'E': 0, 'M': 0, 'D': 0, 'S': 0}
    for i in range(1, 84):
        letra = epq_r_data.get(f'pregunta_{i}')
        if letra in conteos:
            conteos[letra] += 1

    # Preparar datos para la tabla de puntajes detallados
    detailed_scores = {}
    personalidades_orden = [('S', 'Sinceridad'), ('E', 'Extraversión'), ('M', 'Emotividad'), ('D', 'Dureza')]

    for letra_code, dim_name in personalidades_orden:
        pd_score = conteos[letra_code]
        
        # Obtener puntajes T para Hombres y Mujeres (sin importar el sexo del paciente)
        puntaje_t_hombre = PUNTAJE_T_VARONES[letra_code].get(pd_score, 0)
        puntaje_t_mujer = PUNTAJE_T_MUJERES[letra_code].get(pd_score, 0)
        
        # Puntaje T Final es el que corresponde al sexo del paciente
        puntaje_t_final = tabla_puntaje_t_final[letra_code].get(pd_score, 0)

        detailed_scores[dim_name] = {
            'PD': pd_score,
            'Puntaje T H': puntaje_t_hombre,
            'Puntaje T M': puntaje_t_mujer,
            'Puntaje T Final': puntaje_t_final
        }

    pdf.chapter_title("Puntajes Obtenidos por Dimensión")
    sexo_display = "M" if sexo_paciente == 'MASCULINO' else "F"
    pdf.draw_detailed_scores_table(detailed_scores, sexo_display)

    descripciones = {
        "Sinceridad": { "MUY POCA": "muy sincero", "POCA": "Tendencia a ser sincero", "MODERADO": "Moderadamente sincero", "BASTANTE": "Tendencia a no ser sincero", "MUY ALTO": "Muy Poco sincero" },
        "Extraversión": { "MUY POCA": "Muy Introvertido", "POCA": "Bastante Introvertido", "MODERADO": "Moderna Extroversión", "BASTANTE": "Bastante extrovertido", "MUY ALTO": "Muy extrovertido" },
        "Emotividad": { "MUY POCA": "Muy Estable", "POCA": "Bastante Estable", "MODERADO": "Moderna Emotividad", "BASTANTE": "Bastante inestable", "MUY ALTO": "Muy Inestable" },
        "Dureza": { "MUY POCA": "Muy Empático", "POCA": "Bastante empático", "MODERADO": "Moderna Dureza", "BASTANTE": "Bastante insensible", "MUY ALTO": "Muy insensible" }
    }
    
    resultados_interpretacion = {}
    for letra, nombre in personalidades_orden:
        pt = detailed_scores[nombre]['Puntaje T Final'] # Usamos el puntaje T final calculado
        categoria = ""
        if pt <= 35: categoria = "MUY POCA"
        elif 36 <= pt <= 45: categoria = "POCA"
        elif 46 <= pt <= 55: categoria = "MODERADO"
        elif 56 <= pt <= 65: categoria = "BASTANTE"
        else: categoria = "MUY ALTO"
        
        resultados_interpretacion[nombre] = {
            "puntaje_t": pt,
            "categoria": categoria,
            "descripcion": descripciones[nombre][categoria]
        }

    pdf.chapter_title("Interpretación de Resultados")
    pdf.draw_results_table(resultados_interpretacion)

    # Añadir imagen de la tabla de resultados
    try:
        pdf.image("tabla_resultados_epqr.png", x=10, y=pdf.get_y() + 10, w=190)
    except RuntimeError:
        pdf.ln(10)
        #pdf.chapter_body("[Aquí iría la imagen de la tabla de resultados, pero no se encontró el archivo 'tabla_resultados_epqr.png']")
        
    # --- SECCIÓN DE CONCLUSIÓN / APTITUD ---
    pdf.ln(90) # Espacio después de la imagen
    pdf.chapter_title("Conclusión")
    
    aptitud = epq_r_data.get('aptitud', 'NO APTO') # Default si no existe la clave
    
    texto_conclusion = ""
    if aptitud:
        texto_conclusion = "APTO: Ajuste psicosocial dentro de los parámetros esperados."
    else:
        texto_conclusion = "NO APTO: Ajuste psicosocial inferior a lo requerido."
    
    # Dibujar la conclusión en negrita
    pdf.set_font('Arial', 'B', 11)
    pdf.multi_cell(0, 7, texto_conclusion)

    return pdf.output(dest='S').encode('latin1')

