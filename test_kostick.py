import streamlit as st
from supabase import Client
import json
from collections import Counter

# --- DATOS DEL TEST KOSTICK ---

# --- DEBES RELLENAR ESTE DICCIONARIO CON LAS 90 PREGUNTAS ---
# Formato: { numero_pregunta: {"opcion_1": {"texto": "Texto opcion 1", "factor": "G"}, 
#                             "opcion_0": {"texto": "Texto opcion 0", "factor": "L"}} }
KOSTICK_QUESTIONS = {
    1: {"opcion_1": {"texto": "Soy trabajador", "factor": "G"}, 
        "opcion_0": {"texto": "No soy de humor variable", "factor": "Z"}},
    2: {"opcion_1": {"texto": "Me gusta seguir con lo que he empezado hasta terminarlo.", "factor": "N"},
        "opcion_0": {"texto": "Me gusta hacer el trabajo mejor que los demás.", "factor": "A"}},
    3: {"opcion_1": {"texto": "Me gusta hacer las cosas lo mejor posible.", "factor": "A"}, 
        "opcion_0": {"texto": "Me gusta enseñar a la gente cómo hacer las cosas.", "factor": "P"}},
    4: {"opcion_1": {"texto": "Me gusta hacer las cosas graciosas.", "factor": "X"}, 
        "opcion_0": {"texto": "Me gusta decir a la gente lo que tiene que hacer.", "factor": "P"}},
    5: {"opcion_1": {"texto": "Me gusta ser tomado en cuenta por los grupos.", "factor": "X"},
        "opcion_0": {"texto": "Me gusta unirme a grupos.", "factor": "B"}},
    6: {"opcion_1": {"texto": "Me gusta hacer un amigo íntimo.", "factor": "O"},
        "opcion_0": {"texto": "Me gusta hacer amistad con el grupo.", "factor": "B"}},
    7: {"opcion_1": {"texto": "Soy rápido en cambiar cuando lo creo necesario.", "factor": "E"},
        "opcion_0": {"texto": "Intento hacer amigos íntimos.", "factor": "O"}},
    8: {"opcion_1": {"texto": "Me gusta hacer cosas nuevas o diferentes.", "factor": "E"},
        "opcion_0": {"texto": "Me gusta “devolverla” cuando alguien me ofende.", "factor": "K"}},
    9: {"opcion_1": {"texto": "Quiero que mi Jefe me estime.", "factor": "F"},
        "opcion_0": {"texto": "Me gusta decir a la gente cuándo están equivocados.", "factor": "K"}},
    10: {"opcion_1": {"texto": "Me gusta seguir las instrucciones que me dan.", "factor": "W"},
         "opcion_0": {"texto": "Me gusta agradar a mis superiores.", "factor": "F"}},
    
    11: {"opcion_1": {"texto": "Me esfuerzo mucho.", "factor": "G"},
         "opcion_0": {"texto": "Soy ordenado. Pongo todo en su sitio.", "factor": "C"}},
    12: {"opcion_1": {"texto": "No me altero fácilmente.", "factor": "Z"},
         "opcion_0": {"texto": "Consigo con la gente haga lo que yo quiero.", "factor": "L"}},
    13: {"opcion_1": {"texto": "Siempre continúo un trabajo hasta que está hecho.", "factor": "N"},
         "opcion_0": {"texto": "Me gusta decir al grupo lo que tiene que hacer.", "factor": "P"}},
    14: {"opcion_1": {"texto": "Yo quiero tener mucho éxito.", "factor": "A"},
         "opcion_0": {"texto": "Me gusta ser animado e interesante.", "factor": "X"}},
    15: {"opcion_1": {"texto": "Me gusta ayudar a las personas a tomar decisiones.", "factor": "P"},
         "opcion_0": {"texto": "Me gusta “encajar” con grupos.", "factor": "B"}},
    16: {"opcion_1": {"texto": "Me preocupa cuando alguien no me estima.", "factor": "O"},
         "opcion_0": {"texto": "Me gusta que la gente note mi presencia.", "factor": "X"}},
    17: {"opcion_1": {"texto": "Prefiero trabajar con otras personas que solo.", "factor": "B"},
         "opcion_0": {"texto": "Me gusta probar cosas nuevas.", "factor": "E"}},
    18: {"opcion_1": {"texto": "Me molesta cuando no le gusto a alguien.", "factor": "O"},
         "opcion_0": {"texto": "Algunas veces culpo a otros cuando las cosas salen mal.", "factor": "K"}},
    19: {"opcion_1": {"texto": "Me gusta intentar trabajos nuevos y diferentes.", "factor": "E"},
         "opcion_0": {"texto": "Me gusta complacer a mis superiores.", "factor": "F"}},
    20: {"opcion_1": {"texto": "Me gusta tener instrucciones detallas para hacer un trabajo.", "factor": "W"},
         "opcion_0": {"texto": "Me gusta decírselo a la gente cuando me enfada.", "factor": "K"}},

    21: {"opcion_1": {"texto": "Siempre me esfuerzo mucho.", "factor": "G"},
         "opcion_0": {"texto": "Me gusta ir paso a paso con gran cuidado.", "factor": "D"}},
    22: {"opcion_1": {"texto": "Organizo bien el trabajo de un puesto.", "factor": "C"},
         "opcion_0": {"texto": "Soy un buen “dirigente”.", "factor": "L"}},
    23: {"opcion_1": {"texto": "Soy lento tomando decisiones.", "factor": "Z"},
         "opcion_0": {"texto": "Me enfado con facilidad.", "factor": "I"}},
    24: {"opcion_1": {"texto": "Me gusta trabajar en varias actividades al mismo tiempo.", "factor": "X"},
         "opcion_0": {"texto": "Cuando estoy en grupo me gusta estar callado.", "factor": "N"}},
    25: {"opcion_1": {"texto": "Me encanta que me inviten.", "factor": "B"},
         "opcion_0": {"texto": "Me gusta hacer las cosas mejor que los demás.", "factor": "A"}},
    26: {"opcion_1": {"texto": "Me gusta aconsejar a los demás.", "factor": "P"},
         "opcion_0": {"texto": "Me gusta hacer amigos íntimos.", "factor": "O"}},
    27: {"opcion_1": {"texto": "Me gusta hacer cosas nuevas y diferentes.", "factor": "E"},
         "opcion_0": {"texto": "Me gusta hablar de mis éxitos.", "factor": "X"}},
    28: {"opcion_1": {"texto": "Cuando tengo razón me gusta luchar por ella.", "factor": "K"},
         "opcion_0": {"texto": "Me gusta pertenecer a un grupo.", "factor": "B"}},
    29: {"opcion_1": {"texto": "Evito ser diferente.", "factor": "F"},
         "opcion_0": {"texto": "Intento acercarme mucho a la gente.", "factor": "O"}},
    30: {"opcion_1": {"texto": "Me gusta que me digan exactamente cómo hacer las cosas.", "factor": "W"},
         "opcion_0": {"texto": "Me aburro fácilmente.", "factor": "E"}},

    31: {"opcion_1": {"texto": "Pienso y planeo mucho.", "factor": "R"},
         "opcion_0": {"texto": "Trabajo mucho.", "factor": "G"}},
    32: {"opcion_1": {"texto": "Los pequeños detalles me interesan.", "factor": "D"},
         "opcion_0": {"texto": "Me gusta dirigir el grupo.", "factor": "L"}},
    33: {"opcion_1": {"texto": "Tengo mis cosas cuidadas y ordenadas.", "factor": "C"},
         "opcion_0": {"texto": "Tomo decisiones fácil y rápidamente.", "factor": "I"}},
    34: {"opcion_1": {"texto": "Yo no me pongo enfadado ni triste a menudo.", "factor": "Z"},
         "opcion_0": {"texto": "Hago las cosas de prisa.", "factor": "T"}},
    35: {"opcion_1": {"texto": "Quiero ser parte del grupo.", "factor": "B"},
         "opcion_0": {"texto": "Quiero hacer un solo trabajo a un tiempo.", "factor": "N"}},
    36: {"opcion_1": {"texto": "Intento hacer amigos íntimos.", "factor": "O"},
         "opcion_0": {"texto": "Intento mucho ser el mejor.", "factor": "A"}},
    37: {"opcion_1": {"texto": "Me gusta ser responsable por otros.", "factor": "P"},
         "opcion_0": {"texto": "Me gustan los nuevos estilos en trajes y coches.", "factor": "E"}},
    38: {"opcion_1": {"texto": "Me gusta llamar la atención.", "factor": "X"},
         "opcion_0": {"texto": "Disfruto discutiendo.", "factor": "K"}},
    39: {"opcion_1": {"texto": "Me gusta agradar a mis superiores.", "factor": "F"},
         "opcion_0": {"texto": "Estoy interesado en ser parte del grupo.", "factor": "B"}},
    40: {"opcion_1": {"texto": "Me gusta regir las reglas con cuidado.", "factor": "W"},
         "opcion_0": {"texto": "Me gusta que la gente me conozca muy bien.", "factor": "O"}},

    41: {"opcion_1": {"texto": "Me esfuerzo mucho.", "factor": "G"},
         "opcion_0": {"texto": "Soy muy amigable.", "factor": "S"}},
    42: {"opcion_1": {"texto": "La gente piensa que soy un buen “dirigente”.", "factor": "L"},
         "opcion_0": {"texto": "Pienso con cuidado y largamente.", "factor": "R"}},
    43: {"opcion_1": {"texto": "La gente piensa que soy un buen “dirigente”.", "factor": "I"},
         "opcion_0": {"texto": "Pienso con cuidado y largamente.", "factor": "D"}},
    44: {"opcion_1": {"texto": "A menudo me arriesgo.", "factor": "T"},
         "opcion_0": {"texto": "Me gusta protestar por pequeñas cosas.", "factor": "C"}},
    45: {"opcion_1": {"texto": "Soy muy agradable.", "factor": "Z"},
         "opcion_0": {"texto": "Me gusta jugar y hacer deportes.", "factor": "V"}},
    46: {"opcion_1": {"texto": "Siempre trato de terminar lo que he empezado.", "factor": "N"},
         "opcion_0": {"texto": "Me gusta que la gente esté unida y sea amistosa.", "factor": "O"}},
    47: {"opcion_1": {"texto": "Me gusta hacer bien un trabajo difícil.", "factor": "A"},
         "opcion_0": {"texto": "Me gusta experimentar y probar nuevas cosas.", "factor": "E"}},
    48: {"opcion_1": {"texto": "Me gusta que me traten justamente.", "factor": "K"},
         "opcion_0": {"texto": "Me gusta decir a los demás cómo hacer las cosas.", "factor": "P"}},
    49: {"opcion_1": {"texto": "Me gusta hacer aquello que esperan de mí.", "factor": "F"},
         "opcion_0": {"texto": "Me gusta llamar la atención.", "factor": "X"}},
    50: {"opcion_1": {"texto": "Me gusta tener instrucciones precisas para hacer un trabajo.", "factor": "W"},
         "opcion_0": {"texto": "Me gusta estar con la gente.", "factor": "B"}},
    51: {"opcion_1": {"texto": "Siempre trato de hacer mi trabajo perfecto.", "factor": "G"},
         "opcion_0": {"texto": "Me dicen que soy prácticamente incansable.", "factor": "V"}},
    52: {"opcion_1": {"texto": "Hago amigos fácilmente.", "factor": "S"},
         "opcion_0": {"texto": "Soy el tipo “dirigente”.", "factor": "L"}},
    53: {"opcion_1": {"texto": "Asumo riesgos.", "factor": "I"},
         "opcion_0": {"texto": "Pienso mucho.", "factor": "R"}},
    54: {"opcion_1": {"texto": "Disfruto trabajando en detalles.", "factor": "D"},
         "opcion_0": {"texto": "Trabajo a un paso rápido y constante.", "factor": "T"}},
    55: {"opcion_1": {"texto": "Tengo mis cosas cuidadas y ordenadas.", "factor": "C"},
         "opcion_0": {"texto": "Tengo mucha energía para juegos y deportes.", "factor": "V"}},
    56: {"opcion_1": {"texto": "Me llevo bien con todo el mundo.", "factor": "S"},
         "opcion_0": {"texto": "Soy de temperamento estable.", "factor": "Z"}},
    57: {"opcion_1": {"texto": "Siempre quiero terminar el trabajo que he empezado.", "factor": "N"},
         "opcion_0": {"texto": "Quiero conocer nueva gente y hacer cosas nuevas.", "factor": "E"}},
    58: {"opcion_1": {"texto": "Normalmente me gusta trabajar mucho.", "factor": "A"},
         "opcion_0": {"texto": "Normalmente lucho por lo que yo creo.", "factor": "K"}},
    59: {"opcion_1": {"texto": "Me gustan las sugerencias de las personas que admiro.", "factor": "F"},
         "opcion_0": {"texto": "Me gusta estar encargado de otras personas.", "factor": "P"}},
    60: {"opcion_1": {"texto": "Me dejo influenciar mucho por la gente.", "factor": "W"},
         "opcion_0": {"texto": "Me gusta ser el centro de atención.", "factor": "X"}},

    61: {"opcion_1": {"texto": "Normalmente trabajo mucho.", "factor": "G"},
         "opcion_0": {"texto": "Normalmente trabajo de prisa.", "factor": "T"}},
    62: {"opcion_1": {"texto": "Cuando hablo el grupo escucha.", "factor": "L"},
         "opcion_0": {"texto": "Soy hábil con herramientas.", "factor": "V"}},
    63: {"opcion_1": {"texto": "Soy lento en hacer amigos.", "factor": "I"},
         "opcion_0": {"texto": "Soy lento en decidirme.", "factor": "S"}},
    64: {"opcion_1": {"texto": "Normalmente como de prisa.", "factor": "T"},
         "opcion_0": {"texto": "Disfruto leyendo.", "factor": "R"}},
    65: {"opcion_1": {"texto": "Me gusta el trabajo que tenga que hacerse con cuidado.", "factor": "D"},
         "opcion_0": {"texto": "Me gusta el trabajo en donde puedo moverme.", "factor": "V"}},
    66: {"opcion_1": {"texto": "Encuentro lo que he guardado.", "factor": "C"},
         "opcion_0": {"texto": "Hago el mayor número posible de amigos.", "factor": "S"}},
    67: {"opcion_1": {"texto": "Planeo a largo plazo.", "factor": "R"},
         "opcion_0": {"texto": "Siempre soy agradable.", "factor": "Z"}},
    68: {"opcion_1": {"texto": "Tengo orgullo de mi buen nombre.", "factor": "K"},
         "opcion_0": {"texto": "Insisto en un problema hasta que está resuelto.", "factor": "N"}},
    69: {"opcion_1": {"texto": "Quiero tener éxito.", "factor": "A"},
         "opcion_0": {"texto": "Me gusta agradar a la gente que admiro.", "factor": "F"}},
    70: {"opcion_1": {"texto": "Me gusta que otros tomen decisiones para el grupo.", "factor": "W"},
         "opcion_0": {"texto": "A mi me gusta tomar decisiones para el grupo.", "factor": "P"}},
    71: {"opcion_1": {"texto": "Siempre me esfuerzo mucho.", "factor": "G"},
         "opcion_0": {"texto": "Tomo decisiones fácil y rápidamente.", "factor": "I"}},
    72: {"opcion_1": {"texto": "Normalmente tengo prisa.", "factor": "T"},
         "opcion_0": {"texto": "El grupo hace normally lo que yo quiero.", "factor": "L"}}, # Corregido "normally"
    73: {"opcion_1": {"texto": "A menudo me siento cansado.", "factor": "I"},
         "opcion_0": {"texto": "Soy lento tomando decisiones.", "factor": "V"}},
    74: {"opcion_1": {"texto": "Trabajo de prisa.", "factor": "T"},
         "opcion_0": {"texto": "Hago amigos en seguida.", "factor": "S"}},
    75: {"opcion_1": {"texto": "Normalmente tengo energía.", "factor": "V"},
         "opcion_0": {"texto": "Dedico mucho tiempo a pensar.", "factor": "R"}},
    76: {"opcion_1": {"texto": "Me gusta el trabajo que requiere precisión.", "factor": "D"},
         "opcion_0": {"texto": "Soy muy cordial con la gente.", "factor": "S"}},
    77: {"opcion_1": {"texto": "Guardo todas las cosas en su sitio.", "factor": "C"},
         "opcion_0": {"texto": "Pienso y planeo mucho.", "factor": "R"}},
    78: {"opcion_1": {"texto": "Tardo en enfadarme.", "factor": "Z"},
         "opcion_0": {"texto": "Me gusta el trabajo que requiere detalles.", "factor": "D"}},
    79: {"opcion_1": {"texto": "Siempre termino el trabajo que he empezado.", "factor": "N"},
         "opcion_0": {"texto": "Me gusta seguir a la gente que admiro.", "factor": "F"}},
    80: {"opcion_1": {"texto": "Me gustan las instrucciones claras.", "factor": "W"},
         "opcion_0": {"texto": "Me gusta trabajar mucho.", "factor": "A"}},

    # --- Preguntas 81-90 añadidas ---
    81: {"opcion_1": {"texto": "Persigo aquello que deseo.", "factor": "G"},
         "opcion_0": {"texto": "Soy un buen “dirigente”", "factor": "L"}},
    82: {"opcion_1": {"texto": "Soy desenfadado.", "factor": "I"},
         "opcion_0": {"texto": "Hago que los demás trabajen mucho.", "factor": "L"}},
    83: {"opcion_1": {"texto": "Hablo de prisa.", "factor": "T"},
         "opcion_0": {"texto": "Tomo decisiones rápidas.", "factor": "I"}},
    84: {"opcion_1": {"texto": "Hago ejercicios con regularidad.", "factor": "V"},
         "opcion_0": {"texto": "Normalmente trabajo de prisa.", "factor": "T"}},
    85: {"opcion_1": {"texto": "Me canso en seguida.", "factor": "S"},
         "opcion_0": {"texto": "No me gusta conocer gente.", "factor": "V"}},
    86: {"opcion_1": {"texto": "Hago muchísimos amigos.", "factor": "S"},
         "opcion_0": {"texto": "Dedico mucho tiempo a pensar.", "factor": "R"}},
    87: {"opcion_1": {"texto": "Me gusta trabajar con detalles.", "factor": "D"},
         "opcion_0": {"texto": "Me gusta pensar sobre teoría.", "factor": "R"}},
    88: {"opcion_1": {"texto": "Me gusta organizar mi trabajo.", "factor": "C"},
         "opcion_0": {"texto": "Me gusta trabajar con detalles.", "factor": "D"}},
    89: {"opcion_1": {"texto": "Siempre soy agradable.", "factor": "Z"},
         "opcion_0": {"texto": "Pongo las cosas en su sitio.", "factor": "C"}},
    90: {"opcion_1": {"texto": "Tengo que terminar lo que he empezado.", "factor": "N"}, 
         "opcion_0": {"texto": "Me gusta que me digan qué he de hacer.", "factor": "W"}} 
}

