from fpdf import FPDF
from datetime import datetime

# Clase base para los informes, con el logo
class PDFReport(FPDF):
    def header(self):
        self.image('workmed_logo.png', x=10, y=8, w=40)
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

# --- Generador de PDF para el Test de Epworth ---
def generar_pdf_epworth(epworth_data, ficha_data):
    """
    Crea un informe PDF específico para los resultados del Test de Epworth.
    """
    pdf = PDFReport()
    pdf.title = 'Informe de Somnolencia de Epworth'
    pdf.add_page()

    # Información del paciente
    pdf.chapter_title("Datos del Paciente")
    pdf.create_table_section({
        "Nombre Completo": ficha_data.get('nombre_completo', 'N/A'),
        "RUT": ficha_data.get('rut', 'N/A'),
        "Fecha de Evaluación": datetime.now().strftime('%d-%m-%Y'),
    })

    # Resultados del test
    pdf.chapter_title("Resultados del Test")
    
    preguntas = {
        "sentado_leyendo": "Sentado y leyendo",
        "viendo_tv": "Viendo televisión",
        "sentado_publico": "Sentado en un lugar público",
        "pasajero_auto": "Como pasajero en un auto por 1 hora",
        "descansando_tarde": "Descansando en la tarde",
        "sentado_conversando": "Sentado y conversando con alguien",
        "post_almuerzo": "Sentado después del almuerzo (sin alcohol)",
        "auto_detenido": "En un auto, detenido por el tráfico"
    }
    
    total_score = 0
    resultados_data = {}
    for key, pregunta in preguntas.items():
        score = epworth_data.get(key, 0)
        total_score += score
        resultados_data[pregunta] = score
    
    pdf.create_table_section(resultados_data)
    
    # Puntaje Total e Interpretación
    pdf.chapter_title("Puntaje Total e Interpretación")
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, f"Puntaje Total: {total_score}", 0, 1)

    interpretacion = ""
    if total_score <= 10:
        interpretacion = "Normal."
    elif 11 <= total_score <= 15:
        interpretacion = "Somnolencia diurna excesiva leve a moderada."
    else: # > 15
        interpretacion = "Somnolencia diurna excesiva severa."
    
    pdf.chapter_body(interpretacion)

    return pdf.output(dest='S').encode('latin1')
