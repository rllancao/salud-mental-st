import streamlit as st
from supabase import Client
import json
import math

# --- DEBES RELLENAR ESTOS DICCIONARIOS ---

# 1. Mapeo de Pregunta -> Factor
# Basado en tu input (ej: A: 1, 65, 63...)
QUESTIONS_TO_FACTOR_MAP = {
    1: 'A', 2: 'C', 3: 'E', 4: 'F', 5: 'G', 6: 'F', 7: 'G', 8: 'I', 9: 'H', 10: 'I',
    11: 'L', 12: 'M', 13: 'L', 14: 'M', 15: 'N', 16: 'MI', 17: 'M', 18: 'N', 19: 'O', 20: 'Q1',
    21: 'O', 22: 'Q1', 23: 'MI', 24: 'Q1', 25: 'Q2', 26: 'Q3', 27: 'Q2', 28: 'Q4', 29: 'Q3', 30: 'Q4',
    31: 'A', 32: 'C', 33: 'A', 34: 'MI', 35: 'C', 36: 'E', 37: 'F', 38: 'E', 39: 'F', 40: 'G',
    41: 'H', 42: 'I', 43: 'L', 44: 'I', 45: 'L', 46: 'M', 47: 'N', 48: 'MI', 49: 'M', 50: 'N',
    51: 'O', 52: 'Q1', 53: 'Q1', 54: 'O', 55: 'Q1', 56: 'Q2', 57: 'Q3', 58: 'MI', 59: 'Q2', 60: 'Q4',
    61: 'Q3', 62: 'Q4', 63: 'A', 64: 'C', 65: 'A', 66: 'E', 67: 'C', 68: 'F', 69: 'G', 70: 'F',
    71: 'H', 72: 'G', 73: 'H', 74: 'I', 75: 'MI', 76: 'L', 77: 'I', 78: 'L', 79: 'M', 80: 'N',
    81: 'M', 82: 'O', 83: 'Q1', 84: 'N', 85: 'MI', 86: 'Q1', 87: 'O', 88: 'Q1', 89: 'Q2', 90: 'Q3',
    91: 'Q4', 92: 'Q2', 93: 'Q3', 94: 'Q4', 95: 'MI', 96: 'A', 97: 'C', 98: 'A', 99: 'E', 100: 'F',
    101: 'MI', 102: 'E', 103: 'F', 104: 'G', 105: 'H', 106: 'G', 107: 'H', 108: 'I', 109: 'L', 110: 'I',
    111: 'M', 112: 'L', 113: 'N', 114: 'M', 115: 'MI', 116: 'O', 117: 'N', 118: 'Q1', 119: 'O', 120: 'Q1',
    121: 'Q2', 122: 'Q3', 123: 'Q2', 124: 'Q4', 125: 'Q3', 126: 'Q4', 127: 'A', 128: 'C', 129: 'A', 130: 'E',
    131: 'C', 132: 'E', 133: 'G', 134: 'F', 135: 'H', 136: 'G', 137: 'H', 138: 'I', 139: 'L', 140: 'I',
    141: 'L', 142: 'M', 143: 'N', 144: 'MI', 145: 'M', 146: 'O', 147: 'Q1', 148: 'N', 149: 'Q1', 150: 'O',
    151: 'Q1', 152: 'Q2', 153: 'MI', 154: 'Q3', 155: 'Q4', 156: 'Q2', 157: 'Q3', 158: 'Q4', 159: 'A', 160: 'C',
    161: 'A', 162: 'C', 163: 'E', 164: 'F', 165: 'E', 166: 'G', 167: 'H', 168: 'G', 169: 'H', 170: 'I',
    171: 'B', 172: 'B', 173: 'B', 174: 'B', 175: 'B', 176: 'B', 177: 'B', 178: 'B', 179: 'B', 180: 'B',
    181: 'B', 182: 'B', 183: 'B', 184: 'B', 185: 'B',
    # Factores IN y AQ (se calculan por separado)
}