# --- DEBES RELLENAR ESTE DICCIONARIO CON LAS INTERPRETACIONES ---
# Formato: { "Factor": { puntaje: {"descripcion": "...", "observacion": "..."} } }
KOSTICK_SCORING = {
    "G": {
        0: {"descripcion": "DESEMPEÑO DEL TRABAJO ARDUO Y CONCENTRADO ( RESPONSABILIDAD ).", "observacion": "1.- NO LE AGRADAN TRABAJOS QUE EXIJAN ESFUERZO, PUEDE DEJAR PARA EL DÍA SIGUIENTE LO QUE PODÍA HACER HOY."},
        1: {"descripcion": "DESEMPEÑO DEL TRABAJO ARDUO Y CONCENTRADO ( RESPONSABILIDAD ).", "observacion": "1.- NO LE AGRADAN TRABAJOS QUE EXIJAN ESFUERZO, PUEDE DEJAR PARA EL DÍA SIGUIENTE LO QUE PODÍA HACER HOY."},
        2: {"descripcion": "DESEMPEÑO DEL TRABAJO ARDUO Y CONCENTRADO ( RESPONSABILIDAD ).", "observacion": "2.- DEDICA POCO ESFUERZO A LA REALIZACIÓN DE SUS TRABAJOS."},
        3: {"descripcion": "DESEMPEÑO DEL TRABAJO ARDUO Y CONCENTRADO ( RESPONSABILIDAD ).", "observacion": "3.- LE AGRADA REALIZAR TRABAJOS QUE NO EXIJAN ESFUERZO PARA SER REALIZADOS."},
        4: {"descripcion": "DESEMPEÑO DEL TRABAJO ARDUO Y CONCENTRADO ( RESPONSABILIDAD ).", "observacion": "5/4.- IDENTIFICACIÓN REGULAR CON TRABAJOS DIFÍCILES."},
        5: {"descripcion": "DESEMPEÑO DEL TRABAJO ARDUO Y CONCENTRADO ( RESPONSABILIDAD ).", "observacion": "5/4.- IDENTIFICACIÓN REGULAR CON TRABAJOS DIFÍCILES."},
        6: {"descripcion": "DESEMPEÑO DEL TRABAJO ARDUO Y CONCENTRADO ( RESPONSABILIDAD ).", "observacion": "6.- IDENTIFICACIÓN SOBRE REGULAR CON TRABAJOS DIFÍCILES."},
        7: {"descripcion": "DESEMPEÑO DEL TRABAJO ARDUO Y CONCENTRADO ( RESPONSABILIDAD ).", "observacion": "7.- PREFIERE TRABAJOS QUE EXIJAN ESFUERZO PARA SER REALIZADO."},
        8: {"descripcion": "DESEMPEÑO DEL TRABAJO ARDUO Y CONCENTRADO ( RESPONSABILIDAD ).", "observacion": "8.- ES BASTANTE DEDICADO AL TRABAJO QUE EXIGE ESFUERZO PARA SER REALIZADO."},
        9: {"descripcion": "DESEMPEÑO DEL TRABAJO ARDUO Y CONCENTRADO ( RESPONSABILIDAD ).", "observacion": "9.- ES EXTREMADAMENTE DEDICADO A TRABAJOS QUE EXIGEN ESFUERZOS PARA SER REALIZADOS."}
    },
    "L": {
        0: {"descripcion": "PAPEL DE LIDERAZGO.", "observacion": "1.- NO ACEPTA EL PAPEL DE LÍDER, PREFIERE SER LIDERADO A LIDERAR, EN POSICIÓN DE JEFATURA, TIENE A EVITAR EL LIDERAZGO."},
        1: {"descripcion": "PAPEL DE LIDERAZGO.", "observacion": "1.- NO ACEPTA EL PAPEL DE LÍDER, PREFIERE SER LIDERADO A LIDERAR, EN POSICIÓN DE JEFATURA, TIENE A EVITAR EL LIDERAZGO."},
        2: {"descripcion": "PAPEL DE LIDERAZGO.", "observacion": "2.- TIENE PROBLEMAS CON LIDERAZGO. PREFIERE SER ORIENTADO POR LOS OTROS . NO OBTIENE SUFICIENTE RECOMPENSA INTERIOR EN EL PAPEL DE LIDERAZGO."},
        3: {"descripcion": "PAPEL DE LIDERAZGO.", "observacion": "3.- NO OBTIENE SUFICIENTE RECOMPENSA INTERIOR COMO LÍDER, TIENDE A TRANSFERIR LOS PROBLEMAS DE LIDERAZGO."},
        4: {"descripcion": "PAPEL DE LIDERAZGO.", "observacion": "4.- GRADO MEDIO DE CONFIANZA EN SÍ MISMO COMO LÍDER, PUDIENDO IGUALMENTE EJERCER EL LIDERAZGO Y SER LIDERADO."},
        5: {"descripcion": "PAPEL DE LIDERAZGO.", "observacion": "5.- CONFÍA EN SÍ MISMO COMO LÍDER, TIENDE A EJERCER EL LIDERAZGO."},
        6: {"descripcion": "PAPEL DE LIDERAZGO.", "observacion": "6.- LE AGRADA LIDERAR ES UNA PERSONA QUE ASUME EL LIDERAZGO DEL GRUPO."},
        7: {"descripcion": "PAPEL DE LIDERAZGO.", "observacion": "7.- TIENE CONFIANZA EN SÍ COMO LÍDER; LE AGRADA TOMAR EL LIDERAZGO DEL GRUPO."},
        8: {"descripcion": "PAPEL DE LIDERAZGO.", "observacion": "8.- MUY CONFIADO COMO LÍDER; ES CONSIDERADO COMO UN LÍDER EN EL GRUPO."},
        9: {"descripcion": "PAPEL DE LIDERAZGO.", "observacion": "9.- ES IMPULSADO POR UN FUERTE DESEO DE LIDERAZGO. ES AUTO-CONFIANTE A PUNTO DE TOMAR FRECUENTEMENTE EL LIDERAZGO."}
    },
    "I": {
        0: {"descripcion": "FACILIDAD EN LA TOMA DE DECISIONES.", "observacion": "1.- SIENTE DIFICULTAD PARA DECIDIRSE, EL PROCESO DE DECISIÓN LE CREA ANGUSTIA Y MALESTAR; NO LE AGRADA TOMAR DECISIONES."},
        1: {"descripcion": "FACILIDAD EN LA TOMA DE DECISIONES.", "observacion": "1.- SIENTE DIFICULTAD PARA DECIDIRSE, EL PROCESO DE DECISIÓN LE CREA ANGUSTIA Y MALESTAR; NO LE AGRADA TOMAR DECISIONES."},
        2: {"descripcion": "FACILIDAD EN LA TOMA DE DECISIONES.", "observacion": "2.- ES LENTO EN LA TOMA DE DECISIONES. SE PREOCUPA MUCHO POR LA CALIDAD DE LA DECISIÓN ( TIENDE A DEJAR DE TOMAR DECISIONES )."},
        3: {"descripcion": "FACILIDAD EN LA TOMA DE DECISIONES.", "observacion": "3.- PIENSA PARA DECIDIRSE; TIENDE A SER REFLEXIVO, ES LENTO EN EL PROCESO DE TOMA DE DECISIONES."},
        4: {"descripcion": "FACILIDAD EN LA TOMA DE DECISIONES.", "observacion": "4.- GRADO REGULAR DE CAPACIDAD PARA DECIDIRSE."},
        5: {"descripcion": "FACILIDAD EN LA TOMA DE DECISIONES.", "observacion": "5.- BUENA CAPACIDAD PARA DECIDIRSE; TRATA DE IMPRIMIR EN SUS DECISIONES EL MISMO GRADO DE CALIDAD Y RAPIDEZ."},
        6: {"descripcion": "FACILIDAD EN LA TOMA DE DECISIONES.", "observacion": "6.- TOMA DECISIONES CON FACILIDAD SIN, ENTRETANTO, APRESURARSE EN DEJAR DE MEDIR LAS CONSECUENCIAS DE SUS DECISIONES."},
        7: {"descripcion": "FACILIDAD EN LA TOMA DE DECISIONES.", "observacion": "7.- RÁPIDO PARA DECIDIRSE; SE PREOCUPA POCO DE LAS CONSECUENCIAS DE SUS DECISIONES, DANDO MÁS ÉNFASIS A LA VELOCIDAD EN LA TOMA DE LAS MISMAS."},
        8: {"descripcion": "FACILIDAD EN LA TOMA DE DECISIONES.", "observacion": "8.- IMPULSIVO, DA MÁS ÉNFASIS A LA VELOCIDAD QUE A LA SEGURIDAD DE LA DECISIONES. PUEDE TOMAR DECISIONES APRESURADAS."},
        9: {"descripcion": "FACILIDAD EN LA TOMA DE DECISIONES.", "observacion": "9.- EXTREMADAMENTE RÁPIDO PARA DECIDIRSE; CORRE EL RIESGO DE TOMAR DECISIONES NO PENSADAS."}
    },
    "T": {
        0: {"descripcion": "TIPO ACTIVO-INQUIETO Y AGIL ( STRESS )", "observacion": "1.- NO LE AGRADA TRABAJAR CON PRESIÓN DE PLAZOS, TIENDE A NO DAR IMPORTANCIA AL TIEMPO ESTABLECIDO."},
        1: {"descripcion": "TIPO ACTIVO-INQUIETO Y AGIL ( STRESS )", "observacion": "1.- NO LE AGRADA TRABAJAR CON PRESIÓN DE PLAZOS, TIENDE A NO DAR IMPORTANCIA AL TIEMPO ESTABLECIDO."},
        2: {"descripcion": "TIPO ACTIVO-INQUIETO Y AGIL ( STRESS )", "observacion": "2.- TRABAJA CALMADAMENTE, POCO PREOCUPADO EN CUANTO A LÍMITES DE TIEMPO, TIENE DIFICULTAD EN MANEJAR PLAZOS PRE - ESTABLECIDOS"},
        3: {"descripcion": "TIPO ACTIVO-INQUIETO Y AGIL ( STRESS )", "observacion": "3.- SE PREOCUPA EVENTUALMENTE POR LOS LÍMITES DE TIEMPO, PREFIRIENDO NO TRABAJAR EN BASE A PRESIÓN DE PLAZOS."},
        4: {"descripcion": "TIPO ACTIVO-INQUIETO Y AGIL ( STRESS )", "observacion": "4.- ES RESPONSABLE EN CUANTO A LÍMITES DE TIEMPO. TIENDE A EJECUTAR SUS DEBERES DENTRO DE LOS PLAZOS DETERMINADOS."},
        5: {"descripcion": "TIPO ACTIVO-INQUIETO Y AGIL ( STRESS )", "observacion": "5.- SE PREOCUPA POR LO LÍMITES DE TIEMPO. TRABAJA DENTRO DE LOS LÍMITES DE TIEMPO ESTABLECIDOS."},
        6: {"descripcion": "TIPO ACTIVO-INQUIETO Y AGIL ( STRESS )", "observacion": "6.- RESPONSABILIDAD SOBRE REGULAR EN CUANTO A LÍMITES DE TIEMPO."},
        7: {"descripcion": "TIPO ACTIVO-INQUIETO Y AGIL ( STRESS )", "observacion": "7.- ES UNA PERSONA INQUIETA Y MUY PREOCUPADA CON PLAZOS, TIENE MUCHA NECESIDAD DE REALIZAR SUS TRABAJOS DENTRO DE LOS LÍMITES DE TIEMPO."},
        8: {"descripcion": "TIPO ACTIVO-INQUIETO Y AGIL ( STRESS )", "observacion": "8.- POSEE MUCHA TENSIÓN INTERNA. FUERTEMENTE PREOCUPADO CON LOS LÍMITES DE TIEMPO."},
        9: {"descripcion": "TIPO ACTIVO-INQUIETO Y AGIL ( STRESS )", "observacion": "9.- PERSONA QUE ESTA PERMANENTEMENTE TENSA Y FUERTEMENTE IMPULSADA A TRABAJAR DENTRO DE LOS LÍMITES DE TIEMPO."}
    },
    "V": {
        0: {"descripcion": "TIPO CON VIGOR FISICO.", "observacion": "1.- NO LE AGRADAN TRABAJOS QUE EXIJAN MOVIMIENTO; NECESITA ACTIVIDADES QUE PUEDEN SER REALIZADAS SENTADAS."},
        1: {"descripcion": "TIPO CON VIGOR FISICO.", "observacion": "1.- NO LE AGRADAN TRABAJOS QUE EXIJAN MOVIMIENTO; NECESITA ACTIVIDADES QUE PUEDEN SER REALIZADAS SENTADAS."},
        2: {"descripcion": "TIPO CON VIGOR FISICO.", "observacion": "2.- PREFIERE TRABAJOS QUE PUEDEN SER REALIZADOS SENTADO."},
        3: {"descripcion": "TIPO CON VIGOR FISICO.", "observacion": "3.- POCO INTERÉS EN ACTIVIDADES QUE EXIJAN MOVIMIENTO. PREFIERE TRABAJAR SENTADO."},
        4: {"descripcion": "TIPO CON VIGOR FISICO.", "observacion": "5/4.- GRADO REGULAR DE VIGOR FÍSICO. TIENDE A PREFERIR FUNCIONES QUE EXIJAN MOVIMIENTO LIMITADO."},
        5: {"descripcion": "TIPO CON VIGOR FISICO.", "observacion": "5/4.- GRADO REGULAR DE VIGOR FÍSICO. TIENDE A PREFERIR FUNCIONES QUE EXIJAN MOVIMIENTO LIMITADO."},
        6: {"descripcion": "TIPO CON VIGOR FISICO.", "observacion": "6.- LE AGRADA ESTAR EN MOVIMIENTO."},
        7: {"descripcion": "TIPO CON VIGOR FISICO.", "observacion": "7.- NECESITA ESTAR EN CONSTANTE MOVIMIENTO."},
        8: {"descripcion": "TIPO CON VIGOR FISICO.", "observacion": "8.- ES MUY DINÁMICO, TIENE DIFICULTAD EN REALIZAR ACTIVIDADES QUE LO OBLIGUEN A ESTAR PARADO EN UN AMBIENTE."},
        9: {"descripcion": "TIPO CON VIGOR FISICO.", "observacion": "9.- ES EXTREMADAMENTE INQUIETO, NECESITA REALIZAR ACTIVIDADES QUE EXIJAN BASTANTE MOVIMIENTO."}
    },
    "S": {
        0: {"descripcion": "DISPOSICION SOCIAL", "observacion": "1.- PERSONA INTROVERTIDA, SIN PREOCUPACIÓN POR LA COMUNICACIÓN SOCIAL. SOCIALMENTE SIN CONDICIÓN."},
        1: {"descripcion": "DISPOSICION SOCIAL", "observacion": "1.- PERSONA INTROVERTIDA, SIN PREOCUPACIÓN POR LA COMUNICACIÓN SOCIAL. SOCIALMENTE SIN CONDICIÓN."},
        2: {"descripcion": "DISPOSICION SOCIAL", "observacion": "2.- ES UNA PERSONA RESERVADA EN SU RELACIONAMIENTO SOCIAL."},
        3: {"descripcion": "DISPOSICION SOCIAL", "observacion": "3.- POSEE CIERTA RESERVA EN LA COMUNICACIÓN SOCIAL."},
        4: {"descripcion": "DISPOSICION SOCIAL", "observacion": "4.- PREOCUPACIÓN REGULAR (50%) CON LA COMUNICACIÓN SOCIAL."},
        5: {"descripcion": "DISPOSICION SOCIAL", "observacion": "5.- BUENA CAPACIDAD DE ESCUCHAR Y COMUNICARSE SOCIALMENTE."},
        6: {"descripcion": "DISPOSICION SOCIAL", "observacion": "6.- POSEE BUEN RELACIONAMIENTO SOCIAL."},
        7: {"descripcion": "DISPOSICION SOCIAL", "observacion": "7.- BUENA DISPOSICIÓN SOCIAL. PERSONA MUY RECEPTIVA."},
        8: {"descripcion": "DISPOSICION SOCIAL", "observacion": "8.- PERSONA EXTROVERTIDA, CON ÓPTIMA CAPACIDAD DE COMUNICACIÓN."},
        9: {"descripcion": "DISPOSICION SOCIAL", "observacion": "9.- PERSONA MUY PARTICIPATIVA Y RECEPTIVA A LA COMUNICACIÓN."}
    },
    "R": {
        0: {"descripcion": "TIPO TEORICO ( PRACTICA )", "observacion": "0.- NINGUNA PREOCUPACIÓN EN PLANIFICACIÓN."},
        1: {"descripcion": "TIPO TEORICO ( PRACTICA )", "observacion": "1.- EJECUTA LOS TRABAJOS SIN PLANIFICAR."},
        2: {"descripcion": "TIPO TEORICO ( PRACTICA )", "observacion": "2.- TIENE DIFICULTADES EN PLANIFICAR SUS TRABAJOS, PREFIRIENDO EJECUTAR A PLANIFICAR."},
        3: {"descripcion": "TIPO TEORICO ( PRACTICA )", "observacion": "3.- PREFIERE EJECUTAR A PLANIFICAR."},
        4: {"descripcion": "TIPO TEORICO ( PRACTICA )", "observacion": "5/4.- PREFIERE PLANIFICAR Y FORMULAR ESTRATEGIAS 40 A 50% DEL TIEMPO."},
        5: {"descripcion": "TIPO TEORICO ( PRACTICA )", "observacion": "5/4.- PREFIERE PLANIFICAR Y FORMULAR ESTRATEGIAS 40 A 50% DEL TIEMPO."},
        6: {"descripcion": "TIPO TEORICO ( PRACTICA )", "observacion": "7/6.- PREFIERE PLANIFICAR Y FORMULAR ESTRATEGIAS 70% DEL TIEMPO."},
        7: {"descripcion": "TIPO TEORICO ( PRACTICA )", "observacion": "7/6.- PREFIERE PLANIFICAR Y FORMULAR ESTRATEGIAS 70% DEL TIEMPO."},
        8: {"descripcion": "TIPO TEORICO ( PRACTICA )", "observacion": "8.- GASTA LA MAYOR PARTE DEL TIEMPO, 80 A 90%, PLANIFICANDO Y FORMULANDO ESTRATEGIAS."},
        9: {"descripcion": "TIPO TEORICO ( PRACTICA )", "observacion": "9.- GASTA LA TOTALIDAD DE SU TIEMPO PLANIFICANDO, TIENE DIFICULTADES EN EJECUTAR TAREAS."}
    },
    "D": {
        0: {"descripcion": "INTERESADO EN TRABAJAR CON DETALLES", "observacion": "1.- NO VALORIZA DETALLES, CORRE SERIE RIESGO DE NO PRESTAR ATENCIÓN A DETALLES IMPORTANTES PARA LA CORRECCIÓN DE LOS TRABAJOS."},
        1: {"descripcion": "INTERESADO EN TRABAJAR CON DETALLES", "observacion": "1.- NO VALORIZA DETALLES, CORRE SERIE RIESGO DE NO PRESTAR ATENCIÓN A DETALLES IMPORTANTES PARA LA CORRECCIÓN DE LOS TRABAJOS."},
        2: {"descripcion": "INTERESADO EN TRABAJAR CON DETALLES", "observacion": "2.- TRABAJA SIN DETENERSE EN DETALLES, TENDIENDO A PERDER DETALLES IMPORTANTES PARA EL ÉXITO DE SU TRABAJO."},
        3: {"descripcion": "INTERESADO EN TRABAJAR CON DETALLES", "observacion": "3.- POCO INTERÉS POR DETALLES, PREFIRIENDO LA VISIÓN DEL CONJUNTO."},
        4: {"descripcion": "INTERESADO EN TRABAJAR CON DETALLES", "observacion": "4.- INTERÉS PERSONAL REGULAR POR DETALLES."},
        5: {"descripcion": "INTERESADO EN TRABAJAR CON DETALLES", "observacion": "5.- BUENA CAPACIDAD DE VER DETALLES Y TRABAJAR CON ELLOS."},
        6: {"descripcion": "INTERESADO EN TRABAJAR CON DETALLES", "observacion": "7/6.- LE AGRADA REALIZAR TRABAJOS QUE EXIJAN ATENCIÓN EN DETALLES."},
        7: {"descripcion": "INTERESADO EN TRABAJAR CON DETALLES", "observacion": "7/6.- LE AGRADA REALIZAR TRABAJOS QUE EXIJAN ATENCIÓN EN DETALLES."},
        8: {"descripcion": "INTERESADO EN TRABAJAR CON DETALLES", "observacion": "8.- SE DEDICA A ELIMINAR PORMENORES, PERDIENDO LA VISIÓN DEL CONJUNTO."},
        9: {"descripcion": "INTERESADO EN TRABAJAR CON DETALLES", "observacion": "9.- GRAN INTERÉS EN DETALLES. TIENDE A OMITIR CONCEPTOS IMPORTANTES Y PERDER LA VISIÓN DEL CONJUNTO."}
    },
    "C": {
        0: {"descripcion": "TIPO ORGANIZADO", "observacion": "1.- EXTREMADAMENTE DESORGANIZADO."},
        1: {"descripcion": "TIPO ORGANIZADO", "observacion": "1.- EXTREMADAMENTE DESORGANIZADO."},
        2: {"descripcion": "TIPO ORGANIZADO", "observacion": "2.- MÍNIMA PREOCUPACIÓN DE ORDEN Y ORGANIZACIÓN."},
        3: {"descripcion": "TIPO ORGANIZADO", "observacion": "3.- POCA PREOCUPACIÓN DE ORDEN Y ORGANIZACIÓN."},
        4: {"descripcion": "TIPO ORGANIZADO", "observacion": "4.- POCO ORGANIZADO."},
        5: {"descripcion": "TIPO ORGANIZADO", "observacion": "5.- ES UNA PERSONA CON AGRADO REGULAR DE ORGANIZACIÓN."},
        6: {"descripcion": "TIPO ORGANIZADO", "observacion": "7/6.- MUY ORGANIZADO, TRATA DE ESTAR CON TODO SU MATERIAL SIEMPRE EN ORDEN."},
        7: {"descripcion": "TIPO ORGANIZADO", "observacion": "7/6.- MUY ORGANIZADO, TRATA DE ESTAR CON TODO SU MATERIAL SIEMPRE EN ORDEN."},
        8: {"descripcion": "TIPO ORGANIZADO", "observacion": "8.- EXTREMADAMENTE ORGANIZADO, NO CONSIGUE TRABAJAR EN AMBIENTE DESORGANIZADO."},
        9: {"descripcion": "TIPO ORGANIZADO", "observacion": "9.- EXAGERADA PREOCUPACIÓN CON EL ORDEN Y ORGANIZACIÓN, NO CONSIGUE TRABAJAR EN AMBIENTE DESORGANIZADO."}
    },
    "Z": {
        0: {"descripcion": "NECESIDAD DE CAMBIO. NECESIDAD DE IDENTIFICARSE", "observacion": "1.- TIENE GRAN DIFICULTAD PARA ENFRENTAR NUEVAS SITUACIONES Y CAMBIOS; NECESITA TRABAJOS RUTINARIOS Y REPETIDOS EN SITUACIONES ESTABLES"},
        1: {"descripcion": "NECESIDAD DE CAMBIO. NECESIDAD DE IDENTIFICARSE", "observacion": "1.- TIENE GRAN DIFICULTAD PARA ENFRENTAR NUEVAS SITUACIONES Y CAMBIOS; NECESITA TRABAJOS RUTINARIOS Y REPETIDOS EN SITUACIONES ESTABLES"},
        2: {"descripcion": "NECESIDAD DE CAMBIO. NECESIDAD DE IDENTIFICARSE", "observacion": "2.- RESISTENTE A LAS MUDANZAS, ES MÁS INDICADO PARA TRABAJOS DE RUTINA Y REPETIDOS."},
        3: {"descripcion": "NECESIDAD DE CAMBIO. NECESIDAD DE IDENTIFICARSE", "observacion": "3.- POSEE CIERTA RESERVA A LOS CAMBIOS. PREFIERE TRABAJOS DE RUTINA Y REPETIDOS."},
        4: {"descripcion": "NECESIDAD DE CAMBIO. NECESIDAD DE IDENTIFICARSE", "observacion": "4.- MEDIANAMENTE RECEPTIVO A LOS CAMBIOS, DEPENDIENDO DE LAS CIRCUNSTANCIAS QUE LAS ENVUELVEN, PUEDE OFRECER RESISTENCIA A LOS MISMOS."},
        5: {"descripcion": "NECESIDAD DE CAMBIO. NECESIDAD DE IDENTIFICARSE", "observacion": "5.- RECEPTIVO A LOS CAMBIOS. SE AJUSTA A LOS MISMOS."},
        6: {"descripcion": "NECESIDAD DE CAMBIO. NECESIDAD DE IDENTIFICARSE", "observacion": "6.- SE AJUSTA FÁCILMENTE A LOS CAMBIOS; TIENE FLEXIBILIDAD DE PENSAMIENTO."},
        7: {"descripcion": "NECESIDAD DE CAMBIO. NECESIDAD DE IDENTIFICARSE", "observacion": "7.- NECESITA VARIAR SUS ACTIVIDADES, IDENTIFICÁNDOSE CON CAMBIOS Y CON LO QUE ES NUEVO. PREFIERE TRABAJOS QUE EXIJAN CREATIVIDAD."},
        8: {"descripcion": "NECESIDAD DE CAMBIO. NECESIDAD DE IDENTIFICARSE", "observacion": "8.- ES IMPULSADO A MUDAR FRECUENTEMENTE SUS PREFERENCIAS, NECESITA CAMBIOS CONTINUAMENTE EN EL TRABAJO."},
        9: {"descripcion": "NECESIDAD DE CAMBIO. NECESIDAD DE IDENTIFICARSE", "observacion": "9.- ES IMPULSADO POR UNA FUERTE NECESIDAD DE CAMBIAR CONSTANTEMENTE SUS ACTIVIDADES, SIENDO INCONSTANTE EN SUS PREFERENCIAS."}
    },
    "N": {
        0: {"descripcion": "NECESIDAD DE COMPLETAR LA TAREA.", "observacion": "1.- PERSONA QUE SE PREOCUPA PRINCIPALMENTE EN FIJAR OBJETIVOS Y METAS, NO SINTIENDO NINGUNA NECESIDAD EN ACABAR LO QUE INICIA."},
        1: {"descripcion": "NECESIDAD DE COMPLETAR LA TAREA.", "observacion": "1.- PERSONA QUE SE PREOCUPA PRINCIPALMENTE EN FIJAR OBJETIVOS Y METAS, NO SINTIENDO NINGUNA NECESIDAD EN ACABAR LO QUE INICIA."},
        2: {"descripcion": "NECESIDAD DE COMPLETAR LA TAREA.", "observacion": "2.- PERSONA QUE NO SIENTE LA NECESIDAD DE COMPLETAR TAREAS PERSONALMENTE, PREFIERE DESCENTRALIZAR LOS TRABAJOS PARA PERMANECER EN UNA ACTIVIDAD."},
        3: {"descripcion": "NECESIDAD DE COMPLETAR LA TAREA.", "observacion": "3.- PUEDE DELEGAR SUS TRABAJOS. PUEDE REALIZAR MUCHAS TAREAS SIMULTÁNEAMENTE."},
        4: {"descripcion": "NECESIDAD DE COMPLETAR LA TAREA.", "observacion": "4.- PUEDE DELEGAR SUS TRABAJOS. PUEDE REALIZAR ALGUNAS TAREAS SIMULTÁNEAMENTE."},
        5: {"descripcion": "NECESIDAD DE COMPLETAR LA TAREA.", "observacion": "5.- PUEDE DELEGAR PARTE DE SUS TRABAJOS, DEJANDO PARA SÍ LA REALIZACIÓN COMPLETA DE BUENA PARTE DE ELLA."},
        6: {"descripcion": "NECESIDAD DE COMPLETAR LA TAREA.", "observacion": "6.- TIENE NECESIDAD DE COMPLETAR SUS TAREAS."},
        7: {"descripcion": "NECESIDAD DE COMPLETAR LA TAREA.", "observacion": "7.- NECESITA MUCHO TERMINAR LO QUE COMIENZA; FIJA TODA SU ATENCIÓN EN LA REALIZACIÓN DE UNA TAREA HASTA TERMINARLA."},
        8: {"descripcion": "NECESIDAD DE COMPLETAR LA TAREA.", "observacion": "8.- PERSISTENTE. TIENE DIFICULTAD EN DEJAR LA TAREA QUE ESTÁ HACIENDO. TIENE QUE COMPLETAR LO QUE COMIENZA."},
        9: {"descripcion": "NECESIDAD DE COMPLETAR LA TAREA.", "observacion": "9.- NO CONSIGUE DEJAR LO QUE ESTÁ HACIENDO. ES EXTREMADAMENTE PREOCUPADO CON LA NECESIDAD DE COMPLETAR UNA TAREA."}
    },
    "A": {
        0: {"descripcion": "NECESIDAD DE REALIZAR ( INICIATIVA)", "observacion": "1.- TIENE DIFICULTAD PARA TERMINAR LO QUE INICIA, NO TIENE INICIATIVA, NO ENCUENTRA RECOMPENSA EN EL TRABAJO, REALIZÁNDOSE EN OTROS PLANOS."},
        1: {"descripcion": "NECESIDAD DE REALIZAR ( INICIATIVA)", "observacion": "1.- TIENE DIFICULTAD PARA TERMINAR LO QUE INICIA, NO TIENE INICIATIVA, NO ENCUENTRA RECOMPENSA EN EL TRABAJO, REALIZÁNDOSE EN OTROS PLANOS."},
        2: {"descripcion": "NECESIDAD DE REALIZAR ( INICIATIVA)", "observacion": "2.- TIENDE A TENER DIFICULTADES EN TERMINAR LO QUE INICIA, NECESITA SER PRESIONADO PARA REALIZAR SU TRABAJO."},
        3: {"descripcion": "NECESIDAD DE REALIZAR ( INICIATIVA)", "observacion": "3.- NO SIENTE PREOCUPACIÓN DE TERMINAR LO QUE INICIA; NO ES AMBICIOSO, TIENDE A NO REALIZARSE A TRAVÉS DE EJECUCIÓN DE TAREAS."},
        4: {"descripcion": "NECESIDAD DE REALIZAR ( INICIATIVA)", "observacion": "4.- SIENTE LA NECESIDAD DE TERMINAR UNA TAREA CUANDO LA INICIA; TIENE UN GRADO REGULAR DE AMBICIÓN."},
        5: {"descripcion": "NECESIDAD DE REALIZAR ( INICIATIVA)", "observacion": "5.- TIENE INICIATIVA. TIENE UN GRADO DE AMBICIÓN REGULAR; SE REALIZA A TRAVÉS DEL TRABAJO."},
        6: {"descripcion": "NECESIDAD DE REALIZAR ( INICIATIVA)", "observacion": "6.- ES AMBICIOSO, TOMA LA INICIATIVA; TIENE UNA NECESIDAD INTENSA DE REALIZAR; TIENE EL DESEO DE SER EL MEJOR; FIJA ALTOS PADRONES DE EJECUCIÓN."},
        7: {"descripcion": "NECESIDAD DE REALIZAR ( INICIATIVA)", "observacion": "7.- ES AMBICIOSO. TIENE UNA NECESIDAD INTENSA DE REALIZAR, FIJA PADRONES DE EJECUCIÓN MUY ALTOS PARA SÍ Y PARA LOS OTROS;NECESIDAD DE SER EL MEJOR."},
        8: {"descripcion": "NECESIDAD DE REALIZAR ( INICIATIVA)", "observacion": "8.- ES MUY AMBICIOSO; NECESITA SER EL MEJOR; TIENE UNA NECESIDAD EXAGERADA DE REALIZAR. TIENDE A FIJAR PADRONES DE EJECUCIÓN IRREALÍSTICAMENTE ALTOS."},
        9: {"descripcion": "NECESIDAD DE REALIZAR ( INICIATIVA)", "observacion": "9.- ES EXAGERADAMENTE AMBICIOSO; FIJA PADRONES DE EJECUCIÓN EXTREMADAMENTE ALTOS PARA SÍ Y PARA LOS OTROS, SE FRUSTRA CON FACILIDAD LO QUE CONSIGUE"}
    },
    "P": {
        0: {"descripcion": "NECESIDAD DE CONTROLAR A LOS OTROS ( DOMINANCIA ).", "observacion": "1.- NO LE AGRADA ASUMIR RESPONSABILIDAD POR TERCEROS, TIENE DIFICULTAD EN CONTROLAR A LOS OTROS."},
        1: {"descripcion": "NECESIDAD DE CONTROLAR A LOS OTROS ( DOMINANCIA ).", "observacion": "1.- NO LE AGRADA ASUMIR RESPONSABILIDAD POR TERCEROS, TIENE DIFICULTAD EN CONTROLAR A LOS OTROS."},
        2: {"descripcion": "NECESIDAD DE CONTROLAR A LOS OTROS ( DOMINANCIA ).", "observacion": "2.- SE INCLINA POR SÍ MISMO, POCO INTERÉS EN CONTROLAR PERSONAS, TIENE DIFICULTAD EN CONTROLAR A LOS OTROS."},
        3: {"descripcion": "NECESIDAD DE CONTROLAR A LOS OTROS ( DOMINANCIA ).", "observacion": "3.- PREFIERE NO RESPONSABILIZARSE POR LOS OTROS. TIENDE A NO CONTROLAR A LOS OTROS."},
        4: {"descripcion": "NECESIDAD DE CONTROLAR A LOS OTROS ( DOMINANCIA ).", "observacion": "4.- AGRADO DE SÍ MISMO Y RESPETA A LOS OTROS. GRADO REGULAR DE PREOCUPACIÓN EN CONTROLAR A LOS OTROS."},
        5: {"descripcion": "NECESIDAD DE CONTROLAR A LOS OTROS ( DOMINANCIA ).", "observacion": "5.- SE INTERESA POR LAS PERSONAS, PUDIENDO EVENTUALMENTE MANEJARLAS, A TRAVÉS DE LA IMAGEN DE PROTECTOR."},
        6: {"descripcion": "NECESIDAD DE CONTROLAR A LOS OTROS ( DOMINANCIA ).", "observacion": "6.- LE AGRADA INFLUENCIAR A LAS PERSONAS TRANSMITIÉNDOLES SUS PUNTOS DE VISTA."},
        7: {"descripcion": "NECESIDAD DE CONTROLAR A LOS OTROS ( DOMINANCIA ).", "observacion": "7.- LE AGRADA SER RESPONSABLE DE LAS PERSONAS; NECESITA INFLUENCIAR A LOS OTROS."},
        8: {"descripcion": "NECESIDAD DE CONTROLAR A LOS OTROS ( DOMINANCIA ).", "observacion": "8.- SE PREOCUPA DE ORIENTAR Y DIRIGIR A LAS PERSONAS, CONTROLÁNDOLAS DE ACUERDO CON SUS PUNTOS DE VISTA."},
        9: {"descripcion": "NECESIDAD DE CONTROLAR A LOS OTROS ( DOMINANCIA ).", "observacion": "9.- PERSONA FUERTEMENTE DOMINANTE. SE PREOCUPA DE DIRIGIR A LAS PERSONAS SEGÚN SU VOLUNTAD."}
    },
    "X": {
        0: {"descripcion": "NECESIDAD DE SER CONSIDERADO", "observacion": "1.- PREFIERE MANTENERSE RESERVADO, LE AGRADA PASAR DESAPERCIBIDO. NO LE AGRADA SER EL CENTRO DE LAS ATENCIONES."},
        1: {"descripcion": "NECESIDAD DE SER CONSIDERADO", "observacion": "1.- PREFIERE MANTENERSE RESERVADO, LE AGRADA PASAR DESAPERCIBIDO. NO LE AGRADA SER EL CENTRO DE LAS ATENCIONES."},
        2: {"descripcion": "NECESIDAD DE SER CONSIDERADO", "observacion": "2.- ES RESERVADO EN SUS CONTACTOS SOCIALES, TIENDE A NO SENTIRSE BIEN CUANDO ES EL CENTRO DE LAS ATENCIONES."},
        3: {"descripcion": "NECESIDAD DE SER CONSIDERADO", "observacion": "3.- ES SINCERO EN SUS CONTACTOS SOCIALES."},
        4: {"descripcion": "NECESIDAD DE SER CONSIDERADO", "observacion": "4.- GRADO REGULAR DE SOLICITUD , TIENDE A SABER ESCUCHAR A LAS PERSONAS."},
        5: {"descripcion": "NECESIDAD DE SER CONSIDERADO", "observacion": "5.- ES SOLÍCITO BUSCANDO AMISTAD EN EL APOYO DE LOS OTROS."},
        6: {"descripcion": "NECESIDAD DE SER CONSIDERADO", "observacion": "6.- PERSONA QUE LE AGRADA RECIBIR ATENCIÓN DE LOS OTROS Y DE SER NOTADO."},
        7: {"descripcion": "NECESIDAD DE SER CONSIDERADO", "observacion": "7.- LE AGRADA HABLAR RESPECTO DE SUS ACTIVIDADES CON EL FIN DE SENTIRSE VALORIZADO Y ACEPTADO."},
        8: {"descripcion": "NECESIDAD DE SER CONSIDERADO", "observacion": "8.- NECESITA SENTIRSE VALORIZADO POR LAS PERSONAS, LLAMANDO LA ATENCIÓN SOBRE SÍ MISMO."},
        9: {"descripcion": "NECESIDAD DE SER CONSIDERADO", "observacion": "9.- EXAGERADAMENTE DEPENDIENTE DE LAS OPINIONES DE LOS OTROS, TRATA DE HACERSE NOTAR EN EL GRUPO EN EL CUAL SE ENCUENTRA."}
    },
    "B": {
        0: {"descripcion": "NECESIDAD DE PERTENECER A GRUPOS.", "observacion": "1.- INDEPENDIENTE, NO PRESTA IMPORTANCIA A LA PARTICIPACIÓN EN GRUPOS. TIENE OPINIONES Y PUNTOS DE VISTA PROPIOS,  DIFICULTAD CUANDO TRABAJA EN EQUIPO."},
        1: {"descripcion": "NECESIDAD DE PERTENECER A GRUPOS.", "observacion": "1.- INDEPENDIENTE, NO PRESTA IMPORTANCIA A LA PARTICIPACIÓN EN GRUPOS. TIENE OPINIONES Y PUNTOS DE VISTA PROPIOS,  DIFICULTAD CUANDO TRABAJA EN EQUIPO."},
        2: {"descripcion": "NECESIDAD DE PERTENECER A GRUPOS.", "observacion": "2.- COMPORTAMIENTO INDEPENDIENTE, NO SE PREOCUPA DE ESTAR DE ACUERDO CON LOS MIEMBROS DEL GRUPO, NO SIENDO INFLUENCIABLE POR LAS OPINIONES DEL MISMO. "},
        3: {"descripcion": "NECESIDAD DE PERTENECER A GRUPOS.", "observacion": "3.- PERSONA NO INFLUENCIABLE POR LAS ACTITUDES Y PUNTOS DE VISTA DEL GRUPO. ES INDEPENDIENTE PUDIENDO ENTRAR EN CONFLICTO CON LAS OPINIONES DEL GRUPO."},
        4: {"descripcion": "NECESIDAD DE PERTENECER A GRUPOS.", "observacion": "4.- ESTÁ EN IGUALDAD CON EL GRUPO, AL MISMO TIEMPO QUE INFLUENCIA AL GRUPO PUEDE CEDER EN SUS PUNTOS DE VISTA."},
        5: {"descripcion": "NECESIDAD DE PERTENECER A GRUPOS.", "observacion": "5.- PARTICIPA DEL GRUPO RECIBIENDO CIERTA INFLUENCIA, PUDIENDO INFLUENCIARSE POR LAS OPINIONES DEL GRUPO."},
        6: {"descripcion": "NECESIDAD DE PERTENECER A GRUPOS.", "observacion": "6.- LE AGRADA ESCUCHAR Y SEGUIR AL GRUPO. ES INFLUENCIABLES POR LAS ACTITUDES Y PUNTOS DE VISTA DEL GRUPO."},
        7: {"descripcion": "NECESIDAD DE PERTENECER A GRUPOS.", "observacion": "7.- NECESITA COMPORTARSE DE ACUERDO CON LAS ACTITUDES Y PUNTOS DE VISTA DEL GRUPO TENDIENDO A DEPENDER DEL MISMO."},
        8: {"descripcion": "NECESIDAD DE PERTENECER A GRUPOS.", "observacion": "8.- FUERTEMENTE INFLUENCIABLE POR LOS PUNTOS DE VISTA Y ACTITUDES DEL GRUPO. ES DEPENDIENTE DE LA APROBACIÓN DEL GRUPO."},
        9: {"descripcion": "NECESIDAD DE PERTENECER A GRUPOS.", "observacion": "9.- ES DEPENDIENTE DEL GRUPO. SUBORDINA SUS OPINIONES Y ACTITUDES COMPORTÁNDOSE TOTALMENTE DE ACUERDO CON EL GRUPO. MOTIVADO POR EL TRABAJO EN EQUIPO"}
    },
    "O": {
        0: {"descripcion": "NECESIDAD AFECTIVA.", "observacion": "0.- DIFICULTAD EN SU RELACIONAMIENTO, ES MUY FORMAL."},
        1: {"descripcion": "NECESIDAD AFECTIVA.", "observacion": "1.- TIENE UN MODO RACIONAL DE ABORDAR LAS COSAS (INTELECTUALIZADA) CIERTA DIFICULTAD DE RELACIONAMIENTO."},
        2: {"descripcion": "NECESIDAD AFECTIVA.", "observacion": "3/2.- MANTIENE UN RELACIONAMIENTO FORMAL CON LAS PERSONAS."},
        3: {"descripcion": "NECESIDAD AFECTIVA.", "observacion": "3/2.- MANTIENE UN RELACIONAMIENTO FORMAL CON LAS PERSONAS."},
        4: {"descripcion": "NECESIDAD AFECTIVA.", "observacion": "4.- LE AGRADA PERTENECER AL GRUPO Y PARTICIPAR CON OTRAS PERSONAS."},
        5: {"descripcion": "NECESIDAD AFECTIVA.", "observacion": "5.- SE RELACIONA CÁLIDAMENTE CON LAS PERSONAS."},
        6: {"descripcion": "NECESIDAD AFECTIVA.", "observacion": "6.- PERSONA QUE LE AGRADA RECIBIR EL AFECTO DE LOS OTROS."},
        7: {"descripcion": "NECESIDAD AFECTIVA.", "observacion": "7.- NECESITA TENER EL AFECTO Y APOYO DE LOS OTROS."},
        8: {"descripcion": "NECESIDAD AFECTIVA.", "observacion": "8.- SENSIBLE, NECESITA OBTENER EL AFECTO Y APOYO DE LOS OTROS EN SU RELACIONAMIENTO."},
        9: {"descripcion": "NECESIDAD AFECTIVA.", "observacion": "9.- ES EXTREMADAMENTE AFECTIVO EN SU RELACIONAMIENTO; SIENTE LA NECESIDAD DE SER QUERIDO."}
    },
    "E": {
        0: {"descripcion": "TIPO EMOCIONALMENTE CONTENIDO", "observacion": "1.- DEJA REFLEJAR SUS EMOCIONES EN EL TRABAJO, NECESITANDO SER DINÁMICO,COMPLETAMENTE EMOCIONALMENTE CON EL TRABAJO QUE REALIZA."},
        1: {"descripcion": "TIPO EMOCIONALMENTE CONTENIDO", "observacion": "1.- DEJA REFLEJAR SUS EMOCIONES EN EL TRABAJO, NECESITANDO SER DINÁMICO,COMPLETAMENTE EMOCIONALMENTE CON EL TRABAJO QUE REALIZA."},
        2: {"descripcion": "TIPO EMOCIONALMENTE CONTENIDO", "observacion": "2.- DEJA REFLEJAR SUS EMOCIONES, TIENE EXPRESIÓN DINÁMICA Y DRAMÁTICA; GASTA MUCHA ENERGÍA CUANDO TRABAJA."},
        3: {"descripcion": "TIPO EMOCIONALMENTE CONTENIDO", "observacion": "3.- TIENDE A ENVOLVERSE EMOCIONALMENTE CON SU TRABAJO, ES DINÁMICO EN SU EXPRESIÓN, DEJANDO REFLEJAR SUS EMOCIONES."},
        4: {"descripcion": "TIPO EMOCIONALMENTE CONTENIDO", "observacion": "4.- GRADO REGULAR DE ENVOLVIMIENTO EMOCIONAL CON EL TRABAJO, SE ESFUERZA PARA QUE SUS EMOCIONES NO INTERFIERAN EN EL TRABAJO."},
        5: {"descripcion": "TIPO EMOCIONALMENTE CONTENIDO", "observacion": "5.- POCO ENVOLVIMIENTO EMOCIONAL EN EL TRABAJO, EQUILIBRA SUS EMOCIONES."},
        6: {"descripcion": "TIPO EMOCIONALMENTE CONTENIDO", "observacion": "6.- TIENDE A SER CALMADO Y FORMAL EN EL TRABAJO, CONTROLA SUS EMOCIONES."},
        7: {"descripcion": "TIPO EMOCIONALMENTE CONTENIDO", "observacion": "7.- ES CALMADO Y FORMAL EN EL TRABAJO, CONTIENE SUS EMOCIONES DIFÍCILMENTE DEMUESTRA LO QUE ESTÁ SINTIENDO."},
        8: {"descripcion": "TIPO EMOCIONALMENTE CONTENIDO", "observacion": "8.- ES FRÍO Y FORMAL EN EL TRABAJO; CARACTERÍSTICAMENTE RACIONAL; NO DEMUESTRA LO QUE SIENTE, TIENDE A ESCONDER SUS EMOCIONES."},
        9: {"descripcion": "TIPO EMOCIONALMENTE CONTENIDO", "observacion": "9.- ES RACIONAL Y FORMAL EN SU TRABAJO, RACIONALIZANDO SUS EMOCIONES, NO SE PERMITE DEMOSTRACIONES AFECTIVAS EN EL TRABAJO."}
    },
    "K": {
        0: {"descripcion": "NECESIDAD DE SER DEFENSIVAMENTE AGRESIVO", "observacion": "1.- NO MANIFIESTA SUS OPINIONES FRANCAMENTE, ESTANDO A LA DEFENSIVA CASI SIEMPRE."},
        1: {"descripcion": "NECESIDAD DE SER DEFENSIVAMENTE AGRESIVO", "observacion": "1.- NO MANIFIESTA SUS OPINIONES FRANCAMENTE, ESTANDO A LA DEFENSIVA CASI SIEMPRE."},
        2: {"descripcion": "NECESIDAD DE SER DEFENSIVAMENTE AGRESIVO", "observacion": "2.- ESTÁ A LA DEFENSIVA LA MAYOR PARTE DEL TIEMPO, DIFÍCILMENTE SE MANIFIESTA ABIERTAMENTE."},
        3: {"descripcion": "NECESIDAD DE SER DEFENSIVAMENTE AGRESIVO", "observacion": "3.- POSEE RESERVA EN LA MANIFESTACIÓN DE SU S OPINIONES. TIENDE A ESTAR EN LA DEFENSIVA."},
        4: {"descripcion": "NECESIDAD DE SER DEFENSIVAMENTE AGRESIVO", "observacion": "4.- TIENDE A ESTAR A LA DEFENSIVA CON LAS PERSONAS."},
        5: {"descripcion": "NECESIDAD DE SER DEFENSIVAMENTE AGRESIVO", "observacion": "5.- GRADO MEDIO DE DEFENSA, TIENDE A SER RESERVADO."},
        6: {"descripcion": "NECESIDAD DE SER DEFENSIVAMENTE AGRESIVO", "observacion": "6.- CAPACIDAD PARA ENFRENTAR Y ARGUMENTAR CON LAS PERSONAS."},
        7: {"descripcion": "NECESIDAD DE SER DEFENSIVAMENTE AGRESIVO", "observacion": "7.- ENFRENTA LAS PERSONAS, ES ABIERTO Y SINCERO."},
        8: {"descripcion": "NECESIDAD DE SER DEFENSIVAMENTE AGRESIVO", "observacion": "9/8.- PERSONA QUE SE OPONE Y ENFRENTA FRANCA Y ABIERTAMENTE A LOS OTROS."},
        9: {"descripcion": "NECESIDAD DE SER DEFENSIVAMENTE AGRESIVO", "observacion": "9/8.- PERSONA QUE SE OPONE Y ENFRENTA FRANCA Y ABIERTAMENTE A LOS OTROS."}
    },
    "F": {
        0: {"descripcion": "NECESIDAD DE OBEDIENCIA A LA AUTORIDAD.", "observacion": "1.- ES REBELDE ANTE LA AUTORIDAD. NECESITA SENTIRSE LIBRE Y EXENTO DE CONTROL DE LA JEFATURA; SU OPINIÓN RESPECTO DE SU TRABAJO ES EL FACTOR QUE LO MOTIVA."},
        1: {"descripcion": "NECESIDAD DE OBEDIENCIA A LA AUTORIDAD.", "observacion": "1.- ES REBELDE ANTE LA AUTORIDAD. NECESITA SENTIRSE LIBRE Y EXENTO DE CONTROL DE LA JEFATURA; SU OPINIÓN RESPECTO DE SU TRABAJO ES EL FACTOR QUE LO MOTIVA."},
        2: {"descripcion": "NECESIDAD DE OBEDIENCIA A LA AUTORIDAD.", "observacion": "2.- COMPORTAMIENTO INDEPENDIENTE, POCA PREOCUPACIÓN EN ESTAR DE ACUERDO CON LA AUTORIDAD, PREFIERE NO RECIBIR SUPERVISIÓN."},
        3: {"descripcion": "NECESIDAD DE OBEDIENCIA A LA AUTORIDAD.", "observacion": "3.- AUTO-CONFIADO Y MOTIVADO POR EL TRABAJO Y NO POR EL RECONOCIMIENTO DEL JEFE. SE SIENTE LIBRE PARA EXPRESAR SUS PUNTOS DE VISTA."},
        4: {"descripcion": "NECESIDAD DE OBEDIENCIA A LA AUTORIDAD.", "observacion": "4.- TIENE CONFIANZA EN SÍ MISMO, NO DEPENDIENDO DEL CONTROL DE LA JEFATURA, EVENTUALMENTE PUEDE ARGUMENTAR CON LA JEFATURA."},
        5: {"descripcion": "NECESIDAD DE OBEDIENCIA A LA AUTORIDAD.", "observacion": "5.- TIENE CONFIANZA EN SÍ MISMO, CONVIVIENDO EN IGUALDAD CON LA AUTORIDAD."},
        6: {"descripcion": "NECESIDAD DE OBEDIENCIA A LA AUTORIDAD.", "observacion": "6.- INFLUENCIABLE POR LAS OPINIONES Y PUNTOS DE VISTA DE SUS SUPERIORES; TRATA DE CORRESPONDER A LA EXPECTATIVA DE SU SUPERIORES."},
        7: {"descripcion": "NECESIDAD DE OBEDIENCIA A LA AUTORIDAD.", "observacion": "7.- NECESITA OBEDECER AL JEFE PARA RECIBIR ESTÍMULOS QUE LO MOTIVEN."},
        8: {"descripcion": "NECESIDAD DE OBEDIENCIA A LA AUTORIDAD.", "observacion": "8.- SE PREOCUPA MUCHO EN RESPETAR Y OBEDECER AL JEFE, TRATANDO DE ASEGURARSE DEL VALOR DE SU TRABAJO."},
        9: {"descripcion": "NECESIDAD DE OBEDIENCIA A LA AUTORIDAD.", "observacion": "9.- NO TIENE CONFIANZA EN SÍ MISMO, DEPENDE DEL APOYO DE SU JEFE PARA PODER TRABAJAR. NECESITA SER CONSTANTEMENTE MOTIVADO POR LA AUTORIDAD."}
    },
    "W": {
        0: {"descripcion": "NECESIDAD DE REGLAMENTO Y SUPERVISION.", "observacion": "1.- NO LE AGRADA SEGUIR REGLAMENTOS, LE AGRADA IR Y VENIR LIBREMENTE, ES AUTO-DIRIGIDO, NO LE AGRADA SER ORIENTADO."},
        1: {"descripcion": "NECESIDAD DE REGLAMENTO Y SUPERVISION.", "observacion": "1.- NO LE AGRADA SEGUIR REGLAMENTOS, LE AGRADA IR Y VENIR LIBREMENTE, ES AUTO-DIRIGIDO, NO LE AGRADA SER ORIENTADO."},
        2: {"descripcion": "NECESIDAD DE REGLAMENTO Y SUPERVISION.", "observacion": "2.- PERSONA QUE PREFIERE NO SEGUIR NORMAS. LE AGRADA SER LIBRE. PREFIERE AUTO-DIRIGIRSE A SER ORIENTADO."},
        3: {"descripcion": "NECESIDAD DE REGLAMENTO Y SUPERVISION.", "observacion": "3.- POCA NECESIDAD DE REGLAMENTOS Y NORMAS, PREFIERE RECIBIR SUPERVISIÓN APENAS OCASIONALMENTE."},
        4: {"descripcion": "NECESIDAD DE REGLAMENTO Y SUPERVISION.", "observacion": "4.- REGULAR INTERÉS POR SEGUIR NORMAS Y REGLAMENTOS."},
        5: {"descripcion": "NECESIDAD DE REGLAMENTO Y SUPERVISION.", "observacion": "5.- LE AGRADA SEGUIR REGLAMENTOS Y OBTENER \"LA PALABRA OFICIAL\"."},
        6: {"descripcion": "NECESIDAD DE REGLAMENTO Y SUPERVISION.", "observacion": "6.- LE AGRADA SEGUIR NORMAS Y REGLAMENTOS."},
        7: {"descripcion": "NECESIDAD DE REGLAMENTO Y SUPERVISION.", "observacion": "7.- NECESITA RESPETAR NORMAS Y REGLAMENTOS."},
        8: {"descripcion": "NECESIDAD DE REGLAMENTO Y SUPERVISION.", "observacion": "8.- SE PREOCUPA MUCHO EN RESPETAR NORMAS Y REGLAMENTOS."},
        9: {"descripcion": "NECESIDAD DE REGLAMENTO Y SUPERVISION.", "observacion": "9.- NECESITA DE NORMAS Y REGLAMENTOS PARA PODER TRABAJAR."}
    }
}