# 2. Mapeo de Preguntas de Opción Múltiple (a, b, c) a puntajes
# DEBES RELLENAR ESTO CON LOS PUNTAJES DE CADA RESPUESTA
# Formato: { "Texto de la pregunta": {"a": 2, "b": 1, "c": 0} }
# La alternativa 'b' (intermedia) suele valer 1.
# El puntaje 2 o 0 depende de si la alternativa (a o c) se alinea con el factor.
OPTION_SETS = {
    "MAQUINAS_REGISTROS": {"Las máquinas o llevar registros": 1, "?": 2, "Entrevistar y hablar con personas": 3},
    "VERDADERO_FALSO_1_3": {"Verdadero": 1, "?": 2, "Falso": 3},
    "SENALAR_PASAR": {"Se lo señalo": 1, "?": 2, "Lo paso por alto": 3},
    "CAPACIDAD_TALENTO": {"Una persona con capacidad de tipo medio, pero con una moral estricta": 1, "?": 2, "Una persona con talento, aunque a veces no sea responsable": 3},
    "INGENIERO_ESCRITOR": {"Ingeniero de la construcción": 1, "?": 2, "Escritor de teatro": 3},
    "SI_NO_1_3": {"Sí": 1, "?": 2, "No": 3},
    "FACILIDAD_REMEDIO": {"Con facilidad cuando las personas parecen estar interesadas.": 1, "?": 2, "Solo si no tengo más remedio.": 3},
    "ALGUNAS_NUNCA": {"Algunas veces": 1, "?": 2, "Nunca": 3},
    "CASINUNCA_AMENUDO": {"Casi nunca": 1, "?": 2, "A menudo": 3},
    "COMENTAR_GUARDAR": {"Comentar mis problemas con los amigos": 1, "?": 2, "Guardarlos para mis adentros": 3},
    "NO_PERTURBABA_DANO": {"No me perturbaba": 1, "?": 2, "Normalmente me hace daño": 3},
    "DISCUTIR_CAMBIAR": {"Discutir el significado de nuestras diferencias básicas": 1, "?": 2, "Cambiar el tema": 3},
    "VERDADERO_EVITAR": {"Verdadero, para evitar problemas": 1, "?": 2, "Falso, porque podría hacer algo más interesante": 3},
    "OTROS_SOLO": {"Con otros": 1, "?": 2, "Yo solo": 3},
    "RARAS_AMENUDO": {"Raras veces": 1, "?": 2, "A menudo": 3},
    "MOLESTARIA_CONTENTO": {"Eso me molestaría e irritaría": 1, "?": 2, "Me parecería bien y estaría contento de cambiarlos": 3},
    "OFICINA": {"Estar en una oficina, organizando y atendiendo personas": 1, "?": 2, "Ser arquitecto dibujar planos en un despacho tranquilo": 3},
    "MARCHAR_MAL": {"Me siento como si no pudiera dormir": 1, "?": 2, "Continúo de un modo normal": 3},
    "TARDE_1": {"Haciendo con tranquilidad y sosiego algo por lo que tenga afición": 1, "?": 2, "En una fiesta animada": 3},
    "EJERCICIO": {"La esgrima o la danza": 1, "?": 2, "El tenis o la lucha libre": 3},
    "PERSONAS": {"Siempre están haciendo cosas prácticas que necesitan ser hechas": 1, "?": 2, "Imaginan o piensan acerca de cosas sobre sí mismas": 3},
    "DECISION": {"Normalmente verdadero": 1, "?": 2, "Normalmente falso": 3},
    "PERSONAS_DIF": {"Verdadero, normalmente no me gustan": 1, "?": 2, "Falso, normalmente las encuentro interesantes": 3},
    "SIGNIFICADO": {"Buscar un significado personal a la vida": 1, "?": 2, "Asegurarme un trabajo con un buen sueldo": 3},
    "MUNDO": {"Más ciudadanos íntegros y constantes": 1, "?": 2, "Más reformadores con opiniones sobre cómo mejorar el mundo": 3},
    "JUEGOS": {"Se forman equipos o se tiene un compañero": 1, "?": 2, "Cada uno hace su partida": 3},
    "INTERRUMPE": {"Verdadero, no me siento mal": 1, "?": 2, "Falso, me molesta": 3},
    "EMOCIONALES": {"No están demasiado satisfechas": 1, "?": 2, "Están bien satisfechas": 3},
    "VESTIR": {"De modo aseado y sencillo": 1, "?": 2, "A la moda y original": 3},
    "SEGURIDAD": {"Verdadero, porque no siempre son necesarias": 1, "?": 2, "Falso, porque es importante hacer las cosas correctamente": 3},
    "EXTRAÑOS": {"Nunca me ha dado problemas": 1, "?": 2, "Me cuesta bastante": 3},
    "PERIODICO_1": {"Literatura o cine": 1, "?": 2, "Deportes o política": 3},
    "PEQUEÑAS": {"A veces": 1, "?": 2, "Raras veces": 3},
    "GUARDIA": {"Verdadero": 1, "?": 2, "Falso": 3},
    "CONTEMPLAR": {"Verdadero": 1, "?": 2, "Falso": 3},
    "PEREZOSA": {"Casi nunca": 1, "?": 2, "A menudo": 3},
    "IDEAS": {"Verdadero": 1, "?": 2, "Falso": 3},
    "INFO": {"Normalmente verdadero": 1, "?": 2, "Normalmente falso": 3},
    "ATENCION": {"Las cosas que me rodean": 1, "?": 2, "Los pensamientos y la imaginación": 3},
    "CRITICA": {"Casi nunca": 1, "?": 2, "A menudo": 3},
    "INTERESANTE": {"Verdadero": 1, "?": 2, "Falso": 3},
    "TRATAR_GENTE": {"'Poner todas las cartas sobre la mesa'": 1, "?": 2, "'No descubrir tu propio juego'": 3},
    "SITIO": {"Verdadero": 1, "?": 2, "Falso": 3},
    "GUSTO_GENTE": {"Es estable y tradicional en sus intereses": 1, "?": 2, "Reconsidera seriamente sus puntos de vista sobre la vida": 3},
    "ALREDEDOR": {"Verdadero": 1, "?": 2, "Falso": 3},
    "TRABAJO_FAMILIAR": {"Me aburre y me da sueño": 1, "?": 2, "Me da seguridad y confianza": 3},
    "TRABAJO_SOLO": {"Verdadero": 1, "?": 2, "Falso": 3},
    "HABITACION": {"Verdadero": 1, "?": 2, "Falso": 3},
    "PACIENTE": {"Verdadero": 1, "?": 2, "Falso, me cuesta ser paciente": 3},    
    "UNIRME": {"Verdadero": 1, "?": 2, "Falso": 3},
    "PERFECCIONISTA": {"Verdadero": 1, "?": 2, "Falso": 3},
    "COLA": {"Verdadero, no me pongo": 1, "?": 2, "Falso, me pongo intranquilo": 3},
    "INTENCIONES": {"A veces": 1, "?": 2, "Nunca": 3},
    "EMOCIONES": {"Verdadero": 1, "?": 2, "Falso": 3},
    "DEPRIMAN": {"Verdadero": 1, "?": 2, "Falso": 3},
    "INVENTO": {"Investigarlo en el laboratorio": 1, "?": 2, "Mostrar a las personas su utilización": 3},
    "CORTES": {"Verdadero": 1, "?": 2, "Falso": 3},
    "ESPECTACULO": {"Verdadero": 1, "?": 2, "Falso": 3},
    "INSATISFECHO": {"Verdadero": 1, "?": 2, "Falso": 3},
    "CIUDAD": {"No protestaría y les seguiría el juego": 1, "?": 2, "Les haría saber que yo creía que mi camino era mejor": 3},
    "ANIMADA": {"Verdadero": 1, "?": 2, "Falso": 3},
    "BANCO": { "Lo indicaría y lo pagaría": 1, "?": 2, "Yo no tengo por qué decírselo": 3},
    "TIMIDEZ": {"Verdadero": 1, "?": 2, "Falso": 3},
    "PROFESORES": {"Verdadero": 1, "?": 2, "Falso": 3},   
    "PESO": {"Verdadero": 1, "?": 2, "Falso": 3},
    "POEMA": {"Verdadero": 1, "?": 2, "Falso": 3},
    "FRANCO": {"Casi nunca": 1, "?": 2, "A menudo": 3},
    "MECANICAS": {"Verdadero": 1, "?": 2, "Falso": 3},
    "PENSAMIENTOS": {"Verdadero": 1, "?": 2, "Falso": 3},
    "CONFIAR": {"Verdadero, no se puede confiar en ellas": 1, "?": 2, "Falso, se puede confiar en ellas": 3},
    "CONOZCO": {"Verdadero": 1, "?": 2, "Falso": 3},
    "IDEAS_PRACTICAS": {"Verdadero": 1, "?": 2, "Falso": 3},
    "OBSERVACIONES": {"Verdadero": 1, "?": 2, "Falso": 3},
    "HECHO_MALO": {"Verdadero": 1, "?": 2, "Falso": 3},
    "PERSONALES": {"Verdadero": 1, "?": 2, "Falso": 3},
    "MODOS": {"Verdadero": 1, "?": 2, "Falso": 3},
    "SENSIBLE": {"Casi nunca": 1, "?": 2, "A menudo": 3},
    "PERIODICO_2": {"Los artículos sobre los problemas sociuales": 1, "?": 2, "Todas las noticias locales": 3},
    "TARDE_2": {"Leer o trabajar en solitario en un proyecto": 1, "?": 2, "Hacer alguna tarea con los amigos": 3},
    "MOLESTO": {"Dejarlo a un lado hasta que no haya más remedio que hacerlo": 1, "?": 2, "Comenzar a hacerlo de inmediato": 3},
    "TOMAR_COMIDA": {"Con un grupo de gente": 1, "?": 2, "En solitario": 3},
    "PACIENTE_PERSONAS": {"Verdadero": 1, "?": 2, "Falso": 3},
    "PENSAR_ANTES": {"Verdadero": 1, "?": 2, "Falso": 3},
    "EXPLICAR_ALGO": {"Verdadero": 1, "?": 2, "Falso": 3},
    "DESCRIBEN_COMO": {"Cálida y amigable": 1, "?": 2, "Formal y objetiva": 3},
    "PERTURBA": {"Verdadero": 1, "?": 2, "Falso": 3},
    "AFICION_AGRADABLE": {"Hacer o reparar algo": 1, "?": 2, "Trabajar en grupo en una tarea comunitaria": 3},
    "RESTAURANT": {"Verdadero": 1, "?": 2, "Falso": 3},
    "CAMBIOS_HUMOR": {"Normalmente verdadero": 1, "?": 2, "Normalmente falso": 3},
    "VEN_COSAS": {"Verdadero": 1, "?": 2, "Falso": 3},
    "SER_LIBRE": {"Verdadero": 1, "?": 2, "Falso": 3},
    "HACER_REIR": {"Verdadero": 1, "?": 2, "Falso": 3},
    "SOCIALMENTE_ATREVIDA": {"Verdadero": 1, "?": 2, "Falso": 3},
    "ELUDIR": {"Podría incumplirlas si tiene razones especiales para ello": 1, "?": 2, "Debería seguirlas a pesar de todo": 3},
    "NUEVO_GRUPO": {"Verdadero": 1, "?": 2, "Falso": 3},
    "LEER_HISTORIAS": {"Verdadero": 1, "?": 2, "Falso": 3},
    "SOSPECHO": {"Casi nunca": 1, "?": 2, "A menudo": 3},
    "TIEMPO_EN": {"Hacer o construir algo": 1, "?": 2, "Leer o imaginar cosas ideales": 3},
    "QUISQUILLOSAS": {"Verdadero": 1, "?": 2, "Falso": 3},
    "DETALLES_PRACTICOS": {"Verdadero": 1, "?": 2, "Falso": 3},
    "PREGUNTA_PERSONAL": {"Normalmente verdadero": 1, "?": 2, "Normalmente falso": 3},
    "TAREA_VOLUNTARIA": {"A veces": 1, "?": 2, "Raras veces": 3},
    "ABSTRAIDO": {"Verdadero": 1, "?": 2, "Falso": 3},
    "ABATIDO_CRITICAS": {"Verdadero": 1, "?": 2, "Falso": 3},
    "SURGEN_PROBLEMAS": {"Se cuestionan o cambian métodos que son ya satisfactorios": 1, "?": 2, "Descartan enfoques nuevos o prometedores": 3},
    "ABRIRME": {"Verdadero": 1, "?": 2, "Falso": 3},
    "NUEVOS_MODOS": {"Verdadero": 1, "?": 2, "Falso": 3},
    "CRITICO": {"Verdadero": 1, "?": 2, "Falso": 3},
    "COMIDA_ALIMENTOS": {"Verdadero": 1, "?": 2, "Falso": 3},
    "SIN_HABLAR": {"Verdadero": 1, "?": 2, "Falso": 3},
    "AYUDAR_PERSONAS": {"Siempre": 1, "?": 2, "A veces": 3},
    "CREO_QUE": {"Algunos trabajos no deberían ser hechos tan cuidadosamente como otros": 1, "?": 2, "Cualquier trabajo habría que hacerlo bien si es que se va a hacer": 3},
    "DIFICIL_PACIENTE": {"Verdadero": 1, "?": 2, "Falso": 3},
    "PREFIERO_GENTE": {"Verdadero": 1, "?": 2, "Falso": 3},
    "TAREA_SATISFECHO": {"Verdadero": 1, "?": 2, "Falso": 3},
    "SACAN_DE_QUICIO": {"Sí": 1, "?": 2, "No": 3},
    "ESCUCHAR_GENTE": {"Verdadero": 1, "?": 2, "Falso": 3},
    "HUMOR_VER": {"Muy raras veces": 1, "?": 2, "Bastante a menudo": 3},
    "CONSEJERO_ORIENTADOR": {"Verdadero": 1, "?": 2, "Falso": 3},
    "VIDA_COTIDIANA": {"Verdadero, puedo afrontarlos fácilmente": 1, "?": 2, "Falso": 3},
    "PERSONAS_MOLESTAN": {"No le doy importancia": 1, "?": 2, "Se lo digo": 3},
    "CREO_MAS_EN": {"Ser claramente serio en la vida cotidiana": 1, "?": 2, "Seguir casi siempre el dicho 'Diviértete y sé feliz'": 3},
    "COMPETITIVIDAD_COSAS": {"Verdadero": 1, "?": 2, "Falso": 3},
    "MAYORIA_NORMAS": {"Verdadero": 1, "?": 2, "Falso": 3},
    "CUESTA_HABLAR": {"Verdadero": 1, "?": 2, "Falso": 3},
    "HOGAR_EN_QUE": {"Se sigan normas estrictas de conducta": 1, "?": 2, "No haya muchas normas": 3},
    "REUNIONES_SOCIALES": {"Verdadero": 1, "?": 2, "Falso": 3},
    "TELEVISION": {"Un programa sobre nuevos inventos prácticos": 1, "?": 2, "Un concierto de un artista famoso": 3},
    "MINUTO_A_HORA": {"Minuto": 1, "Milisegundo": 2, "Hora": 3},
    "RENACUAJO": {"Araña": 1, "Gusano": 2, "Insecto": 3},
    "JAMON": {"Cordero": 1, "Pollo": 2, "Merluza": 3},
    "HIELO": {"Lava": 1, "Arena": 2, "Petróleo": 3},
    "MEJOR": {"Super": 1, "Santo": 2, "Óptimo": 3},
    "TRES_PALABRAS": {"Terminal": 1, "Estacional": 2, "Cíclico": 3},
    "TRES_P_GATO": {"Gato": 1, "Cerca": 2, "Planeta": 3},
    "OPUESTO_CORRECTO": {"Bueno": 1, "Erróneo": 2, "Adecuado": 3},
    "TRES_P_PROB": {"Probable": 1, "Eventual": 2, "Inseguro": 3},
    "OPUESTO_INEXACTO": {"Casual": 1, "Puntual": 2, "Incorrecto": 3},
    "NUMERO_SIGUE": {"20": 1, "25": 2, "32": 3},
    "LETRA_SIGUE": {"H": 1, "K": 2, "J": 3},
    "LETRA_SIGUE_2": {"M": 1, "N": 2, "O": 3},
    "NUMERO_SIGUE_2": {"3/4": 1, "4/3": 2, "3/2": 3},
    "NUMERO_SIGUE_3": {"5": 1, "4": 2, "-3": 3},
}

# --- 3. Textos de Preguntas ---
TEXTOS_PREGUNTAS = {
    1: "En un negocio sería más interesante encargarse de:",
    2: "Normalmente me voy a dormir sintiéndome satisfecho de cómo ha ido el día.",
    3: "Si observo que la línea de razonamiento de otra persona es incorrecta, normalmente:",
    4: "Me gusta muchísimo tener invitados y hacer que se lo pasen bien.",
    5: "Cuando tomo una decisión siempre pienso cuidadosamente en lo que es correcto y justo.",
    6: "Me atrae más pasar una tarde ocupado en una tarea tranquila a la que tenga afición que estar en una reunión animada.",
    7: "Admiro más a :",
    8: "Sería más interesante ser:",
    9: "Normalmente soy el que da el primer paso al hacer amigos.",
    10: "Me encantan las buenas novelas u obras de teatro - cine.",
    11: "Cuando la gente autoritaria trata de dominarte hago justamente lo contrario de lo que quiere.",
    12: "Algunas veces no congenio muy bien con los demás porque mis ideas no son convencionales y corrientes.",
    13: "Muchas personas te “apuñalarían por la espalda” para salir ellas adelante.",
    14: "Me meto en problemas porque a veces sigo adelante con mis ideas sin comentarlas con las personas que puedan estar implicadas.",
    15: "Hablo de mis sentimientos:",
    16: "Me aprovecho de la gente.",
    17: "Mis pensamientos son demasiado complicados y profundos para ser comprendidos por muchas personas.",
    18: "Prefiero:",
    19: "Pienso a cerca de cosas que debería haber dicho, pero que no las dije.",
    20: "Siempre estoy alerta ante los intentos de propagandas en las cosas que leo.",
    21: "Si las personas actúan como si yo no les gustara:",
    22: "Cuando observo que difiero de alguien en puntos de vista sociales, prefiero:",
    23: "He dicho cosas que hirieron los sentimientos de otros.",
    24: "Si tuviera que cocinar o construir algo seguiría las instrucciones exactamente.",
    25: "A la hora de construir o hacer algo preferiría trabajar:",
    26: "Me gusta hacer planes con antelación para no perder tiempo en las tareas.",
    27: "Normalmente me gusta hacer mis planes yo solo, sin interrupciones y sugerencias de otros.",
    28: "Cuando me siento tenso incluso pequeñas cosas me sacan de quicio.",
    29: "Puedo encontrarme bastante a gusto en un ambiente desorganizado.",
    30: "Si mis planes, cuidadosamente elaborados, tuvieran que ser cambiados a causa de otras personas:",
    31: "Preferiría:",
    32: "Cuando las pequeñas cosas comienzan a marchar mal unas detrás de otras:",
    33: "Me satisface y entretiene cuidarme de las necesidades de los demás.",
    34: "A veces hago observaciones tontas , a modo de broma, para sorprender a los demás.",
    35: "Cuando llega él momento de hacer algo que he planeado y esperado, a veces no me apetece ya continuarlo.",
    36: "En las situaciones que dependen de mí me siento bien dando instrucciones a los demás.",
    37: "Preferiría emplear una tarde:",
    38: "Cuando yo sé muy bien lo que el grupo tiene que hacer, me gusta ser el único en dar las órdenes.",
    39: "Me divierte mucho el humor rápido y vivaz de algunas series de televisión.",
    40: "Le doy más valor y respeto a las normas y buenas maneras, que a una vida fácil.",
    41: "Me encuentro tímido y retraído a la hora de hacer amigos entre personas desconocidas.",
    42: "Si pudiera, preferiría hacer ejercicio con:",
    43: "Normalmente hay una gran diferencia entre lo que la gente dice y lo que hace.",
    44: "Resultaría más interesante ser músico que mecánico.",
    45: "Las personas forman su opinión acerca de mí demasiado rápidamente.",
    46: "Soy de esas personas que:",
    47: "Algunas personas creen que es difícil intimar conmigo.",
    48: "Puedo engañar a las personas siendo amigable cuando en realidad me desagradan.",
    49: "Mis pensamientos tienden más a girar sobre cosas realistas y prácticas.",
    50: "Suelo ser reservado y guardar mis problemas para mis adentros.",
    51: "Después de tomar una decisión sobre algo sigo pensando si será acertada o errónea.",
    52: "En el fondo no me gustan las personas que son “diferentes” u originales.",
    53: "Estoy más interesado en:",
    54: "Me perturbo más que otros cuando las personas se enfadan entre ellas.",
    55: "Lo que este mundo necesita es:",
    56: "Prefiero los juegos en lo que:",
    57: "Normalmente dejo algunas cosas a la buena suerte, en vez de hacer planes complejos y con todo detalle.",
    58: "Frecuentemente tengo periodos de tiempo en que me es difícil abandonar el sentimiento de compadecerme a mí mismo.",
    59: "Mis mejores horas del día son aquellas en que estoy solo con mis pensamientos y proyecto.",
    60: "Si la gente me interrumpe cuando estoy intentando hacer algo, eso no me perturba.",
    61: "Siempre conservo mis pertenencias en perfectas condiciones.",
    62: "A veces me siento frustrado por las personas demasiado rápidamente.",
    63: "No me siento a gusto cuando hablo o muestro mis sentimientos de afecto o cariño.",
    64: "En mi vida personal, casi siempre alcanzo las metas que me pongo.",
    65: "Si el sueldo fuera el mismo, preferiría ser un científico más que un directivo de ventas.",
    66: "Si la gente hace algo incorrecto, normalmente le digo lo que pienso.",
    67: "Pienso que mis necesidades emocionales:",
    68: "Normalmente me gusta estar en medio de mucha actividad y excitación.",
    69: "La gente debería insistir, más de lo que hace ahora, en que las normas morales sean seguidas estrictamente.",
    70: "Preferiría vestir:",
    71: "Me suelo sentir desconcertado si de pronto paso a ser el centro de la atención en un grupo social.",
    72: "Me pone irritado que la gente insista en que yo siga las mínimas reglas de seguridad.",
    73: "Comenzar a conversar con extraños:",
    74: "Si trabajara en un periódico preferiría los temas de:",
    75: "Dejo que pequeñas cosas me perturben más de lo que deberían.",
    76: "Es acertado estar en guardia con los que hablan de modo amable, por que se pueden aprovechar de uno.",
    77: "En la calle me detendría más a contemplar un artista pintando que a ver la construcción de un edificio.",
    78: "Las personas se hacen perezosas en su trabajo cuando consiguen hacerlo con facilidad.",
    79: "Se me ocurren ideas nuevas sobre todo tipo de cosas, demasiadas para ponerlas en práctica.",
    80: "Cuando hablo con alguien que no conozco todavía, no doy más información que la necesaria.",
    81: "Pongo más atención en:",
    82: "Cuando la gente me critica delante de otros me siento muy descorazonado y herido.",
    83: "Encuentro más interesante a la gente si sus puntos de vista son diferentes de los de la mayoría.",
    84: "Al tratar con la gente es mejor:",
    85: "A veces me gustaría más ponerme en mi sitio que perdonar y olvidar.",
    86: "Me gusta la gente que:",
    87: "A veces me siento demasiado responsable sobre cosas que suceden a mí alrededor.",
    88: "El trabajo que me es familiar y habitual:",
    89: "Logro terminar las cosas mejor cuando trabajo solo que cuando lo hago en equipo.",
    90: "Normalmente no me importa si mi habitación está desordenada.",
    91: "Me resulta fácil ser paciente, aun cuando alguien es lento para comprender lo que estoy explicándole.",
    92: "Me gusta unirme a otros que van a hacer algo juntos, como ir a un museo o de excursión.",
    93: "Soy algo perfeccionista y me gusta que las cosas se hagan bien.",
    94: "Cuándo tengo que hacer una larga cola por algún motivo, no me pongo tan intranquilo y nervioso como la mayoría.",
    95: "La gente me trata menos razonablemente de lo que merecen mis buenas intenciones.",
    96: "Me lo paso bien con gente que muestra abiertamente sus emociones.",
    97: "No dejo que me depriman pequeñas cosas.",
    98: "Si pudiera ayudar en el desarrollo de un invento útil preferiría encargarme de:",
    99: "Si ser cortés y amable no da resultado puedo ser rudo y astuto cuando sea necesario.",
    100: "Me gusta ir a menudo a espectáculos y diversiones.",
    101: "Me siento insatisfecho conmigo mismo.",
    102: "Si nos perdiéramos en una cuidad y los amigos no estuvieran de acuerdo conmigo en el camino a seguir:",
    103: "La gente me considera una persona animada y sin preocupaciones.",
    104: "Si el banco se descuidara y no me cobrara algo que debiera, creo que:",
    105: "Siempre tengo que estar luchando contra mi timidez.",
    106: "Los profesores, sacerdotes y otras personas emplean mucho tiempo intentando impedirnos hacer lo que deseamos.",
    107: "Cuando estoy con un grupo, normalmente me siento, escucho y dejo que los demás lleven el peso de la conversación.",
    108: "Normalmente aprecio más belleza de un poema que una excelente estrategia en un deporte.",
    109: "Si uno es franco y abierto los demás intentan aprovecharse de él.",
    110: "Siempre me interesan las cosas mecánicas y soy bastante bueno para arreglarlas.",
    111: "A veces estoy tan enfrascado en mis pensamientos que, a no ser que salga de ellos, pierdo la noción del tiempo y desordeno o no encuentro mis cosa.",
    112: "Parece como si no pudiera confiar en más de la mitad de la gente que voy conociendo.",
    113: "Normalmente descubro que conozco a los demás mejor que ellos me conocen a mí.",
    114: "A menudo los demás dicen que mis ideas son realistas y prácticas.",
    115: "Si creo que lo merecen, hago agudas y sarcásticas observaciones a los demás.",
    116: "A veces me siento como si hubiera hecho algo malo, aunque realmente no lo haya hecho.",
    117: "Me resulta fácil hablar sobre mi vida, incluso sobre aspectos que otros considerarían muy personales.",
    118: "Me gusta diseñar modos por los que el mundo pudiera cambiar y mejorar.",
    119: "Tiendo a ser muy sensible y preocuparme mucho acerca de algo que he hecho.",
    120: "En el periódico que acostumbro a hojear me intereso más por:",
    121: "Preferiría emplear una tarde libre en:",
    122: "Cuando hay algo molesto que hacer, prefiero:",
    123: "Prefiero tomar la comida de medio día:",
    124: "Soy paciente con las personas, incluso cuando no son corteses y consideradas con mis sentimientos.",
    125: "Cuando hago algo, normalmente me tomo tiempo para pensar antes en todo lo que necesito para la tarea.",
    126: "Me siento molesto cuando la gente emplea mucho tiempo para explicar algo.",
    127: "Mis amigos probablemente me describen como una persona.",
    128: "Cuando algo me perturba, normalmente me olvido pronto de ello.",
    129: "Como afición agradable prefiero:",
    130: "Creo que debo reclamar si en el restaurant recibo mal servicio o alimentos deficientes.",
    131: "Tengo más cambios de humor que la mayoría de las personas que conozco.",
    132: "Cuando los demás no ven las cosas como la veo yo, normalmente logro convencerlos.",
    133: "Creo que ser libre para ser lo que desee es más importante que tener buenos modales y respetar las normas.",
    134: "Me encanta hacer reír a la gente con historias ingeniosas.",
    135: "Me considero una persona socialmente muy atrevida y comunicativa.",
    136: "Si una persona es lo suficientemente lista para eludir las normas sin que parezca que las incumple:",
    137: "Cuando me uno a un nuevo grupo, normalmente encajo pronto.",
    138: "Prefiero leer historias rudas o de acción realista más que novelas sentimentales e imaginativas.",
    139: "Sospecho que la persona que se muestra abiertamente amigable conmigo pueda ser desleal cuando yo no esté delante.",
    140: "Cuando era niño empleaba la mayor parte de mi tiempo en:",
    141: "Muchas personas son demasiado quisquillosas y sensibles, y por su propio bien deberían “endurecerse”.",
    142: "Me muestro tan interesado en pensar en las ideas que a veces paso por alto los detalles prácticos.",
    143: "Si alguien me hace una pregunta demasiado personal intento cuidadosamente evitar contestarla.",
    144: "Cuando me piden hacer una tarea voluntaria digo que estoy demasiado ocupado.",
    145: "Mis amigos me consideran una persona algo abstraída y no siempre práctica.",
    146: "Me siento muy abatido cuando la gente me critica en un grupo.",
    147: "Les surgen más problemas a quienes:",
    148: "Soy muy cuidadoso cuando se trata de elegir a alguien con quien “abrirme” francamente.",
    149: "Me gusta más intentar nuevos modos de hacer las cosas que seguir caminos ya conocidos.",
    150: "Los demás dicen que suelo ser demasiado critico conmigo mismo.",
    151: "Generalmente me gusta más una comida si contiene alimentos familiares y cotidianos que si tiene alimentos poco corrientes.",
    152: "Puedo pasar fácilmente una mañana entera sin tener necesidad de hablar con alguien.",
    153: "Deseo ayudar a las personas.",
    154: "Yo creo que:",
    155: "Me resulta difícil ser paciente cuando la gente me critica.",
    156: "Prefiero los momentos en que hay gente a mí alrededor.",
    157: "Cuando realizo una tarea no me encuentro satisfecho a no ser que ponga especial atención incluso a los pequeños detalles.",
    158: "Algunas veces me “ sacan de quicio” de un modo insoportable pequeñas cosas, aunque reconozca que son triviales.",
    159: "Me gusta más escuchar a la gente hablar de sus sentimientos personales que de otros temas.",
    160: "Hay ocasiones en que no me siento de humor para ver a nadie.",
    161: "Me gustaría más ser consejero orientador que arquitecto.",
    162: "En mi vida cotidiana casi nunca me encuentro con problemas que no puedo afrontar.",
    163: "Cuando las personas hacen algo que me molesta, normalmente:",
    164: "Yo creo más en:",
    165: "Me gusta que haya alguna competitividad en las cosas que hago.",
    166: "La mayoría de las normas se han hecho para no cumplirlas cuando haya buenas razones para ello.",
    167: "Me cuesta bastante hablar delante de un grupo numeroso de personas.",
    168: "Preferiría un hogar en el que:",
    169: "En las reuniones sociales suelo sentirme tímido e inseguro de mí mismo.",
    170: "En la televisión prefiero:",
    171: "“Minuto” es a “hora” como “Segundo” es a:",
    172: "“Renacuajo” es a “rana” como “larva” es a:",
    173: "“Jamón” es a “cerdo” como “chuleta” es a:",
    174: "“Hielo” es a “agua” como “roca” es a:",
    175: "“Mejor” es a “pésimo” como “peor” es a:",
    176: "Cual de las tres palabras indica algo diferente de las otras dos:",
    177: "¿Cuál de las tres palabras indica algo diferente de las otras dos?",
    178: "Lo opuesto de “correcto” es lo opuesto de:",
    179: "¿Cuál de las tres palabras indica algo diferente de las otras dos?",
    180: "Lo opuesto de lo opuesto de “inexacto” es:",
    181: "¿Qué número debe seguir al final de éstos?  1 – 4 – 9 – 16 ....",
    182: "¿Qué letra debe seguir al final de éstas? A – B – D – G ....",
    183: "¿Qué letra debe seguir al final de éstas?   E – I – L ....",
    184: "¿Qué número debe seguir al final de éstos?  1/12 , 1/6 , 1/3 , 2/3",
    185: "¿Qué número debe seguir al final de éstos?  1 2 0 3 –1....",
}