ALL_FACTORS = list(KOSTICK_SCORING.keys())

def crear_interfaz_kostick(supabase: Client):
    st.components.v1.html("<script>window.top.scrollTo(0, 0);</script>", height=0)
    st.title("Test de Preferencias Personales Kostick")
    st.markdown("---")
    st.info(
        """
        **Instrucciones:** A continuación encontrará una serie de frases agrupadas en pares. 
        Lea cada par de frases y marque la que MEJOR lo describe a usted. 
        Puede que ambas frases le describan bien, o que ninguna lo describa adecuadamente; 
        escoja de todas maneras la que usted considere que MEJOR lo describe.
        """
    )

    with st.form(key="kostick_form"):
        st.markdown("---")
        comprende = st.checkbox("Sí, comprendo las instrucciones.", key="comprende_kostick")
        st.markdown("---")
        
        respuestas_usuario = {} # Guardará el factor elegido para cada pregunta

        for i in range(1, 91):
            question_data = KOSTICK_QUESTIONS.get(i)
            if not question_data:
                # Omitir silenciosamente las preguntas faltantes en el diccionario
                continue

            opcion_1_text = question_data["opcion_1"]["texto"]
            opcion_0_text = question_data["opcion_0"]["texto"]
            
            # Mostrar las opciones como radio buttons
            st.write(f"**{i}.-**")
            selected_option_text = st.radio(
                f"Seleccione la frase que mejor lo describe para la pregunta {i}",
                [opcion_1_text, opcion_0_text],
                key=f"q_{i}",
                index=None, # No seleccionar ninguna por defecto
                label_visibility="collapsed"
            )

            # Guardar el FACTOR correspondiente a la opción elegida
            if selected_option_text == opcion_1_text:
                respuestas_usuario[f"pregunta_{i}"] = question_data["opcion_1"]["factor"]
            elif selected_option_text == opcion_0_text:
                respuestas_usuario[f"pregunta_{i}"] = question_data["opcion_0"]["factor"]
            else:
                 respuestas_usuario[f"pregunta_{i}"] = None # Marcar como no respondida si no se elige

            if i < 90:
                st.markdown("---")

        siguiente_button = st.form_submit_button("Siguiente")

        if siguiente_button:
            if 'ficha_id' not in st.session_state:
                st.error("Error crítico: No se encontró el ID de la ficha de ingreso.")
                return

            # Verificar que todas las preguntas hayan sido respondidas
            # Solo verificar las preguntas que están definidas en KOSTICK_QUESTIONS
            preguntas_definidas = KOSTICK_QUESTIONS.keys()
            errores = [f"Pregunta {i}" for i in preguntas_definidas if respuestas_usuario.get(f"pregunta_{i}") is None]
            
            if errores:
                st.error("Por favor, responda todas las preguntas. Faltan: " + ", ".join(errores))
            else:
                with st.spinner("Calculando y guardando resultados..."):
                    
                    # 1. Contar la frecuencia de cada factor
                    factor_counts = Counter(respuestas_usuario.values())

                    # 2. Obtener descripción y observación para cada factor
                    factor_results_json = {}
                    for factor in ALL_FACTORS:
                        count = factor_counts.get(factor, 0)
                        scoring_data = KOSTICK_SCORING.get(factor, {}).get(count, 
                                        {"descripcion": "Interpretación no disponible", "observacion": ""})
                        factor_results_json[f"factor_{factor.lower()}"] = json.dumps(scoring_data) # Guardar como string JSON

                    # 3. Preparar datos para Supabase
                    kostick_data_to_save = {
                        "id": st.session_state.ficha_id,
                        "comprende": comprende,
                        # Guardar el factor elegido para cada pregunta (solo las definidas)
                        **{k: v for k, v in respuestas_usuario.items() if k.startswith("pregunta_")},
                        # Guardar los JSON de resultados para cada factor
                        **factor_results_json 
                    }
                    
                    try:
                        # 4. Enviar a Supabase
                        response = supabase.from_('test_kostick').insert(kostick_data_to_save).execute()
                        if response.data:
                            # 5. Guardar datos para el PDF en session_state
                            if 'form_data' not in st.session_state:
                                st.session_state.form_data = {}
                            # Guardar solo los resultados JSON para el PDF
                            st.session_state.form_data['test_kostick'] = factor_results_json 
                            
                            st.session_state.current_test_index += 1
                            st.rerun()
                        else:
                            st.error(f"Error al guardar los resultados: {response.error.message if response.error else 'Error desconocido'}")
                    except Exception as e:
                        st.error(f"Ocurrió una excepción al intentar guardar los resultados: {e}")