# --- 4. Configuración Manual de Preguntas (Mapping) ---
# Se asigna manualmente la opción correcta a cada una de las 185 preguntas
# reemplazando el bucle automático que fallaba con claves repetidas.
QUESTIONS_CONFIG = {
    1: {"text": TEXTOS_PREGUNTAS[1], "option_set": "MAQUINAS_REGISTROS", "factor": QUESTIONS_TO_FACTOR_MAP[1]},
    2: {"text": TEXTOS_PREGUNTAS[2], "option_set": "VERDADERO_FALSO_1_3", "factor": QUESTIONS_TO_FACTOR_MAP[2]},
    3: {"text": TEXTOS_PREGUNTAS[3], "option_set": "SENALAR_PASAR", "factor": QUESTIONS_TO_FACTOR_MAP[3]},
    4: {"text": TEXTOS_PREGUNTAS[4], "option_set": "VERDADERO_FALSO_1_3", "factor": QUESTIONS_TO_FACTOR_MAP[4]},
    5: {"text": TEXTOS_PREGUNTAS[5], "option_set": "VERDADERO_FALSO_1_3", "factor": QUESTIONS_TO_FACTOR_MAP[5]},
    6: {"text": TEXTOS_PREGUNTAS[6], "option_set": "VERDADERO_FALSO_1_3", "factor": QUESTIONS_TO_FACTOR_MAP[6]},
    7: {"text": TEXTOS_PREGUNTAS[7], "option_set": "CAPACIDAD_TALENTO", "factor": QUESTIONS_TO_FACTOR_MAP[7]},
    8: {"text": TEXTOS_PREGUNTAS[8], "option_set": "INGENIERO_ESCRITOR", "factor": QUESTIONS_TO_FACTOR_MAP[8]},
    9: {"text": TEXTOS_PREGUNTAS[9], "option_set": "VERDADERO_FALSO_1_3", "factor": QUESTIONS_TO_FACTOR_MAP[9]},
    10: {"text": TEXTOS_PREGUNTAS[10], "option_set": "VERDADERO_FALSO_1_3", "factor": QUESTIONS_TO_FACTOR_MAP[10]},
    11: {"text": TEXTOS_PREGUNTAS[11], "option_set": "SI_NO_1_3", "factor": QUESTIONS_TO_FACTOR_MAP[11]},
    12: {"text": TEXTOS_PREGUNTAS[12], "option_set": "VERDADERO_FALSO_1_3", "factor": QUESTIONS_TO_FACTOR_MAP[12]},
    13: {"text": TEXTOS_PREGUNTAS[13], "option_set": "VERDADERO_FALSO_1_3", "factor": QUESTIONS_TO_FACTOR_MAP[13]},
    14: {"text": TEXTOS_PREGUNTAS[14], "option_set": "VERDADERO_FALSO_1_3", "factor": QUESTIONS_TO_FACTOR_MAP[14]},
    15: {"text": TEXTOS_PREGUNTAS[15], "option_set": "FACILIDAD_REMEDIO", "factor": QUESTIONS_TO_FACTOR_MAP[15]},
    16: {"text": TEXTOS_PREGUNTAS[16], "option_set": "ALGUNAS_NUNCA", "factor": QUESTIONS_TO_FACTOR_MAP[16]},
    17: {"text": TEXTOS_PREGUNTAS[17], "option_set": "CASINUNCA_AMENUDO", "factor": QUESTIONS_TO_FACTOR_MAP[17]},
    18: {"text": TEXTOS_PREGUNTAS[18], "option_set": "COMENTAR_GUARDAR", "factor": QUESTIONS_TO_FACTOR_MAP[18]},
    19: {"text": TEXTOS_PREGUNTAS[19], "option_set": "CASINUNCA_AMENUDO", "factor": QUESTIONS_TO_FACTOR_MAP[19]},
    20: {"text": TEXTOS_PREGUNTAS[20], "option_set": "SI_NO_1_3", "factor": QUESTIONS_TO_FACTOR_MAP[20]},
    21: {"text": TEXTOS_PREGUNTAS[21], "option_set": "NO_PERTURBABA_DANO", "factor": QUESTIONS_TO_FACTOR_MAP[21]},
    22: {"text": TEXTOS_PREGUNTAS[22], "option_set": "DISCUTIR_CAMBIAR", "factor": QUESTIONS_TO_FACTOR_MAP[22]},
    23: {"text": TEXTOS_PREGUNTAS[23], "option_set": "VERDADERO_FALSO_1_3", "factor": QUESTIONS_TO_FACTOR_MAP[23]},
    24: {"text": TEXTOS_PREGUNTAS[24], "option_set": "VERDADERO_EVITAR", "factor": QUESTIONS_TO_FACTOR_MAP[24]},
    25: {"text": TEXTOS_PREGUNTAS[25], "option_set": "OTROS_SOLO", "factor": QUESTIONS_TO_FACTOR_MAP[25]},
    26: {"text": TEXTOS_PREGUNTAS[26], "option_set": "RARAS_AMENUDO", "factor": QUESTIONS_TO_FACTOR_MAP[26]},
    27: {"text": TEXTOS_PREGUNTAS[27], "option_set": "VERDADERO_FALSO_1_3", "factor": QUESTIONS_TO_FACTOR_MAP[27]},
    28: {"text": TEXTOS_PREGUNTAS[28], "option_set": "VERDADERO_FALSO_1_3", "factor": QUESTIONS_TO_FACTOR_MAP[28]},
    29: {"text": TEXTOS_PREGUNTAS[29], "option_set": "VERDADERO_FALSO_1_3", "factor": QUESTIONS_TO_FACTOR_MAP[29]},
    30: {"text": TEXTOS_PREGUNTAS[30], "option_set": "MOLESTARIA_CONTENTO", "factor": QUESTIONS_TO_FACTOR_MAP[30]},
    31: {"text": TEXTOS_PREGUNTAS[31], "option_set": "OFICINA", "factor": QUESTIONS_TO_FACTOR_MAP[31]},
    32: {"text": TEXTOS_PREGUNTAS[32], "option_set": "MARCHAR_MAL", "factor": QUESTIONS_TO_FACTOR_MAP[32]},
    33: {"text": TEXTOS_PREGUNTAS[33], "option_set": "VERDADERO_FALSO_1_3", "factor": QUESTIONS_TO_FACTOR_MAP[33]},
    34: {"text": TEXTOS_PREGUNTAS[34], "option_set": "VERDADERO_FALSO_1_3", "factor": QUESTIONS_TO_FACTOR_MAP[34]},
    35: {"text": TEXTOS_PREGUNTAS[35], "option_set": "VERDADERO_FALSO_1_3", "factor": QUESTIONS_TO_FACTOR_MAP[35]},
    36: {"text": TEXTOS_PREGUNTAS[36], "option_set": "VERDADERO_FALSO_1_3", "factor": QUESTIONS_TO_FACTOR_MAP[36]},
    37: {"text": TEXTOS_PREGUNTAS[37], "option_set": "TARDE_1", "factor": QUESTIONS_TO_FACTOR_MAP[37]},
    38: {"text": TEXTOS_PREGUNTAS[38], "option_set": "SI_NO_1_3", "factor": QUESTIONS_TO_FACTOR_MAP[38]},
    39: {"text": TEXTOS_PREGUNTAS[39], "option_set": "VERDADERO_FALSO_1_3", "factor": QUESTIONS_TO_FACTOR_MAP[39]},
    40: {"text": TEXTOS_PREGUNTAS[40], "option_set": "VERDADERO_FALSO_1_3", "factor": QUESTIONS_TO_FACTOR_MAP[40]},
    41: {"text": TEXTOS_PREGUNTAS[41], "option_set": "VERDADERO_FALSO_1_3", "factor": QUESTIONS_TO_FACTOR_MAP[41]},
    42: {"text": TEXTOS_PREGUNTAS[42], "option_set": "EJERCICIO", "factor": QUESTIONS_TO_FACTOR_MAP[42]},
    43: {"text": TEXTOS_PREGUNTAS[43], "option_set": "VERDADERO_FALSO_1_3", "factor": QUESTIONS_TO_FACTOR_MAP[43]},
    44: {"text": TEXTOS_PREGUNTAS[44], "option_set": "VERDADERO_FALSO_1_3", "factor": QUESTIONS_TO_FACTOR_MAP[44]},
    45: {"text": TEXTOS_PREGUNTAS[45], "option_set": "CASINUNCA_AMENUDO", "factor": QUESTIONS_TO_FACTOR_MAP[45]},
    46: {"text": TEXTOS_PREGUNTAS[46], "option_set": "PERSONAS", "factor": QUESTIONS_TO_FACTOR_MAP[46]},
    47: {"text": TEXTOS_PREGUNTAS[47], "option_set": "VERDADERO_FALSO_1_3", "factor": QUESTIONS_TO_FACTOR_MAP[47]},
    48: {"text": TEXTOS_PREGUNTAS[48], "option_set": "VERDADERO_FALSO_1_3", "factor": QUESTIONS_TO_FACTOR_MAP[48]},
    49: {"text": TEXTOS_PREGUNTAS[49], "option_set": "VERDADERO_FALSO_1_3", "factor": QUESTIONS_TO_FACTOR_MAP[49]},
    50: {"text": TEXTOS_PREGUNTAS[50], "option_set": "VERDADERO_FALSO_1_3", "factor": QUESTIONS_TO_FACTOR_MAP[50]},
    51: {"text": TEXTOS_PREGUNTAS[51], "option_set": "DECISION", "factor": QUESTIONS_TO_FACTOR_MAP[51]},
    52: {"text": TEXTOS_PREGUNTAS[52], "option_set": "PERSONAS_DIF", "factor": QUESTIONS_TO_FACTOR_MAP[52]},
    53: {"text": TEXTOS_PREGUNTAS[53], "option_set": "SIGNIFICADO", "factor": QUESTIONS_TO_FACTOR_MAP[53]},
    54: {"text": TEXTOS_PREGUNTAS[54], "option_set": "VERDADERO_FALSO_1_3", "factor": QUESTIONS_TO_FACTOR_MAP[54]},
    55: {"text": TEXTOS_PREGUNTAS[55], "option_set": "MUNDO", "factor": QUESTIONS_TO_FACTOR_MAP[55]},
    56: {"text": TEXTOS_PREGUNTAS[56], "option_set": "JUEGOS", "factor": QUESTIONS_TO_FACTOR_MAP[56]},
    57: {"text": TEXTOS_PREGUNTAS[57], "option_set": "VERDADERO_FALSO_1_3", "factor": QUESTIONS_TO_FACTOR_MAP[57]},
    58: {"text": TEXTOS_PREGUNTAS[58], "option_set": "VERDADERO_FALSO_1_3", "factor": QUESTIONS_TO_FACTOR_MAP[58]},
    59: {"text": TEXTOS_PREGUNTAS[59], "option_set": "VERDADERO_FALSO_1_3", "factor": QUESTIONS_TO_FACTOR_MAP[59]},
    60: {"text": TEXTOS_PREGUNTAS[60], "option_set": "INTERRUMPE", "factor": QUESTIONS_TO_FACTOR_MAP[60]},
    61: {"text": TEXTOS_PREGUNTAS[61], "option_set": "VERDADERO_FALSO_1_3", "factor": QUESTIONS_TO_FACTOR_MAP[61]},
    62: {"text": TEXTOS_PREGUNTAS[62], "option_set": "VERDADERO_FALSO_1_3", "factor": QUESTIONS_TO_FACTOR_MAP[62]},
    63: {"text": TEXTOS_PREGUNTAS[63], "option_set": "VERDADERO_FALSO_1_3", "factor": QUESTIONS_TO_FACTOR_MAP[63]},
    64: {"text": TEXTOS_PREGUNTAS[64], "option_set": "VERDADERO_FALSO_1_3", "factor": QUESTIONS_TO_FACTOR_MAP[64]},
    65: {"text": TEXTOS_PREGUNTAS[65], "option_set": "VERDADERO_FALSO_1_3", "factor": QUESTIONS_TO_FACTOR_MAP[65]},
    66: {"text": TEXTOS_PREGUNTAS[66], "option_set": "VERDADERO_FALSO_1_3", "factor": QUESTIONS_TO_FACTOR_MAP[66]},
    67: {"text": TEXTOS_PREGUNTAS[67], "option_set": "EMOCIONALES", "factor": QUESTIONS_TO_FACTOR_MAP[67]},
    68: {"text": TEXTOS_PREGUNTAS[68], "option_set": "VERDADERO_FALSO_1_3", "factor": QUESTIONS_TO_FACTOR_MAP[68]},
    69: {"text": TEXTOS_PREGUNTAS[69], "option_set": "VERDADERO_FALSO_1_3", "factor": QUESTIONS_TO_FACTOR_MAP[69]},
    70: {"text": TEXTOS_PREGUNTAS[70], "option_set": "VESTIR", "factor": QUESTIONS_TO_FACTOR_MAP[70]},
    71: {"text": TEXTOS_PREGUNTAS[71], "option_set": "VERDADERO_FALSO_1_3", "factor": QUESTIONS_TO_FACTOR_MAP[71]},
    72: {"text": TEXTOS_PREGUNTAS[72], "option_set": "SEGURIDAD", "factor": QUESTIONS_TO_FACTOR_MAP[72]},
    73: {"text": TEXTOS_PREGUNTAS[73], "option_set": "EXTRAÑOS", "factor": QUESTIONS_TO_FACTOR_MAP[73]},
    74: {"text": TEXTOS_PREGUNTAS[74], "option_set": "PERIODICO_1", "factor": QUESTIONS_TO_FACTOR_MAP[74]},
    75: {"text": TEXTOS_PREGUNTAS[75], "option_set": "PEQUEÑAS", "factor": QUESTIONS_TO_FACTOR_MAP[75]},
    76: {"text": TEXTOS_PREGUNTAS[76], "option_set": "GUARDIA", "factor": QUESTIONS_TO_FACTOR_MAP[76]},
    77: {"text": TEXTOS_PREGUNTAS[77], "option_set": "CONTEMPLAR", "factor": QUESTIONS_TO_FACTOR_MAP[77]},
    78: {"text": TEXTOS_PREGUNTAS[78], "option_set": "PEREZOSA", "factor": QUESTIONS_TO_FACTOR_MAP[78]},
    79: {"text": TEXTOS_PREGUNTAS[79], "option_set": "IDEAS", "factor": QUESTIONS_TO_FACTOR_MAP[79]},
    80: {"text": TEXTOS_PREGUNTAS[80], "option_set": "INFO", "factor": QUESTIONS_TO_FACTOR_MAP[80]},
    81: {"text": TEXTOS_PREGUNTAS[81], "option_set": "ATENCION", "factor": QUESTIONS_TO_FACTOR_MAP[81]},
    82: {"text": TEXTOS_PREGUNTAS[82], "option_set": "CRITICA", "factor": QUESTIONS_TO_FACTOR_MAP[82]},
    83: {"text": TEXTOS_PREGUNTAS[83], "option_set": "INTERESANTE", "factor": QUESTIONS_TO_FACTOR_MAP[83]},
    84: {"text": TEXTOS_PREGUNTAS[84], "option_set": "TRATAR_GENTE", "factor": QUESTIONS_TO_FACTOR_MAP[84]},
    85: {"text": TEXTOS_PREGUNTAS[85], "option_set": "SITIO", "factor": QUESTIONS_TO_FACTOR_MAP[85]},
    86: {"text": TEXTOS_PREGUNTAS[86], "option_set": "GUSTO_GENTE", "factor": QUESTIONS_TO_FACTOR_MAP[86]},
    87: {"text": TEXTOS_PREGUNTAS[87], "option_set": "ALREDEDOR", "factor": QUESTIONS_TO_FACTOR_MAP[87]},
    88: {"text": TEXTOS_PREGUNTAS[88], "option_set": "TRABAJO_FAMILIAR", "factor": QUESTIONS_TO_FACTOR_MAP[88]},
    89: {"text": TEXTOS_PREGUNTAS[89], "option_set": "TRABAJO_SOLO", "factor": QUESTIONS_TO_FACTOR_MAP[89]},
    90: {"text": TEXTOS_PREGUNTAS[90], "option_set": "HABITACION", "factor": QUESTIONS_TO_FACTOR_MAP[90]},
    91: {"text": TEXTOS_PREGUNTAS[91], "option_set": "PACIENTE", "factor": QUESTIONS_TO_FACTOR_MAP[91]},
    92: {"text": TEXTOS_PREGUNTAS[92], "option_set": "UNIRME", "factor": QUESTIONS_TO_FACTOR_MAP[92]},
    93: {"text": TEXTOS_PREGUNTAS[93], "option_set": "PERFECCIONISTA", "factor": QUESTIONS_TO_FACTOR_MAP[93]},
    94: {"text": TEXTOS_PREGUNTAS[94], "option_set": "COLA", "factor": QUESTIONS_TO_FACTOR_MAP[94]},
    95: {"text": TEXTOS_PREGUNTAS[95], "option_set": "INTENCIONES", "factor": QUESTIONS_TO_FACTOR_MAP[95]},
    96: {"text": TEXTOS_PREGUNTAS[96], "option_set": "EMOCIONES", "factor": QUESTIONS_TO_FACTOR_MAP[96]},
    97: {"text": TEXTOS_PREGUNTAS[97], "option_set": "DEPRIMAN", "factor": QUESTIONS_TO_FACTOR_MAP[97]},
    98: {"text": TEXTOS_PREGUNTAS[98], "option_set": "INVENTO", "factor": QUESTIONS_TO_FACTOR_MAP[98]},
    99: {"text": TEXTOS_PREGUNTAS[99], "option_set": "CORTES", "factor": QUESTIONS_TO_FACTOR_MAP[99]},
    100: {"text": TEXTOS_PREGUNTAS[100], "option_set": "ESPECTACULO", "factor": QUESTIONS_TO_FACTOR_MAP[100]},
    101: {"text": TEXTOS_PREGUNTAS[101], "option_set": "PEQUEÑAS", "factor": QUESTIONS_TO_FACTOR_MAP[101]}, # Mismatch fix: A veces/Raras veces
    102: {"text": TEXTOS_PREGUNTAS[102], "option_set": "CIUDAD", "factor": QUESTIONS_TO_FACTOR_MAP[102]},
    103: {"text": TEXTOS_PREGUNTAS[103], "option_set": "ANIMADA", "factor": QUESTIONS_TO_FACTOR_MAP[103]},
    104: {"text": TEXTOS_PREGUNTAS[104], "option_set": "BANCO", "factor": QUESTIONS_TO_FACTOR_MAP[104]},
    105: {"text": TEXTOS_PREGUNTAS[105], "option_set": "TIMIDEZ", "factor": QUESTIONS_TO_FACTOR_MAP[105]},
    106: {"text": TEXTOS_PREGUNTAS[106], "option_set": "PROFESORES", "factor": QUESTIONS_TO_FACTOR_MAP[106]},
    107: {"text": TEXTOS_PREGUNTAS[107], "option_set": "PESO", "factor": QUESTIONS_TO_FACTOR_MAP[107]},
    108: {"text": TEXTOS_PREGUNTAS[108], "option_set": "POEMA", "factor": QUESTIONS_TO_FACTOR_MAP[108]},
    109: {"text": TEXTOS_PREGUNTAS[109], "option_set": "FRANCO", "factor": QUESTIONS_TO_FACTOR_MAP[109]},
    110: {"text": TEXTOS_PREGUNTAS[110], "option_set": "MECANICAS", "factor": QUESTIONS_TO_FACTOR_MAP[110]},
    111: {"text": TEXTOS_PREGUNTAS[111], "option_set": "PENSAMIENTOS", "factor": QUESTIONS_TO_FACTOR_MAP[111]},
    112: {"text": TEXTOS_PREGUNTAS[112], "option_set": "CONFIAR", "factor": QUESTIONS_TO_FACTOR_MAP[112]},
    113: {"text": TEXTOS_PREGUNTAS[113], "option_set": "CONOZCO", "factor": QUESTIONS_TO_FACTOR_MAP[113]},
    114: {"text": TEXTOS_PREGUNTAS[114], "option_set": "IDEAS_PRACTICAS", "factor": QUESTIONS_TO_FACTOR_MAP[114]},
    115: {"text": TEXTOS_PREGUNTAS[115], "option_set": "INTENCIONES", "factor": QUESTIONS_TO_FACTOR_MAP[115]}, # Mismatch fix: A veces/Nunca
    116: {"text": TEXTOS_PREGUNTAS[116], "option_set": "HECHO_MALO", "factor": QUESTIONS_TO_FACTOR_MAP[116]},
    117: {"text": TEXTOS_PREGUNTAS[117], "option_set": "PERSONALES", "factor": QUESTIONS_TO_FACTOR_MAP[117]},
    118: {"text": TEXTOS_PREGUNTAS[118], "option_set": "MODOS", "factor": QUESTIONS_TO_FACTOR_MAP[118]},
    119: {"text": TEXTOS_PREGUNTAS[119], "option_set": "SENSIBLE", "factor": QUESTIONS_TO_FACTOR_MAP[119]},
    120: {"text": TEXTOS_PREGUNTAS[120], "option_set": "PERIODICO_2", "factor": QUESTIONS_TO_FACTOR_MAP[120]},
    121: {"text": TEXTOS_PREGUNTAS[121], "option_set": "TARDE_2", "factor": QUESTIONS_TO_FACTOR_MAP[121]},
    122: {"text": TEXTOS_PREGUNTAS[122], "option_set": "MOLESTO", "factor": QUESTIONS_TO_FACTOR_MAP[122]},
    123: {"text": TEXTOS_PREGUNTAS[123], "option_set": "TOMAR_COMIDA", "factor": QUESTIONS_TO_FACTOR_MAP[123]},
    124: {"text": TEXTOS_PREGUNTAS[124], "option_set": "PACIENTE_PERSONAS", "factor": QUESTIONS_TO_FACTOR_MAP[124]},
    125: {"text": TEXTOS_PREGUNTAS[125], "option_set": "PENSAR_ANTES", "factor": QUESTIONS_TO_FACTOR_MAP[125]},
    126: {"text": TEXTOS_PREGUNTAS[126], "option_set": "EXPLICAR_ALGO", "factor": QUESTIONS_TO_FACTOR_MAP[126]},
    127: {"text": TEXTOS_PREGUNTAS[127], "option_set": "DESCRIBEN_COMO", "factor": QUESTIONS_TO_FACTOR_MAP[127]},
    128: {"text": TEXTOS_PREGUNTAS[128], "option_set": "PERTURBA", "factor": QUESTIONS_TO_FACTOR_MAP[128]},
    129: {"text": TEXTOS_PREGUNTAS[129], "option_set": "AFICION_AGRADABLE", "factor": QUESTIONS_TO_FACTOR_MAP[129]},
    130: {"text": TEXTOS_PREGUNTAS[130], "option_set": "RESTAURANT", "factor": QUESTIONS_TO_FACTOR_MAP[130]},
    131: {"text": TEXTOS_PREGUNTAS[131], "option_set": "CAMBIOS_HUMOR", "factor": QUESTIONS_TO_FACTOR_MAP[131]},
    132: {"text": TEXTOS_PREGUNTAS[132], "option_set": "VEN_COSAS", "factor": QUESTIONS_TO_FACTOR_MAP[132]},
    133: {"text": TEXTOS_PREGUNTAS[133], "option_set": "SER_LIBRE", "factor": QUESTIONS_TO_FACTOR_MAP[133]},
    134: {"text": TEXTOS_PREGUNTAS[134], "option_set": "HACER_REIR", "factor": QUESTIONS_TO_FACTOR_MAP[134]},
    135: {"text": TEXTOS_PREGUNTAS[135], "option_set": "SOCIALMENTE_ATREVIDA", "factor": QUESTIONS_TO_FACTOR_MAP[135]},
    136: {"text": TEXTOS_PREGUNTAS[136], "option_set": "ELUDIR", "factor": QUESTIONS_TO_FACTOR_MAP[136]},
    137: {"text": TEXTOS_PREGUNTAS[137], "option_set": "NUEVO_GRUPO", "factor": QUESTIONS_TO_FACTOR_MAP[137]},
    138: {"text": TEXTOS_PREGUNTAS[138], "option_set": "LEER_HISTORIAS", "factor": QUESTIONS_TO_FACTOR_MAP[138]},
    139: {"text": TEXTOS_PREGUNTAS[139], "option_set": "SOSPECHO", "factor": QUESTIONS_TO_FACTOR_MAP[139]},
    140: {"text": TEXTOS_PREGUNTAS[140], "option_set": "TIEMPO_EN", "factor": QUESTIONS_TO_FACTOR_MAP[140]},
    141: {"text": TEXTOS_PREGUNTAS[141], "option_set": "QUISQUILLOSAS", "factor": QUESTIONS_TO_FACTOR_MAP[141]},
    142: {"text": TEXTOS_PREGUNTAS[142], "option_set": "DETALLES_PRACTICOS", "factor": QUESTIONS_TO_FACTOR_MAP[142]},
    143: {"text": TEXTOS_PREGUNTAS[143], "option_set": "PREGUNTA_PERSONAL", "factor": QUESTIONS_TO_FACTOR_MAP[143]},
    144: {"text": TEXTOS_PREGUNTAS[144], "option_set": "TAREA_VOLUNTARIA", "factor": QUESTIONS_TO_FACTOR_MAP[144]},
    145: {"text": TEXTOS_PREGUNTAS[145], "option_set": "ABSTRAIDO", "factor": QUESTIONS_TO_FACTOR_MAP[145]},
    146: {"text": TEXTOS_PREGUNTAS[146], "option_set": "ABATIDO_CRITICAS", "factor": QUESTIONS_TO_FACTOR_MAP[146]},
    147: {"text": TEXTOS_PREGUNTAS[147], "option_set": "SURGEN_PROBLEMAS", "factor": QUESTIONS_TO_FACTOR_MAP[147]},
    148: {"text": TEXTOS_PREGUNTAS[148], "option_set": "ABRIRME", "factor": QUESTIONS_TO_FACTOR_MAP[148]},
    149: {"text": TEXTOS_PREGUNTAS[149], "option_set": "NUEVOS_MODOS", "factor": QUESTIONS_TO_FACTOR_MAP[149]},
    150: {"text": TEXTOS_PREGUNTAS[150], "option_set": "CRITICO", "factor": QUESTIONS_TO_FACTOR_MAP[150]},
    151: {"text": TEXTOS_PREGUNTAS[151], "option_set": "COMIDA_ALIMENTOS", "factor": QUESTIONS_TO_FACTOR_MAP[151]},
    152: {"text": TEXTOS_PREGUNTAS[152], "option_set": "SIN_HABLAR", "factor": QUESTIONS_TO_FACTOR_MAP[152]},
    153: {"text": TEXTOS_PREGUNTAS[153], "option_set": "AYUDAR_PERSONAS", "factor": QUESTIONS_TO_FACTOR_MAP[153]}, # Fallback to available key
    154: {"text": TEXTOS_PREGUNTAS[154], "option_set": "CREO_QUE", "factor": QUESTIONS_TO_FACTOR_MAP[154]},
    155: {"text": TEXTOS_PREGUNTAS[155], "option_set": "DIFICIL_PACIENTE", "factor": QUESTIONS_TO_FACTOR_MAP[155]},
    156: {"text": TEXTOS_PREGUNTAS[156], "option_set": "PREFIERO_GENTE", "factor": QUESTIONS_TO_FACTOR_MAP[156]},
    157: {"text": TEXTOS_PREGUNTAS[157], "option_set": "TAREA_SATISFECHO", "factor": QUESTIONS_TO_FACTOR_MAP[157]},
    158: {"text": TEXTOS_PREGUNTAS[158], "option_set": "SACAN_DE_QUICIO", "factor": QUESTIONS_TO_FACTOR_MAP[158]},
    159: {"text": TEXTOS_PREGUNTAS[159], "option_set": "ESCUCHAR_GENTE", "factor": QUESTIONS_TO_FACTOR_MAP[159]},
    160: {"text": TEXTOS_PREGUNTAS[160], "option_set": "HUMOR_VER", "factor": QUESTIONS_TO_FACTOR_MAP[160]},
    161: {"text": TEXTOS_PREGUNTAS[161], "option_set": "CONSEJERO_ORIENTADOR", "factor": QUESTIONS_TO_FACTOR_MAP[161]},
    162: {"text": TEXTOS_PREGUNTAS[162], "option_set": "VIDA_COTIDIANA", "factor": QUESTIONS_TO_FACTOR_MAP[162]},
    163: {"text": TEXTOS_PREGUNTAS[163], "option_set": "PERSONAS_MOLESTAN", "factor": QUESTIONS_TO_FACTOR_MAP[163]},
    164: {"text": TEXTOS_PREGUNTAS[164], "option_set": "CREO_MAS_EN", "factor": QUESTIONS_TO_FACTOR_MAP[164]},
    165: {"text": TEXTOS_PREGUNTAS[165], "option_set": "COMPETITIVIDAD_COSAS", "factor": QUESTIONS_TO_FACTOR_MAP[165]},
    166: {"text": TEXTOS_PREGUNTAS[166], "option_set": "MAYORIA_NORMAS", "factor": QUESTIONS_TO_FACTOR_MAP[166]},
    167: {"text": TEXTOS_PREGUNTAS[167], "option_set": "CUESTA_HABLAR", "factor": QUESTIONS_TO_FACTOR_MAP[167]},
    168: {"text": TEXTOS_PREGUNTAS[168], "option_set": "HOGAR_EN_QUE", "factor": QUESTIONS_TO_FACTOR_MAP[168]},
    169: {"text": TEXTOS_PREGUNTAS[169], "option_set": "REUNIONES_SOCIALES", "factor": QUESTIONS_TO_FACTOR_MAP[169]},
    170: {"text": TEXTOS_PREGUNTAS[170], "option_set": "TELEVISION", "factor": QUESTIONS_TO_FACTOR_MAP[170]},
    171: {"text": TEXTOS_PREGUNTAS[171], "option_set": "MINUTO_A_HORA", "factor": QUESTIONS_TO_FACTOR_MAP[171]},
    172: {"text": TEXTOS_PREGUNTAS[172], "option_set": "RENACUAJO", "factor": QUESTIONS_TO_FACTOR_MAP[172]},
    173: {"text": TEXTOS_PREGUNTAS[173], "option_set": "JAMON", "factor": QUESTIONS_TO_FACTOR_MAP[173]},
    174: {"text": TEXTOS_PREGUNTAS[174], "option_set": "HIELO", "factor": QUESTIONS_TO_FACTOR_MAP[174]},
    175: {"text": TEXTOS_PREGUNTAS[175], "option_set": "MEJOR", "factor": QUESTIONS_TO_FACTOR_MAP[175]},
    176: {"text": TEXTOS_PREGUNTAS[176], "option_set": "TRES_PALABRAS", "factor": QUESTIONS_TO_FACTOR_MAP[176]},
    177: {"text": TEXTOS_PREGUNTAS[177], "option_set": "TRES_P_GATO", "factor": QUESTIONS_TO_FACTOR_MAP[177]},
    178: {"text": TEXTOS_PREGUNTAS[178], "option_set": "OPUESTO_CORRECTO", "factor": QUESTIONS_TO_FACTOR_MAP[178]},
    179: {"text": TEXTOS_PREGUNTAS[179], "option_set": "TRES_P_PROB", "factor": QUESTIONS_TO_FACTOR_MAP[179]},
    180: {"text": TEXTOS_PREGUNTAS[180], "option_set": "OPUESTO_INEXACTO", "factor": QUESTIONS_TO_FACTOR_MAP[180]},
    181: {"text": TEXTOS_PREGUNTAS[181], "option_set": "NUMERO_SIGUE", "factor": QUESTIONS_TO_FACTOR_MAP[181]},
    182: {"text": TEXTOS_PREGUNTAS[182], "option_set": "LETRA_SIGUE", "factor": QUESTIONS_TO_FACTOR_MAP[182]},
    183: {"text": TEXTOS_PREGUNTAS[183], "option_set": "LETRA_SIGUE_2", "factor": QUESTIONS_TO_FACTOR_MAP[183]},
    184: {"text": TEXTOS_PREGUNTAS[184], "option_set": "NUMERO_SIGUE_2", "factor": QUESTIONS_TO_FACTOR_MAP[184]},
    185: {"text": TEXTOS_PREGUNTAS[185], "option_set": "NUMERO_SIGUE_3", "factor": QUESTIONS_TO_FACTOR_MAP[185]},
}

# --- 5. Tablas y Baremos (Sin cambios) ---
DECATIPO_TABLES = {
    "MASCULINO": {
        'A': {0:1, 1:1, 2:1, 3:1, 4:2, 5:2, 6:3, 7:3, 8:4, 9:4, 10:5, 11:5, 12:6, 13:6, 14:7, 15:7, 16:8, 17:8, 18:9, 19:9, 20:10, 21:10, 22:10},
        'B': {0:1, 1:1, 2:2, 3:2, 4:3, 5:4, 6:5, 7:6, 8:7, 9:8, 10:9, 11:10, 12:10, 13:10, 14:10, 15:10},
        'C': {0:1, 1:1, 2:1, 3:1, 4:1, 5:2, 6:2, 7:3, 8:3, 9:4, 10:4, 11:5, 12:5, 13:6, 14:6, 15:7, 16:8, 17:9, 18:9, 19:10, 20:10},
        'E': {0:1, 1:1, 2:1, 3:1, 4:1, 5:2, 6:2, 7:3, 8:3, 9:4, 10:4, 11:5, 12:5, 13:6, 14:7, 15:8, 16:9, 17:9, 18:10, 19:10, 20:10},
        'F': {0:1, 1:1, 2:1, 3:1, 4:2, 5:2, 6:3, 7:3, 8:4, 9:4, 10:5, 11:6, 12:7, 13:8, 14:8, 15:9, 16:9, 17:10, 18:10, 19:10, 20:10},
        'G': {0:1, 1:1, 2:1, 3:1, 4:2, 5:2, 6:3, 7:3, 8:4, 9:5, 10:6, 11:7, 12:8, 13:8, 14:9, 15:9, 16:10, 17:10, 18:10, 19:10, 20:10},
        'H': {0:1, 1:1, 2:1, 3:1, 4:1, 5:1, 6:1, 7:2, 8:2, 9:3, 10:3, 11:4, 12:4, 13:5, 14:5, 15:6, 16:7, 17:8, 18:9, 19:9, 20:10, 21:10, 22:10},
        'I': {0:1, 1:1, 2:1, 3:2, 4:2, 5:3, 6:4, 7:5, 8:6, 9:7, 10:8, 11:8, 12:9, 13:9, 14:9, 15:10, 16:10, 17:10, 18:10, 19:10, 20:10, 21:10, 22:10},
        'L': {0:1, 1:1, 2:1, 3:2, 4:3, 5:4, 6:5, 7:6, 8:7, 9:8, 10:8, 11:9, 12:9, 13:10, 14:10, 15:10, 16:10, 17:10, 18:10, 19:10, 20:10},
        'M': {0:1, 1:1, 2:1, 3:2, 4:2, 5:3, 6:3, 7:4, 8:4, 9:5, 10:5, 11:6, 12:6, 13:7, 14:7, 15:8, 16:8, 17:9, 18:9, 19:10, 20:10, 21:10, 22:10},
        'N': {0:1, 1:1, 2:1, 3:2, 4:3, 5:4, 6:5, 7:6, 8:7, 9:8, 10:8, 11:9, 12:9, 13:10, 14:10, 15:10, 16:10, 17:10, 18:10, 19:10, 20:10},
        'O': {0:1, 1:1, 2:2, 3:3, 4:4, 5:4, 6:5, 7:5, 8:6, 9:7, 10:8, 11:9, 12:9, 13:10, 14:10, 15:10, 16:10, 17:10, 18:10, 19:10, 20:10},
        'Q1': {0:1, 1:1, 2:1, 3:2, 4:2, 5:3, 6:4, 7:5, 8:6, 9:7, 10:8, 11:8, 12:9, 13:9, 14:10, 15:10, 16:10, 17:10, 18:10, 19:10, 20:10},
        'Q2': {0:1, 1:1, 2:2, 3:2, 4:3, 5:4, 6:5, 7:6, 8:7, 9:8, 10:8, 11:9, 12:9, 13:10, 14:10, 15:10, 16:10, 17:10, 18:10, 19:10, 20:10},
        'Q3': {0:1, 1:1, 2:2, 3:3, 4:4, 5:5, 6:6, 7:7, 8:8, 9:8, 10:9, 11:9, 12:9, 13:10, 14:10, 15:10, 16:10, 17:10, 18:10, 19:10, 20:10},
        'Q4': {0:1, 1:1, 2:1, 3:2, 4:2, 5:3, 6:3, 7:4, 8:4, 9:5, 10:6, 11:7, 12:7, 13:8, 14:8, 15:9, 16:9, 17:10, 18:10, 19:10, 20:10},
    },
    "FEMENINO": {
        'A': {0:1, 1:1, 2:1, 3:1, 4:1, 5:2, 6:2, 7:3, 8:3, 9:4, 10:4, 11:5, 12:6, 13:7, 14:7, 15:8, 16:8, 17:9, 18:9, 19:10, 20:10, 21:10, 22:10},
        'B': {0:1, 1:1, 2:2, 3:2, 4:3, 5:4, 6:5, 7:6, 8:7, 9:8, 10:9, 11:10, 12:10, 13:10, 14:10, 15:10},
        'C': {0:1, 1:1, 2:1, 3:1, 4:1, 5:2, 6:2, 7:3, 8:3, 9:4, 10:4, 11:5, 12:5, 13:6, 14:6, 15:7, 16:8, 17:9, 18:9, 19:10, 20:10},
        'E': {0:1, 1:1, 2:1, 3:1, 4:1, 5:2, 6:2, 7:3, 8:3, 9:4, 10:5, 11:6, 12:7, 13:7, 14:8, 15:8, 16:9, 17:9, 18:10, 19:10, 20:10},
        'F': {0:1, 1:1, 2:1, 3:1, 4:2, 5:2, 6:3, 7:3, 8:4, 9:4, 10:5, 11:5, 12:6, 13:7, 14:7, 15:8, 16:8, 17:9, 18:9, 19:10, 20:10},
        'G': {0:1, 1:1, 2:1, 3:1, 4:2, 5:2, 6:3, 7:3, 8:4, 9:5, 10:6, 11:6, 12:7, 13:7, 14:8, 15:8, 16:9, 17:9, 18:10, 19:10, 20:10},
        'H': {0:1, 1:1, 2:1, 3:1, 4:1, 5:1, 6:1, 7:1, 8:2, 9:2, 10:2, 11:3, 12:3, 13:4, 14:4, 15:5, 16:6, 17:7, 18:8, 19:9, 20:10, 21:10, 22:10},
        'I': {0:1, 1:1, 2:1, 3:2, 4:2, 5:3, 6:4, 7:4, 8:5, 9:6, 10:7, 11:8, 12:8, 13:9, 14:9, 15:9, 16:10, 17:10, 18:10, 19:10, 20:10, 21:10, 22:10},
        'L': {0:1, 1:1, 2:1, 3:1, 4:2, 5:2, 6:3, 7:4, 8:5, 9:6, 10:6, 11:7, 12:8, 13:8, 14:9, 15:9, 16:10, 17:10, 18:10, 19:10, 20:10},
        'M': {0:1, 1:1, 2:2, 3:2, 4:3, 5:3, 6:4, 7:4, 8:5, 9:5, 10:6, 11:6, 12:7, 13:7, 14:8, 15:8, 16:9, 17:9, 18:9, 19:10, 20:10, 21:10, 22:10},
        'N': {0:1, 1:1, 2:1, 3:2, 4:2, 5:3, 6:4, 7:5, 8:6, 9:7, 10:8, 11:8, 12:9, 13:9, 14:10, 15:10, 16:10, 17:10, 18:10, 19:10, 20:10},
        'O': {0:1, 1:1, 2:1, 3:2, 4:3, 5:4, 6:5, 7:6, 8:7, 9:8, 10:8, 11:9, 12:9, 13:10, 14:10, 15:10, 16:10, 17:10, 18:10, 19:10, 20:10},
        'Q1': {0:1, 1:1, 2:1, 3:2, 4:3, 5:4, 6:5, 7:6, 8:6, 9:7, 10:7, 11:8, 12:8, 13:9, 14:9, 15:10, 16:10, 17:10, 18:10, 19:10, 20:10},
        'Q2': {0:1, 1:1, 2:2, 3:3, 4:4, 5:5, 6:5, 7:6, 8:6, 9:7, 10:7, 11:8, 12:8, 13:9, 14:9, 15:10, 16:10, 17:10, 18:10, 19:10, 20:10},
        'Q3': {0:1, 1:1, 2:2, 3:3, 4:4, 5:5, 6:6, 7:7, 8:7, 9:8, 10:8, 11:9, 12:9, 13:9, 14:10, 15:10, 16:10, 17:10, 18:10, 19:10, 20:10},
        'Q4': {0:1, 1:1, 2:1, 3:2, 4:2, 5:3, 6:3, 7:4, 8:5, 9:6, 10:7, 11:7, 12:8, 13:8, 14:9, 15:9, 16:10, 17:10, 18:10, 19:10, 20:10},
    },
    "MI_IN_AQ": {
        'MI': {0:1, 1:1, 2:1, 3:2, 4:2, 5:3, 6:3, 7:4, 8:4, 9:5, 10:5, 11:6, 12:6, 13:7, 14:7, 15:8, 16:8, 17:9, 18:9, 19:10, 20:10, 21:10, 22:10, 23:10, 24:10},
        'IN': {0:4, 1:4, 2:4, 3:5, 4:5, 5:6, 6:6, 7:7, 8:7, 9:8, 10:8, 11:9, 12:9, 13:10, 14:10, 15:10, 16:10, 17:10, 18:10, 19:10, 20:10, 21:10, 22:10, 23:10, 24:10, 25:10, 26:10, 27:10, 28:10, 29:10, 30:10, 31:10, 32:10, 33:10, 34:10, 35:10, 36:10, 37:10, 38:10},
        'AQ': {0:1, 1:1, 2:1, 3:1, 4:1, 5:1, 6:1, 7:1, 8:1, 9:1, 10:1, 11:1, 12:1, 13:1, 14:1, 15:1, 16:1, 17:1, 18:1, 19:1, 20:1, 21:2, 22:2, 23:2, 24:2, 25:2, 26:3, 27:3, 28:3, 29:3, 30:4, 31:4, 32:4, 33:5, 34:5, 35:5, 36:6, 37:6, 38:6, 39:7, 40:7, 41:7, 42:8, 43:8, 44:8, 45:9, 46:9, 47:9, 48:9, 49:9, 50:10, 51:10, 52:10, 53:10, 54:10, 55:10, 56:10, 57:10, 58:10, 59:10, 60:10, 61:10, 62:10, 63:10, 64:10, 65:10, 66:10, 67:10, 68:10, 69:10, 70:10, 71:10, 72:10, 73:10, 74:10, 75:10, 76:10, 77:10, 78:10, 79:10, 80:10, 81:10, 82:10, 83:10, 84:10, 85:10, 86:10, 87:10, 88:10, 89:10, 90:10, 91:10, 92:10, 93:10, 94:10, 95:10}
    }
}

DECATIPO_INTERPRETATION = {
    "A": { (1, 3): "Reservado, alejado, crítico", (4, 7): "Término medio", (8, 10): "Abierto, afectuoso, reposado" },
    "B": { (1, 3): "Lento para aprender, torpe", (4, 7): "Término medio", (8, 10): "Rápido para aprender, inteligente" },
    "C": { (1, 3): "Inestable, se afecta por emociones", (4, 7): "Término medio", (8, 10): "Emocionalmente estable, maduro" },
    "E": { (1, 3): "Sumiso, dócil, complaciente", (4, 7): "Término medio", (8, 10): "Dominante, dogmático, agresivo" },
    "F": { (1, 3): "Sobrio, taciturno, serio", (4, 7): "Término medio", (8, 10): "Entusiasta, sociable, conversador" },
    "G": { (1, 3): "Informal, casual, infringe reglas", (4, 7): "Término medio", (8, 10): "Consciente, perseverante, moralista" },
    "H": { (1, 3): "Tímido, sensible a la amenaza", (4, 7): "Término medio", (8, 10): "Aventurero, socialmente atrevido" },
    "I": { (1, 3): "Realista, confía en sí mismo", (4, 7): "Término medio", (8, 10): "Sensible, dependiente, inseguro" },
    "L": { (1, 3): "Confiado, acepta condiciones", (4, 7): "Término medio", (8, 10): "Suspicaz, celoso, desconfiado" },
    "M": { (1, 3): "Práctico, convencional", (4, 7): "Término medio", (8, 10): "Imaginativo, bohemio, abstraído" },
    "N": { (1, 3): "Sencillo, natural, espontáneo", (4, 7): "Término medio", (8, 10): "Astuto, calculador, mundano" },
    "O": { (1, 3): "Sereno, confiado en sí mismo", (4, 7): "Término medio", (8, 10): "Aprensivo, inseguro, depresivo" },
    "Q1": { (1, 3): "Conservador, respeta ideas tradicionales", (4, 7): "Término medio", (8, 10): "Experimental, liberal, radical" },
    "Q2": { (1, 3): "Dependiente del grupo, seguidor", (4, 7): "Término medio", (8, 10): "Autosuficiente, prefiere decidir solo" },
    "Q3": { (1, 3): "Poco controlado, sigue sus impulsos", (4, 7): "Término medio", (8, 10): "Controlado, compulsivo" },
    "Q4": { (1, 3): "Relajado, tranquilo, no frustrado", (4, 7): "Término medio", (8, 10): "Tenso, frustrado, presionado" },
    "MI": { (1, 3): "Deseoso por dar mala autoimagen", (4, 7): "Dentro de la zona media", (8, 10): "Deseoso de causar buena impresión, buena imagen" },
    "IN": { (1, 3): "", (4, 7): "Dentro de la zona media", (8, 10): "Contesta al azar o se niega a dar información de si mismo" },
    "AQ": { (1, 3): "Tiende a rechazar la respuesta A de las preguntas", (4, 7): "Dentro de la zona media", (8, 10): "Sumiso, tímido y confiado" },
}

BIG_FIVE_WEIGHTS = {
    "Extraversión": {"+": {'A': 5, 'B': 1, 'F': 3, 'G': 1, 'H': 1, 'I': 2, 'O': 2, 'Q3': 1, 'Q4': 1}, 
                     "-": {'C': 1, 'N': 3, 'Q1': 2, 'Q2': 4}, 
                     "constante": (16, 0)},
    "Ansiedad":     {"+": {'A': 2, 'B': 2, 'E': 1, 'F': 1, 'G': 1, 'I': 1, 'L': 3, 'N': 1, 'O': 5, 'Q3': 3, 'Q4': 4},
                     "-": {'C': 3, 'H': 2, 'Q1': 3, 'Q2': 2},
                     "constante": (0, 16)},
    "Dureza":       {"+": {'F': 3, 'L': 2, 'N': 1, 'O': 1, 'Q4': 3},
                     "-": {'A': 2, 'B': 1, 'C': 1, 'E': 1, 'H': 2, 'I': 3, 'M': 3, 'Q1': 8, 'Q2': 3, 'Q3': 1},
                     "constante": (138, 0)},
    "Independencia":{"+": {'B': 1, 'C': 1, 'E': 7, 'F': 3, 'H': 2, 'L': 3, 'N': 2, 'Q1': 1, 'Q3': 1, 'Q4': 2},
                     "-": {'A': 1, 'G': 1, 'I': 2},
                     "constante": (0, 50)},
    "Auto-Control": {"+": {'A': 3, 'F': 3, 'G': 5, 'I': 1, 'O': 3, 'Q3': 7},
                     "-": {'C': 1, 'E': 1, 'H': 1, 'M': 1},
                     "constante": (0, 22)}
}

AQ_IZQ_QUESTIONS = [2, 4, 5, 6, 9, 10, 12, 13, 14, 23, 27, 28, 29, 33, 34, 35, 36, 37, 38, 39, 41, 42, 45, 46, 49, 50, 54, 57, 58, 59, 61, 62, 63, 64, 65, 66, 68, 69, 71, 76, 77, 79, 83, 85, 87, 89, 90, 91, 92, 93, 96, 97, 99]
AQ_DER_QUESTIONS = [100, 103, 105, 106, 107, 108, 110, 111, 113, 114, 116, 117, 118, 124, 125, 126, 128, 130, 132, 133, 134, 135, 137, 138, 141, 142, 145, 146, 148, 149, 150, 151, 152, 155, 156, 157, 159, 161, 165, 166, 167, 169]

# --- 6. Función de Cálculo ---
def calcular_16pf_results(respuestas_usuario_raw, sexo_paciente):
    
    # Inicializar puntajes brutos con las claves correctas
    factores_ordenados = ['A', 'B', 'C', 'E', 'F', 'G', 'H', 'I', 'L', 'M', 'N', 'O', 'Q1', 'Q2', 'Q3', 'Q4']
    puntajes_brutos = {f: 0 for f in factores_ordenados}
    puntajes_brutos['MI'] = 0
    puntajes_brutos['IN'] = 0
    puntajes_brutos['AQ'] = 0 
    
    # --- 1. CALCULAR PUNTAJES BRUTOS (EXCEPTO AQ) ---
    for i in range(1, 186):
        config = QUESTIONS_CONFIG.get(i)
        if not config: continue

        factor = config.get("factor")
        option_set_key = config.get("option_set")
        pregunta_key = f"pregunta_{i}"
        respuesta_seleccionada_texto = respuestas_usuario_raw.get(pregunta_key)

        if respuesta_seleccionada_texto and option_set_key:
            option_set = OPTION_SETS.get(option_set_key)
            if option_set:
                puntos = option_set.get(respuesta_seleccionada_texto, 0)
                
                # Sumar al factor correspondiente (excluyendo especiales por ahora)
                if factor in puntajes_brutos and factor not in ['B', 'MI', 'IN', 'AQ']:
                    puntajes_brutos[factor] += puntos
                
                # Sumar a factores especiales según las listas proporcionadas
                if i in [16, 23, 48, 58, 75, 85, 95, 101, 115, 144, 34, 153]:
                    puntajes_brutos['MI'] += puntos
                
                if i in [5,8,10,14,16,22,24,26,27,28,35,36,51,56,63,75,80,85,90,91,92,98,101,102,111,116,121,123,125,128,130,131,140,144,151,154,158,160]:
                    puntajes_brutos['IN'] += puntos
                
                if 171 <= i <= 185 and factor == 'B':
                    puntajes_brutos['B'] += puntos

    # --- 2. CALCULAR AQ (AQUIESCENCIA) ---
    # AQ Izquierda
    for i in AQ_IZQ_QUESTIONS:
        config = QUESTIONS_CONFIG.get(i)
        respuesta_texto = respuestas_usuario_raw.get(f"pregunta_{i}")
        if config and respuesta_texto:
            option_set = OPTION_SETS.get(config["option_set"])
            if option_set and option_set.get(respuesta_texto) == 1:
                 puntajes_brutos['AQ'] += 1

    # AQ Derecha
    for i in AQ_DER_QUESTIONS:
        config = QUESTIONS_CONFIG.get(i)
        respuesta_texto = respuestas_usuario_raw.get(f"pregunta_{i}")
        if config and respuesta_texto:
            option_set = OPTION_SETS.get(config["option_set"])
            if option_set and option_set.get(respuesta_texto) == 1:
                 puntajes_brutos['AQ'] += 1

    # --- 3. CALCULAR DECATIPOS ---
    sexo_key = sexo_paciente.upper() if sexo_paciente else "MASCULINO"
    if sexo_key not in ["MASCULINO", "FEMENINO"]:
        sexo_key = "MASCULINO" # Fallback por defecto

    tabla_decatipos = DECATIPO_TABLES.get(sexo_key)
    tabla_decatipos_mi_in_aq = DECATIPO_TABLES["MI_IN_AQ"]

    decatipos = {}
    for factor, puntaje in puntajes_brutos.items():
        if factor in ['MI', 'IN', 'AQ']:
            decatipos[factor] = tabla_decatipos_mi_in_aq[factor].get(puntaje, 1) # Default 1
        elif factor in tabla_decatipos:
            decatipos[factor] = tabla_decatipos[factor].get(puntaje, 1) # Default 1

    # --- 4. CALCULAR "BIG FIVE" ---
    decatipos_big_five = {}
    for big_five, weights in BIG_FIVE_WEIGHTS.items():
        suma_positiva = weights["constante"][0]
        suma_negativa = weights["constante"][1]
        
        for factor, peso in weights["+"].items():
            if factor in decatipos:
                suma_positiva += decatipos[factor] * peso
        
        for factor, peso in weights["-"].items():
            if factor in decatipos:
                suma_negativa += decatipos[factor] * peso
        
        resultado_final = (suma_positiva - suma_negativa) / 10
        decatipos_big_five[big_five] = round(resultado_final, 1)

    # --- 5. INTERPRETACIONES ---
    interpretaciones = {}
    for factor, de in decatipos.items():
        if factor in DECATIPO_INTERPRETATION:
            for (min_de, max_de), interp in DECATIPO_INTERPRETATION[factor].items():
                if min_de <= de <= max_de:
                    interpretaciones[factor] = interp
                    break
    
    # --- 6. INTERPRETACIONES BIG FIVE ---
    interpretaciones_big_five = {}
    
    # Extraversión
    ext = decatipos_big_five.get("Extraversión", 0)
    if ext <= 3.4: interpretaciones_big_five["Extraversión"] = "Introvertido y socialmente inhibido"
    elif ext >= 7.5: interpretaciones_big_five["Extraversión"] = "Extravertido y socialmente participativo"
    else: interpretaciones_big_five["Extraversión"] = "Dentro de la zona media"

    # Ansiedad
    ans = decatipos_big_five.get("Ansiedad", 0)
    if ans <= 3.4: interpretaciones_big_five["Ansiedad"] = "Imperturbable, con poca ansiedad"
    elif ans >= 7.5: interpretaciones_big_five["Ansiedad"] = "Pertubable, con mucha ansiedad"
    else: interpretaciones_big_five["Ansiedad"] = "Dentro de la zona media"

    # Dureza
    dur = decatipos_big_five.get("Dureza", 0)
    if dur <= 3.4: interpretaciones_big_five["Dureza"] = "Receptivo, de mente abierta, intuitiva"
    elif dur >= 7.5: interpretaciones_big_five["Dureza"] = "Duro, firme, flexible, frio, objetivo"
    else: interpretaciones_big_five["Dureza"] = "Dentro de la zona media"

    # Independencia
    ind = decatipos_big_five.get("Independencia", 0)
    if ind <= 3.4: interpretaciones_big_five["Independencia"] = "Acomodaticia, acepta acuerdos, cede fácil"
    elif ind >= 7.5: interpretaciones_big_five["Independencia"] = "Independiente, crítico, polemiza, analítico"
    else: interpretaciones_big_five["Independencia"] = "Dentro de la zona media"

    # Auto-Control
    aut = decatipos_big_five.get("Auto-Control", 0)
    if aut <= 3.4: interpretaciones_big_five["Auto-Control"] = "No reprimido, sigue sus impulsos"
    elif aut >= 7.5: interpretaciones_big_five["Auto-Control"] = "Autocontrolado, contiene sus impulsos"
    else: interpretaciones_big_five["Auto-Control"] = "Dentro de la zona media"

    return {
        "puntajes_brutos": puntajes_brutos,
        "decatipos": decatipos,
        "decatipos_big_five": decatipos_big_five,
        "interpretaciones": interpretaciones,
        "interpretaciones_big_five": interpretaciones_big_five
    }
# --- 7. Interfaz Gráfica ---
def crear_interfaz_16pf(supabase: Client, sexo_paciente: str):
    st.components.v1.html("<script>window.top.scrollTo(0, 0);</script>", height=0)
    st.title("Cuestionario de Personalidad 16PF")
    st.markdown("---")
    st.info(
        """
        **Instrucciones:** A continuación, encontrará una serie de preguntas. 
        Estas preguntas buscan conocer sus intereses y la forma en que usted piensa. 
        No hay respuestas "buenas" o "malas". Responda la totalidad de las preguntas con sinceridad.
        """
    )

    with st.form(key="16pf_form"):
        st.markdown("---")
        comprende = st.checkbox("Sí, comprendo las instrucciones.", key="comprende_16pf")
        st.markdown("---")

        respuestas_usuario_raw = {} 

        # Renderizar preguntas
        for i in range(1, 186):
            
            if i == 171:
                st.info("Las siguientes preguntas consisten en ejercicios de resolución de problemas. En estas solamente existe 1 respuesta correcta, elija la que crea mejor.")
            
            
            config = QUESTIONS_CONFIG.get(i)
            if not config: continue
            
            texto_pregunta = config["text"]
            option_set_key = config["option_set"]
            option_set = OPTION_SETS.get(option_set_key)
            
            if not option_set:
                 st.error(f"Set de opciones '{option_set_key}' no encontrado para pregunta {i}")
                 continue

            st.write(f"**{i}. {texto_pregunta}**")
            
            opciones_display = list(option_set.keys())
            
            selected_option_text = st.radio(
                f"Respuesta {i}",
                opciones_display,
                key=f"q_{i}",
                index=None,
                label_visibility="collapsed"
            )
            
            respuestas_usuario_raw[f"pregunta_{i}"] = selected_option_text

            if i < 185:
                st.markdown("---")

        siguiente_button = st.form_submit_button("Siguiente")

        if siguiente_button:
            if 'ficha_id' not in st.session_state:
                st.error("Error crítico: No se encontró el ID de la ficha de ingreso.")
                return

            if not comprende:
                st.warning("Debe marcar la casilla indicando que comprende las instrucciones.")
                return

            # Verificar respuestas
            preguntas_definidas = [i for i in range(1, 186) if i in QUESTIONS_CONFIG]
            errores = [f"Pregunta {i}" for i in preguntas_definidas if respuestas_usuario_raw.get(f"pregunta_{i}") is None]

            if errores:
                st.error("Por favor, responda todas las preguntas. Faltan: " + ", ".join(errores))
            else:
                with st.spinner("Calculando y guardando resultados..."):
                    
                    try:
                        resultados_finales = calcular_16pf_results(respuestas_usuario_raw, sexo_paciente)
                    except Exception as e:
                        st.error(f"Error al calcular los resultados: {e}")
                        return

                    # Convert selected text answers to numeric values before saving
                    respuestas_usuario_valores = {}
                    for i in range(1, 186):
                        key = f"pregunta_{i}"
                        texto = respuestas_usuario_raw.get(key)
                        config = QUESTIONS_CONFIG.get(i)
                        if config and texto:
                            option_set = OPTION_SETS.get(config["option_set"])
                            if option_set and texto in option_set:
                                respuestas_usuario_valores[key] = option_set[texto]

                    _16pf_data_to_save = {
                        "id": st.session_state.ficha_id,
                        "comprende": comprende,
                        **respuestas_usuario_valores, # Use numeric values here
                        "resultados": json.dumps(resultados_finales, ensure_ascii=False)
                    }

                    try:
                        response = supabase.from_('test_16pf').insert(_16pf_data_to_save).execute()
                        if response.data:
                            if 'form_data' not in st.session_state:
                                st.session_state.form_data = {}
                            st.session_state.form_data['test_16pf'] = resultados_finales
                            
                            st.session_state.current_test_index += 1
                            st.rerun()
                        else:
                            st.error(f"Error al guardar los resultados: {response.error.message if response.error else 'Error desconocido'}")
                    except Exception as e:
                        st.error(f"Ocurrió una excepción al intentar guardar los resultados: {e}")