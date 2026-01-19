import streamlit as st
from supabase import Client
from collections import Counter

# Estructura de datos con todas las cualidades y sus letras correspondientes
GRUPOS_DISC = {
    1: {"Entusiasta": "I", "Rápido": "D", "Lógico": "C", "Apacible": "S"},
    2: {"Cauteloso": "C", "Decidido": "D", "Receptivo": "I", "Bondadoso": "S"},
    3: {"Amigable": "I", "Preciso": "C", "Franco": "D", "Tranquilo": "S"},
    4: {"Elocuente": "I", "Controlado": "C", "Tolerante": "S", "Decisivo": "D"},
    5: {"Atrevido": "D", "Concienzudo": "C", "Comunicativo": "I", "Moderado": "S"},
    6: {"Ameno": "I", "Ingenioso": "C", "Investigador": "C", "Acepta riesgos": "D"},
    7: {"Expresivo": "I", "Cuidadoso": "C", "Dominante": "D", "Sensible": "S"},
    8: {"Extrovertido": "I", "Precavido": "C", "Constante": "S", "Impaciente": "D"},
    9: {"Discreto": "C", "Complaciente": "S", "Encantador": "I", "Insistente": "D"},
    10: {"Valeroso": "D", "Anima a los demás": "I", "Pacífico": "S", "Perfeccionista": "C"},
    11: {"Reservado": "C", "Atento": "S", "Osado": "D", "Alegre": "I"},
    12: {"Estimulante": "I", "Gentil": "S", "Perceptivo": "C", "Independiente": "D"},
    13: {"Competitivo": "D", "Considerado": "S", "Alegre": "I", "Sagaz": "C"},
    14: {"Meticuloso": "C", "Obediente": "S", "Ideas firmes": "D", "Alentador": "I"},
    15: {"Popular": "I", "Reflexivo": "C", "Tenaz": "D", "Calmado": "S"},
    16: {"Analítico": "C", "Audaz": "D", "Leal": "S", "Promotor": "I"},
    17: {"Sociable": "I", "Paciente": "S", "Auto suficiente": "D", "Certero": "C"},
    18: {"Adaptable": "S", "Resuelto": "D", "Prevenido": "C", "Vivaz": "I"},
    19: {"Agresivo": "D", "Impetuoso": "I", "Amistoso": "S", "Discerniente": "C"},
    20: {"De trato fácil": "I", "Compasivo": "S", "Cauto": "C", "Habla directo": "D"},
    21: {"Evaluador": "C", "Generoso": "S", "Animado": "I", "Persistente": "D"},
    22: {"Impulsivo": "I", "Cuida los detalles": "C", "Enérgico": "D", "Tranquilo": "S"},
    23: {"Sociable": "I", "Sistemático": "C", "Vigoroso": "D", "Tolerante": "I"},
    24: {"Cautivador": "I", "Contento": "S", "Exigente": "D", "Apegado a las Normas": "C"},
    25: {"Le agrada discutir": "D", "Metódico": "C", "Comedido": "S", "Desenvuelto": "I"},
    26: {"Jovial": "I", "Preciso": "C", "Directo": "D", "Ecuánime": "S"},
    27: {"Inquieto": "D", "Amable": "S", "Elocuente": "I", "Cuidadoso": "C"},
    28: {"Prudente": "C", "Pionero": "D", "Espontáneo": "I", "Colaborador": "S"},
}

# --- Diccionario de perfiles de personalidad (puedes completarlo o modificarlo) ---
PERFILES_DISC = {
    "7777": "Superactivo", "7776": "Superactivo", "7775": "Superactivo", "7774": "Alentador", "7773": "Alentador", "7772": "Alentador", "7771": "Alentador",
    "7767": "Superactivo", "7766": "Superactivo", "7765": "Superactivo", "7764": "Alentador", "7763": "Alentador", "7762": "Alentador", "7761": "Alentador",
    "7757": "Superactivo", "7756": "Superactivo", "7755": "Superactivo", "7754": "Alentador", "7753": "Alentador", "7752": "Alentador", "7751": "Alentador",
    "7747": "Evaluador", "7746": "Evaluador", "7745": "Evaluador", "7744": "Alentador", "7743": "Alentador", "7742": "Alentador", "7741": "Alentador",
    "7737": "Evaluador", "7736": "Evaluador", "7735": "Evaluador", "7734": "Alentador", "7733": "Alentador", "7732": "Alentador", "7731": "Alentador",
    "7727": "Evaluador", "7726": "Evaluador", "7725": "Evaluador", "7724": "Alentador", "7723": "Alentador", "7722": "Alentador", "7721": "Alentador",
    "7717": "Evaluador", "7716": "Evaluador", "7715": "Evaluador", "7714": "Alentador", "7713": "Alentador", "7712": "Alentador", "7711": "Alentador",
    "7677": "Superactivo", "7676": "Superactivo", "7675": "Superactivo", "7674": "Realizador", "7673": "Realizador", "7672": "Realizador", "7671": "Realizador",
    "7667": "Superactivo", "7666": "Superactivo", "7665": "Superactivo", "7664": "Alentador", "7663": "Alentador", "7662": "Alentador", "7661": "Alentador",
    "7657": "Superactivo", "7656": "Superactivo", "7655": "Superactivo", "7654": "Alentador", "7653": "Alentador", "7652": "Alentador", "7651": "Alentador",
    "7647": "Creativo", "7646": "Creativo", "7645": "Creativo", "7644": "Alentador", "7643": "Alentador", "7642": "Alentador", "7641": "Alentador",
    "7637": "Creativo", "7636": "Creativo", "7635": "Creativo", "7634": "Alentador", "7633": "Alentador", "7632": "Alentador", "7631": "Alentador",
    "7627": "Creativo", "7626": "Creativo", "7625": "Creativo", "7624": "Alentador", "7623": "Alentador", "7622": "Alentador", "7621": "Alentador",
    "7617": "Creativo", "7616": "Creativo", "7615": "Creativo", "7614": "Alentador", "7613": "Alentador", "7612": "Alentador", "7611": "Alentador",
    "7577": "Superactivo", "7576": "Superactivo", "7575": "Superactivo", "7574": "Realizador", "7573": "Realizador", "7572": "Realizador", "7571": "Realizador",
    "7567": "Superactivo", "7566": "Superactivo", "7565": "Superactivo", "7564": "Realizador", "7563": "Realizador", "7562": "Realizador", "7561": "Realizador",
    "7557": "Superactivo", "7556": "Superactivo", "7555": "Superactivo", "7554": "Orientado a resultados", "7553": "Orientado a resultados", "7552": "Orientado a resultados", "7551": "Orientado a resultados",
    "7547": "Creativo", "7546": "Creativo", "7545": "Creativo", "7544": "Orientado a resultados", "7543": "Orientado a resultados", "7542": "Orientado a resultados", "7541": "Orientado a resultados",
    "7537": "Creativo", "7536": "Creativo", "7535": "Creativo", "7534": "Orientado a resultados", "7533": "Orientado a resultados", "7532": "Orientado a resultados", "7531": "Orientado a resultados",
    "7527": "Creativo", "7526": "Creativo", "7525": "Creativo", "7524": "Orientado a resultados", "7523": "Orientado a resultados", "7522": "Orientado a resultados", "7521": "Orientado a resultados",
    "7517": "Creativo", "7516": "Creativo", "7515": "Creativo", "7514": "Orientado a resultados", "7513": "Orientado a resultados", "7512": "Orientado a resultados", "7511": "Orientado a resultados",
    "7477": "Investigador", "7476": "Investigador", "7475": "Investigador", "7474": "Realizador", "7473": "Realizador", "7472": "Realizador", "7471": "Realizador",
    "7467": "Investigador", "7466": "Investigador", "7465": "Investigador", "7464": "Realizador", "7463": "Realizador", "7462": "Realizador", "7461": "Realizador",
    "7457": "Investigador", "7456": "Investigador", "7455": "Investigador", "7454": "Realizador", "7453": "Realizador", "7452": "Realizador", "7451": "Realizador",
    "7447": "Creativo", "7446": "Creativo", "7445": "Creativo", "7444": "Orientado a resultados", "7443": "Orientado a resultados", "7442": "Orientado a resultados", "7441": "Orientado a resultados",
    "7437": "Creativo", "7436": "Creativo", "7435": "Creativo", "7434": "Orientado a resultados", "7433": "Orientado a resultados", "7432": "Orientado a resultados", "7431": "Orientado a resultados",
    "7427": "Creativo", "7426": "Creativo", "7425": "Creativo", "7424": "Orientado a resultados", "7423": "Orientado a resultados", "7422": "Orientado a resultados", "7421": "Orientado a resultados",
    "7417": "Creativo", "7416": "Creativo", "7415": "Creativo", "7414": "Orientado a resultados", "7413": "Orientado a resultados", "7412": "Orientado a resultados", "7411": "Orientado a resultados",
    "7377": "Investigador", "7376": "Investigador", "7375": "Investigador", "7374": "Realizador", "7373": "Realizador", "7372": "Realizador", "7371": "Realizador",
    "7367": "Investigador", "7366": "Investigador", "7365": "Investigador", "7364": "Realizador", "7363": "Realizador", "7362": "Realizador", "7361": "Realizador",
    "7357": "Investigador", "7356": "Investigador", "7355": "Investigador", "7354": "Realizador", "7353": "Realizador", "7352": "Realizador", "7351": "Realizador",
    "7347": "Creativo", "7346": "Creativo", "7345": "Creativo", "7344": "Resolutivo", "7343": "Resolutivo", "7342": "Resolutivo", "7341": "Resolutivo",
    "7337": "Creativo", "7336": "Creativo", "7335": "Creativo", "7334": "Resolutivo", "7333": "Resolutivo", "7332": "Resolutivo", "7331": "Resolutivo",
    "7327": "Creativo", "7326": "Creativo", "7325": "Creativo", "7324": "Resolutivo", "7323": "Resolutivo", "7322": "Resolutivo", "7321": "Resolutivo",
    "7317": "Creativo", "7316": "Creativo", "7315": "Creativo", "7314": "Resolutivo", "7313": "Resolutivo", "7312": "Resolutivo", "7311": "Resolutivo",
    "7277": "Investigador", "7276": "Investigador", "7275": "Investigador", "7274": "Realizador", "7273": "Realizador", "7272": "Realizador", "7271": "Realizador",
    "7267": "Investigador", "7266": "Investigador", "7265": "Investigador", "7264": "Realizador", "7263": "Realizador", "7262": "Realizador", "7261": "Realizador",
    "7257": "Investigador", "7256": "Investigador", "7255": "Investigador", "7254": "Realizador", "7253": "Realizador", "7252": "Realizador", "7251": "Realizador",
    "7247": "Creativo", "7246": "Creativo", "7245": "Creativo", "7244": "Resolutivo", "7243": "Resolutivo", "7242": "Resolutivo", "7241": "Resolutivo",
    "7237": "Creativo", "7236": "Creativo", "7235": "Creativo", "7234": "Resolutivo", "7233": "Resolutivo", "7232": "Resolutivo", "7231": "Resolutivo",
    "7227": "Creativo", "7226": "Creativo", "7225": "Creativo", "7224": "Resolutivo", "7223": "Resolutivo", "7222": "Resolutivo", "7221": "Resolutivo",
    "7217": "Creativo", "7216": "Creativo", "7215": "Creativo", "7214": "Resolutivo", "7213": "Resolutivo", "7212": "Resolutivo", "7211": "Resolutivo",
    "7177": "Investigador", "7176": "Investigador", "7175": "Investigador", "7174": "Realizador", "7173": "Realizador", "7172": "Realizador", "7171": "Realizador",
    "7167": "Investigador", "7166": "Investigador", "7165": "Investigador", "7164": "Realizador", "7163": "Realizador", "7162": "Realizador", "7161": "Realizador",
    "7157": "Investigador", "7156": "Investigador", "7155": "Investigador", "7154": "Realizador", "7153": "Realizador", "7152": "Realizador", "7151": "Realizador",
    "7147": "Creativo", "7146": "Creativo", "7145": "Creativo", "7144": "Resolutivo", "7143": "Resolutivo", "7142": "Resolutivo", "7141": "Resolutivo",
    "7137": "Creativo", "7136": "Creativo", "7135": "Creativo", "7134": "Resolutivo", "7133": "Resolutivo", "7132": "Resolutivo", "7131": "Resolutivo",
    "7127": "Creativo", "7126": "Creativo", "7125": "Creativo", "7124": "Resolutivo", "7123": "Resolutivo", "7122": "Resolutivo", "7121": "Resolutivo",
    "7117": "Creativo", "7116": "Creativo", "7115": "Creativo", "7114": "Resolutivo", "7113": "Resolutivo", "7112": "Resolutivo", "7111": "Resolutivo",
    "6777": "Superactivo", "6776": "Superactivo", "6775": "Superactivo", "6774": "Alentador", "6773": "Alentador", "6772": "Alentador", "6771": "Alentador",
    "6767": "Superactivo", "6766": "Superactivo", "6765": "Superactivo", "6764": "Alentador", "6763": "Alentador", "6762": "Alentador", "6761": "Alentador",
    "6757": "Superactivo", "6756": "Superactivo", "6755": "Superactivo", "6754": "Alentador", "6753": "Alentador", "6752": "Alentador", "6751": "Alentador",
    "6747": "Evaluador", "6746": "Evaluador", "6745": "Evaluador", "6744": "Alentador", "6743": "Alentador", "6742": "Alentador", "6741": "Alentador",
    "6737": "Evaluador", "6736": "Evaluador", "6735": "Evaluador", "6734": "Alentador", "6733": "Alentador", "6732": "Alentador", "6731": "Alentador",
    "6727": "Evaluador", "6726": "Evaluador", "6725": "Evaluador", "6724": "Alentador", "6723": "Alentador", "6722": "Alentador", "6721": "Alentador",
    "6717": "Evaluador", "6716": "Evaluador", "6715": "Evaluador", "6714": "Alentador", "6713": "Alentador", "6712": "Alentador", "6711": "Alentador",
    "6677": "Superactivo", "6676": "Superactivo", "6675": "Superactivo", "6674": "Alentador", "6673": "Alentador", "6672": "Alentador", "6671": "Alentador",
    "6667": "Superactivo", "6666": "Superactivo", "6665": "Superactivo", "6664": "Alentador", "6663": "Alentador", "6662": "Alentador", "6661": "Alentador",
    "6657": "Superactivo", "6656": "Superactivo", "6655": "Superactivo", "6654": "Alentador", "6653": "Alentador", "6652": "Alentador", "6651": "Alentador",
    "6647": "Evaluador", "6646": "Evaluador", "6645": "Evaluador", "6644": "Alentador", "6643": "Alentador", "6642": "Alentador", "6641": "Alentador",
    "6637": "Evaluador", "6636": "Evaluador", "6635": "Evaluador", "6634": "Alentador", "6633": "Alentador", "6632": "Alentador", "6631": "Alentador",
    "6627": "Evaluador", "6626": "Evaluador", "6625": "Evaluador", "6624": "Alentador", "6623": "Alentador", "6622": "Alentador", "6621": "Alentador",
    "6617": "Evaluador", "6616": "Evaluador", "6615": "Evaluador", "6614": "Alentador", "6613": "Alentador", "6612": "Alentador", "6611": "Alentador",
    "6577": "Superactivo", "6576": "Superactivo", "6575": "Superactivo", "6574": "Realizador", "6573": "Realizador", "6572": "Realizador", "6571": "Realizador",
    "6567": "Superactivo", "6566": "Superactivo", "6565": "Superactivo", "6564": "Realizador", "6563": "Realizador", "6562": "Realizador", "6561": "Realizador",
    "6557": "Superactivo", "6556": "Superactivo", "6555": "Superactivo", "6554": "Orientado a resultados", "6553": "Orientado a resultados", "6552": "Orientado a resultados", "6551": "Orientado a resultados",
    "6547": "Creativo", "6546": "Creativo", "6545": "Creativo", "6544": "Orientado a resultados", "6543": "Orientado a resultados", "6542": "Orientado a resultados", "6541": "Orientado a resultados",
    "6537": "Creativo", "6536": "Creativo", "6535": "Creativo", "6534": "Orientado a resultados", "6533": "Orientado a resultados", "6532": "Orientado a resultados", "6531": "Orientado a resultados",
    "6527": "Creativo", "6526": "Creativo", "6525": "Creativo", "6524": "Orientado a resultados", "6523": "Orientado a resultados", "6522": "Orientado a resultados", "6521": "Orientado a resultados",
    "6517": "Creativo", "6516": "Creativo", "6515": "Creativo", "6514": "Orientado a resultados", "6513": "Orientado a resultados", "6512": "Orientado a resultados", "6511": "Orientado a resultados",
    "6477": "Investigador", "6476": "Investigador", "6475": "Investigador", "6474": "Realizador", "6473": "Realizador", "6472": "Realizador", "6471": "Realizador",
    "6467": "Investigador", "6466": "Investigador", "6465": "Investigador", "6464": "Realizador", "6463": "Realizador", "6462": "Realizador", "6461": "Realizador",
    "6457": "Investigador", "6456": "Investigador", "6455": "Investigador", "6454": "Realizador", "6453": "Realizador", "6452": "Realizador", "6451": "Realizador",
    "6447": "Creativo", "6446": "Creativo", "6445": "Creativo", "6444": "Orientado a resultados", "6443": "Orientado a resultados", "6442": "Orientado a resultados", "6441": "Orientado a resultados",
    "6437": "Creativo", "6436": "Creativo", "6435": "Creativo", "6434": "Orientado a resultados", "6433": "Orientado a resultados", "6432": "Orientado a resultados", "6431": "Orientado a resultados",
    "6427": "Creativo", "6426": "Creativo", "6425": "Creativo", "6424": "Orientado a resultados", "6423": "Orientado a resultados", "6422": "Orientado a resultados", "6421": "Orientado a resultados",
    "6417": "Creativo", "6416": "Creativo", "6415": "Creativo", "6414": "Orientado a resultados", "6413": "Orientado a resultados", "6412": "Orientado a resultados", "6411": "Orientado a resultados",
    "6377": "Investigador", "6376": "Investigador", "6375": "Investigador", "6374": "Realizador", "6373": "Realizador", "6372": "Realizador", "6371": "Realizador",
    "6367": "Investigador", "6366": "Investigador", "6365": "Investigador", "6364": "Realizador", "6363": "Realizador", "6362": "Realizador", "6361": "Realizador",
    "6357": "Investigador", "6356": "Investigador", "6355": "Investigador", "6354": "Realizador", "6353": "Realizador", "6352": "Realizador", "6351": "Realizador",
    "6347": "Creativo", "6346": "Creativo", "6345": "Creativo", "6344": "Resolutivo", "6343": "Resolutivo", "6342": "Resolutivo", "6341": "Resolutivo",
    "6337": "Creativo", "6336": "Creativo", "6335": "Creativo", "6334": "Resolutivo", "6333": "Resolutivo", "6332": "Resolutivo", "6331": "Resolutivo",
    "6327": "Creativo", "6326": "Creativo", "6325": "Creativo", "6324": "Resolutivo", "6323": "Resolutivo", "6322": "Resolutivo", "6321": "Resolutivo",
    "6317": "Creativo", "6316": "Creativo", "6315": "Creativo", "6314": "Resolutivo", "6313": "Resolutivo", "6312": "Resolutivo", "6311": "Resolutivo",
    "6277": "Investigador", "6276": "Investigador", "6275": "Investigador", "6274": "Realizador", "6273": "Realizador", "6272": "Realizador", "6271": "Realizador",
    "6267": "Investigador", "6266": "Investigador", "6265": "Investigador", "6264": "Realizador", "6263": "Realizador", "6262": "Realizador", "6261": "Realizador",
    "6257": "Investigador", "6256": "Investigador", "6255": "Investigador", "6254": "Realizador", "6253": "Realizador", "6252": "Realizador", "6251": "Realizador",
    "6247": "Creativo", "6246": "Creativo", "6245": "Creativo", "6244": "Resolutivo", "6243": "Resolutivo", "6242": "Resolutivo", "6241": "Resolutivo",
    "6237": "Creativo", "6236": "Creativo", "6235": "Creativo", "6234": "Resolutivo", "6233": "Resolutivo", "6232": "Resolutivo", "6231": "Resolutivo",
    "6227": "Creativo", "6226": "Creativo", "6225": "Creativo", "6224": "Resolutivo", "6223": "Resolutivo", "6222": "Resolutivo", "6221": "Resolutivo",
    "6217": "Creativo", "6216": "Creativo", "6215": "Creativo", "6214": "Resolutivo", "6213": "Resolutivo", "6212": "Resolutivo", "6211": "Resolutivo",
    "6177": "Investigador", "6176": "Investigador", "6175": "Investigador", "6174": "Realizador", "6173": "Realizador", "6172": "Realizador", "6171": "Realizador",
    "6167": "Investigador", "6166": "Investigador", "6165": "Investigador", "6164": "Realizador", "6163": "Realizador", "6162": "Realizador", "6161": "Realizador",
    "6157": "Investigador", "6156": "Investigador", "6155": "Investigador", "6154": "Realizador", "6153": "Realizador", "6152": "Realizador", "6151": "Realizador",
    "6147": "Creativo", "6146": "Creativo", "6145": "Creativo", "6144": "Resolutivo", "6143": "Resolutivo", "6142": "Resolutivo", "6141": "Resolutivo",
    "6137": "Creativo", "6136": "Creativo", "6135": "Creativo", "6134": "Resolutivo", "6133": "Resolutivo", "6132": "Resolutivo", "6131": "Resolutivo",
    "6127": "Creativo", "6126": "Creativo", "6125": "Creativo", "6124": "Resolutivo", "6123": "Resolutivo", "6122": "Resolutivo", "6121": "Resolutivo",
    "6117": "Creativo", "6116": "Creativo", "6115": "Creativo", "6114": "Resolutivo", "6113": "Resolutivo", "6112": "Resolutivo", "6111": "Resolutivo",
    "5777": "Superactivo", "5776": "Superactivo", "5775": "Superactivo", "5774": "Consejero", "5773": "Consejero", "5772": "Consejero", "5771": "Consejero",
    "5767": "Superactivo", "5766": "Superactivo", "5765": "Superactivo", "5764": "Consejero", "5763": "Consejero", "5762": "Consejero", "5761": "Consejero",
    "5757": "Superactivo", "5756": "Superactivo", "5755": "Superactivo", "5754": "Persuasivo", "5753": "Persuasivo", "5752": "Persuasivo", "5751": "Persuasivo",
    "5747": "Evaluador", "5746": "Evaluador", "5745": "Evaluador", "5744": "Persuasivo", "5743": "Persuasivo", "5742": "Persuasivo", "5741": "Persuasivo",
    "5737": "Evaluador", "5736": "Evaluador", "5735": "Evaluador", "5734": "Persuasivo", "5733": "Persuasivo", "5732": "Persuasivo", "5731": "Persuasivo",
    "5727": "Evaluador", "5726": "Evaluador", "5725": "Evaluador", "5724": "Persuasivo", "5723": "Persuasivo", "5722": "Persuasivo", "5721": "Persuasivo",
    "5717": "Evaluador", "5716": "Evaluador", "5715": "Evaluador", "5714": "Persuasivo", "5713": "Persuasivo", "5712": "Persuasivo", "5711": "Persuasivo",
    "5677": "Superactivo", "5676": "Superactivo", "5675": "Superactivo", "5674": "Agente", "5673": "Agente", "5672": "Agente", "5671": "Agente",
    "5667": "Superactivo", "5666": "Superactivo", "5665": "Superactivo", "5664": "Consejero", "5663": "Consejero", "5662": "Consejero", "5661": "Consejero",
    "5657": "Superactivo", "5656": "Superactivo", "5655": "Superactivo", "5654": "Persuasivo", "5653": "Persuasivo", "5652": "Persuasivo", "5651": "Persuasivo",
    "5647": "Evaluador", "5646": "Evaluador", "5645": "Evaluador", "5644": "Persuasivo", "5643": "Persuasivo", "5642": "Persuasivo", "5641": "Persuasivo",
    "5637": "Evaluador", "5636": "Evaluador", "5635": "Evaluador", "5634": "Persuasivo", "5633": "Persuasivo", "5632": "Persuasivo", "5631": "Persuasivo",
    "5627": "Evaluador", "5626": "Evaluador", "5625": "Evaluador", "5624": "Persuasivo", "5623": "Persuasivo", "5622": "Persuasivo", "5621": "Persuasivo",
    "5617": "Evaluador", "5616": "Evaluador", "5615": "Evaluador", "5614": "Persuasivo", "5613": "Persuasivo", "5612": "Persuasivo", "5611": "Persuasivo",
    "5577": "Superactivo", "5576": "Superactivo", "5575": "Superactivo", "5574": "Agente", "5573": "Agente", "5572": "Agente", "5571": "Agente",
    "5567": "Superactivo", "5566": "Superactivo", "5565": "Superactivo", "5564": "Agente", "5563": "Agente", "5562": "Agente", "5561": "Agente",
    "5557": "Superactivo", "5556": "Superactivo", "5555": "Superactivo", "5554": "Desconcertante", "5553": "Consejero", "5552": "Consejero", "5551": "Consejero",
    "5547": "Evaluador", "5546": "Evaluador", "5545": "Evaluador", "5544": "Desconcertante", "5543": "Alentador", "5542": "Alentador", "5541": "Alentador",
    "5537": "Evaluador", "5536": "Evaluador", "5535": "Evaluador", "5534": "Alentador", "5533": "Alentador", "5532": "Alentador", "5531": "Alentador",
    "5527": "Evaluador", "5526": "Evaluador", "5525": "Evaluador", "5524": "Alentador", "5523": "Alentador", "5522": "Alentador", "5521": "Alentador",
    "5517": "Evaluador", "5516": "Evaluador", "5515": "Evaluador", "5514": "Alentador", "5513": "Alentador", "5512": "Alentador", "5511": "Alentador",
    "5477": "Investigador", "5476": "Investigador", "5475": "Investigador", "5474": "Realizador", "5473": "Realizador", "5472": "Realizador", "5471": "Realizador",
    "5467": "Investigador", "5466": "Investigador", "5465": "Investigador", "5464": "Realizador", "5463": "Realizador", "5462": "Realizador", "5461": "Realizador",
    "5457": "Investigador", "5456": "Investigador", "5455": "Investigador", "5454": "Realizador", "5453": "Realizador", "5452": "Realizador", "5451": "Realizador",
    "5447": "Creativo", "5446": "Creativo", "5445": "Creativo", "5444": "Desconcertante", "5443": "Orientado a resultados", "5442": "Orientado a resultados", "5441": "Orientado a resultados",
    "5437": "Creativo", "5436": "Creativo", "5435": "Creativo", "5434": "Orientado a resultados", "5433": "Orientado a resultados", "5432": "Orientado a resultados", "5431": "Orientado a resultados",
    "5427": "Creativo", "5426": "Creativo", "5425": "Creativo", "5424": "Orientado a resultados", "5423": "Orientado a resultados", "5422": "Orientado a resultados", "5421": "Orientado a resultados",
    "5417": "Creativo", "5416": "Creativo", "5415": "Creativo", "5414": "Orientado a resultados", "5413": "Orientado a resultados", "5412": "Orientado a resultados", "5411": "Orientado a resultados",
    "5377": "Investigador", "5376": "Investigador", "5375": "Investigador", "5374": "Realizador", "5373": "Realizador", "5372": "Realizador", "5371": "Realizador",
    "5367": "Investigador", "5366": "Investigador", "5365": "Investigador", "5364": "Realizador", "5363": "Realizador", "5362": "Realizador", "5361": "Realizador",
    "5357": "Investigador", "5356": "Investigador", "5355": "Investigador", "5354": "Realizador", "5353": "Realizador", "5352": "Realizador", "5351": "Realizador",
    "5347": "Creativo", "5346": "Creativo", "5345": "Creativo", "5344": "Resolutivo", "5343": "Resolutivo", "5342": "Resolutivo", "5341": "Resolutivo",
    "5337": "Creativo", "5336": "Creativo", "5335": "Creativo", "5334": "Resolutivo", "5333": "Resolutivo", "5332": "Resolutivo", "5331": "Resolutivo",
    "5327": "Creativo", "5326": "Creativo", "5325": "Creativo", "5324": "Resolutivo", "5323": "Resolutivo", "5322": "Resolutivo", "5321": "Resolutivo",
    "5317": "Creativo", "5316": "Creativo", "5315": "Creativo", "5314": "Resolutivo", "5313": "Resolutivo", "5312": "Resolutivo", "5311": "Resolutivo",
    "5277": "Investigador", "5276": "Investigador", "5275": "Investigador", "5274": "Realizador", "5273": "Realizador", "5272": "Realizador", "5271": "Realizador",
    "5267": "Investigador", "5266": "Investigador", "5265": "Investigador", "5264": "Realizador", "5263": "Realizador", "5262": "Realizador", "5261": "Realizador",
    "5257": "Investigador", "5256": "Investigador", "5255": "Investigador", "5254": "Realizador", "5253": "Realizador", "5252": "Realizador", "5251": "Realizador",
    "5247": "Creativo", "5246": "Creativo", "5245": "Creativo", "5244": "Resolutivo", "5243": "Resolutivo", "5242": "Resolutivo", "5241": "Resolutivo",
    "5237": "Creativo", "5236": "Creativo", "5235": "Creativo", "5234": "Resolutivo", "5233": "Resolutivo", "5232": "Resolutivo", "5231": "Resolutivo",
    "5227": "Creativo", "5226": "Creativo", "5225": "Creativo", "5224": "Resolutivo", "5223": "Resolutivo", "5222": "Resolutivo", "5221": "Resolutivo",
    "5217": "Creativo", "5216": "Creativo", "5215": "Creativo", "5214": "Resolutivo", "5213": "Resolutivo", "5212": "Resolutivo", "5211": "Resolutivo",
    "5177": "Investigador", "5176": "Investigador", "5175": "Investigador", "5174": "Realizador", "5173": "Realizador", "5172": "Realizador", "5171": "Realizador",
    "5167": "Investigador", "5166": "Investigador", "5165": "Investigador", "5164": "Realizador", "5163": "Realizador", "5162": "Realizador", "5161": "Realizador",
    "5157": "Investigador", "5156": "Investigador", "5155": "Investigador", "5154": "Realizador", "5153": "Realizador", "5152": "Realizador", "5151": "Realizador",
    "5147": "Creativo", "5146": "Creativo", "5145": "Creativo", "5144": "Resolutivo", "5143": "Resolutivo", "5142": "Resolutivo", "5141": "Resolutivo",
    "5137": "Creativo", "5136": "Creativo", "5135": "Creativo", "5134": "Resolutivo", "5133": "Resolutivo", "5132": "Resolutivo", "5131": "Resolutivo",
    "5127": "Creativo", "5126": "Creativo", "5125": "Creativo", "5124": "Resolutivo", "5123": "Resolutivo", "5122": "Resolutivo", "5121": "Resolutivo",
    "5117": "Creativo", "5116": "Creativo", "5115": "Creativo", "5114": "Resolutivo", "5113": "Resolutivo", "5112": "Resolutivo", "5111": "Resolutivo",
    "4777": "Profesional", "4776": "Profesional", "4775": "Profesional", "4774": "Consejero", "4773": "Consejero", "4772": "Consejero", "4771": "Consejero",
    "4767": "Profesional", "4766": "Profesional", "4765": "Profesional", "4764": "Consejero", "4763": "Consejero", "4762": "Consejero", "4761": "Consejero",
    "4757": "Profesional", "4756": "Profesional", "4755": "Profesional", "4754": "Consejero", "4753": "Consejero", "4752": "Consejero", "4751": "Consejero",
    "4747": "Evaluador", "4746": "Evaluador", "4745": "Evaluador", "4744": "Promotor", "4743": "Promotor", "4742": "Promotor", "4741": "Promotor",
    "4737": "Evaluador", "4736": "Evaluador", "4735": "Evaluador", "4734": "Promotor", "4733": "Promotor", "4732": "Promotor", "4731": "Promotor",
    "4727": "Evaluador", "4726": "Evaluador", "4725": "Evaluador", "4724": "Promotor", "4723": "Promotor", "4722": "Promotor", "4721": "Promotor",
    "4717": "Evaluador", "4716": "Evaluador", "4715": "Evaluador", "4714": "Promotor", "4713": "Promotor", "4712": "Promotor", "4711": "Promotor",
    "4677": "Profesional", "4676": "Profesional", "4675": "Profesional", "4674": "Agente", "4673": "Agente", "4672": "Agente", "4671": "Agente",
    "4667": "Profesional", "4666": "Profesional", "4665": "Profesional", "4664": "Consejero", "4663": "Consejero", "4662": "Consejero", "4661": "Consejero",
    "4657": "Profesional", "4656": "Profesional", "4655": "Profesional", "4654": "Consejero", "4653": "Consejero", "4652": "Consejero", "4651": "Consejero",
    "4647": "Evaluador", "4646": "Evaluador", "4645": "Evaluador", "4644": "Promotor", "4643": "Promotor", "4642": "Promotor", "4641": "Promotor",
    "4637": "Evaluador", "4636": "Evaluador", "4635": "Evaluador", "4634": "Promotor", "4633": "Promotor", "4632": "Promotor", "4631": "Promotor",
    "4627": "Evaluador", "4626": "Evaluador", "4625": "Evaluador", "4624": "Promotor", "4623": "Promotor", "4622": "Promotor", "4621": "Promotor",
    "4617": "Evaluador", "4616": "Evaluador", "4615": "Evaluador", "4614": "Promotor", "4613": "Promotor", "4612": "Promotor", "4611": "Promotor",
    "4577": "Profesional", "4576": "Profesional", "4575": "Profesional", "4574": "Agente", "4573": "Agente", "4572": "Agente", "4571": "Agente",
    "4567": "Profesional", "4566": "Profesional", "4565": "Profesional", "4564": "Agente", "4563": "Agente", "4562": "Agente", "4561": "Agente",
    "4557": "Profesional", "4556": "Profesional", "4555": "Desconcertante", "4554": "Consejero", "4553": "Consejero", "4552": "Consejero", "4551": "Consejero",
    "4547": "Profesional", "4546": "Profesional", "4545": "Profesional", "4544": "Desconcertante", "4543": "Consejero", "4542": "Consejero", "4541": "Consejero",
    "4537": "Evaluador", "4536": "Evaluador", "4535": "Evaluador", "4534": "Promotor", "4533": "Promotor", "4532": "Promotor", "4531": "Promotor",
    "4527": "Evaluador", "4526": "Evaluador", "4525": "Evaluador", "4524": "Promotor", "4523": "Promotor", "4522": "Promotor", "4521": "Promotor",
    "4517": "Evaluador", "4516": "Evaluador", "4515": "Evaluador", "4514": "Promotor", "4513": "Promotor", "4512": "Promotor", "4511": "Promotor",
    "4477": "Perfeccionista", "4476": "Perfeccionista", "4475": "Perfeccionista", "4474": "Especialista", "4473": "Especialista", "4472": "Especialista", "4471": "Especialista",
    "4467": "Perfeccionista", "4466": "Perfeccionista", "4465": "Perfeccionista", "4464": "Especialista", "4463": "Especialista", "4462": "Especialista", "4461": "Especialista",
    "4457": "Perfeccionista", "4456": "Perfeccionista", "4455": "Desconcertante", "4454": "Desconcertante", "4453": "Especialista", "4452": "Especialista", "4451": "Especialista",
    "4447": "Objetivo", "4446": "Objetivo", "4445": "Desconcertante", "4444": "Desconcertante", "4443": "Desconcertante", "4442": "Subactivo", "4441": "Subactivo",
    "4437": "Objetivo", "4436": "Objetivo", "4435": "Objetivo", "4434": "Desconcertante", "4433": "Desconcertante", "4432": "Subactivo", "4431": "Subactivo",
    "4427": "Objetivo", "4426": "Objetivo", "4425": "Objetivo", "4424": "Subactivo", "4423": "Subactivo", "4422": "Subactivo", "4421": "Subactivo",
    "4417": "Objetivo", "4416": "Objetivo", "4415": "Objetivo", "4414": "Subactivo", "4413": "Subactivo", "4412": "Subactivo", "4411": "Subactivo",
    "4377": "Perfeccionista", "4376": "Perfeccionista", "4375": "Perfeccionista", "4374": "Especialista", "4373": "Especialista", "4372": "Especialista", "4371": "Especialista",
    "4367": "Perfeccionista", "4366": "Perfeccionista", "4365": "Perfeccionista", "4364": "Especialista", "4363": "Especialista", "4362": "Especialista", "4361": "Especialista",
    "4357": "Perfeccionista", "4356": "Perfeccionista", "4355": "Perfeccionista", "4354": "Especialista", "4353": "Especialista", "4352": "Especialista", "4351": "Especialista",
    "4347": "Objetivo", "4346": "Objetivo", "4345": "Objetivo", "4344": "Desconcertante", "4343": "Desconcertante", "4342": "Subactivo", "4341": "Subactivo",
    "4337": "Objetivo", "4336": "Objetivo", "4335": "Objetivo", "4334": "Desconcertante", "4333": "Desconcertante", "4332": "Subactivo", "4331": "Subactivo",
    "4327": "Objetivo", "4326": "Objetivo", "4325": "Objetivo", "4324": "Subactivo", "4323": "Subactivo", "4322": "Subactivo", "4321": "Subactivo",
    "4317": "Objetivo", "4316": "Objetivo", "4315": "Objetivo", "4314": "Subactivo", "4313": "Subactivo", "4312": "Subactivo", "4311": "Subactivo",
    "4277": "Perfeccionista", "4276": "Perfeccionista", "4275": "Perfeccionista", "4274": "Especialista", "4273": "Especialista", "4272": "Especialista", "4271": "Especialista",
    "4267": "Perfeccionista", "4266": "Perfeccionista", "4265": "Perfeccionista", "4264": "Especialista", "4263": "Especialista", "4262": "Especialista", "4261": "Especialista",
    "4257": "Perfeccionista", "4256": "Perfeccionista", "4255": "Perfeccionista", "4254": "Especialista", "4253": "Especialista", "4252": "Especialista", "4251": "Especialista",
    "4247": "Objetivo", "4246": "Objetivo", "4245": "Objetivo", "4244": "Subactivo", "4243": "Subactivo", "4242": "Subactivo", "4241": "Subactivo",
    "4237": "Objetivo", "4236": "Objetivo", "4235": "Objetivo", "4234": "Subactivo", "4233": "Subactivo", "4232": "Subactivo", "4231": "Subactivo",
    "4227": "Objetivo", "4226": "Objetivo", "4225": "Objetivo", "4224": "Subactivo", "4223": "Subactivo", "4222": "Subactivo", "4221": "Subactivo",
    "4217": "Objetivo", "4216": "Objetivo", "4215": "Objetivo", "4214": "Subactivo", "4213": "Subactivo", "4212": "Subactivo", "4211": "Subactivo",
    "4177": "Perfeccionista", "4176": "Perfeccionista", "4175": "Perfeccionista", "4174": "Especialista", "4173": "Especialista", "4172": "Especialista", "4171": "Especialista",
    "4167": "Perfeccionista", "4166": "Perfeccionista", "4165": "Perfeccionista", "4164": "Especialista", "4163": "Especialista", "4162": "Especialista", "4161": "Especialista",
    "4157": "Perfeccionista", "4156": "Perfeccionista", "4155": "Perfeccionista", "4154": "Especialista", "4153": "Especialista", "4152": "Especialista", "4151": "Especialista",
    "4147": "Objetivo", "4146": "Objetivo", "4145": "Objetivo", "4144": "Subactivo", "4143": "Subactivo", "4142": "Subactivo", "4141": "Subactivo",
    "4137": "Objetivo", "4136": "Objetivo", "4135": "Objetivo", "4134": "Subactivo", "4133": "Subactivo", "4132": "Subactivo", "4131": "Subactivo",
    "4127": "Objetivo", "4126": "Objetivo", "4125": "Objetivo", "4124": "Subactivo", "4123": "Subactivo", "4122": "Subactivo", "4121": "Subactivo",
    "4117": "Objetivo", "4116": "Objetivo", "4115": "Objetivo", "4114": "Subactivo", "4113": "Subactivo", "4112": "Subactivo", "4111": "Subactivo",
    "3777": "Profesional", "3776": "Profesional", "3775": "Profesional", "3774": "Consejero", "3773": "Consejero", "3772": "Consejero", "3771": "Consejero",
    "3767": "Profesional", "3766": "Profesional", "3765": "Profesional", "3764": "Consejero", "3763": "Consejero", "3762": "Consejero", "3761": "Consejero",
    "3757": "Profesional", "3756": "Profesional", "3755": "Profesional", "3754": "Consejero", "3753": "Consejero", "3752": "Consejero", "3751": "Consejero",
    "3747": "Profesional", "3746": "Profesional", "3745": "Profesional", "3744": "Promotor", "3743": "Promotor", "3742": "Promotor", "3741": "Promotor",
    "3737": "Evaluador", "3736": "Evaluador", "3735": "Evaluador", "3734": "Promotor", "3733": "Promotor", "3732": "Promotor", "3731": "Promotor",
    "3727": "Evaluador", "3726": "Evaluador", "3725": "Evaluador", "3724": "Promotor", "3723": "Promotor", "3722": "Promotor", "3721": "Promotor",
    "3717": "Evaluador", "3716": "Evaluador", "3715": "Evaluador", "3714": "Promotor", "3713": "Promotor", "3712": "Promotor", "3711": "Promotor",
    "3677": "Profesional", "3676": "Profesional", "3675": "Profesional", "3674": "Agente", "3673": "Agente", "3672": "Agente", "3671": "Agente",
    "3667": "Profesional", "3666": "Profesional", "3665": "Profesional", "3664": "Consejero", "3663": "Consejero", "3662": "Consejero", "3661": "Consejero",
    "3657": "Profesional", "3656": "Profesional", "3655": "Profesional", "3654": "Consejero", "3653": "Consejero", "3652": "Consejero", "3651": "Consejero",
    "3647": "Profesional", "3646": "Profesional", "3645": "Profesional", "3644": "Promotor", "3643": "Promotor", "3642": "Promotor", "3641": "Promotor",
    "3637": "Evaluador", "3636": "Evaluador", "3635": "Evaluador", "3634": "Promotor", "3633": "Promotor", "3632": "Promotor", "3631": "Promotor",
    "3627": "Evaluador", "3626": "Evaluador", "3625": "Evaluador", "3624": "Promotor", "3623": "Promotor", "3622": "Promotor", "3621": "Promotor",
    "3617": "Evaluador", "3616": "Evaluador", "3615": "Evaluador", "3614": "Promotor", "3613": "Promotor", "3612": "Promotor", "3611": "Promotor",
    "3577": "Profesional", "3576": "Profesional", "3575": "Profesional", "3574": "Agente", "3573": "Agente", "3572": "Agente", "3571": "Agente",
    "3567": "Profesional", "3566": "Profesional", "3565": "Profesional", "3564": "Agente", "3563": "Agente", "3562": "Agente", "3561": "Agente",
    "3557": "Profesional", "3556": "Profesional", "3555": "Profesional", "3554": "Consejero", "3553": "Consejero", "3552": "Consejero", "3551": "Consejero",
    "3547": "Profesional", "3546": "Profesional", "3545": "Profesional", "3544": "Promotor", "3543": "Promotor", "3542": "Promotor", "3541": "Promotor",
    "3537": "Evaluador", "3536": "Evaluador", "3535": "Evaluador", "3534": "Promotor", "3533": "Promotor", "3532": "Promotor", "3531": "Promotor",
    "3527": "Evaluador", "3526": "Evaluador", "3525": "Evaluador", "3524": "Promotor", "3523": "Promotor", "3522": "Promotor", "3521": "Promotor",
    "3517": "Evaluador", "3516": "Evaluador", "3515": "Evaluador", "3514": "Promotor", "3513": "Promotor", "3512": "Promotor", "3511": "Promotor",
    "3477": "Perfeccionista", "3476": "Perfeccionista", "3475": "Perfeccionista", "3474": "Especialista", "3473": "Especialista", "3472": "Especialista", "3471": "Especialista",
    "3467": "Perfeccionista", "3466": "Perfeccionista", "3465": "Perfeccionista", "3464": "Especialista", "3463": "Especialista", "3462": "Especialista", "3461": "Especialista",
    "3457": "Perfeccionista", "3456": "Perfeccionista", "3455": "Perfeccionista", "3454": "Especialista", "3453": "Especialista", "3452": "Especialista", "3451": "Especialista",
    "3447": "Objetivo", "3446": "Objetivo", "3445": "Objetivo", "3444": "Desconcertante", "3443": "Desconcertante", "3442": "Subactivo", "3441": "Subactivo",
    "3437": "Objetivo", "3436": "Objetivo", "3435": "Objetivo", "3434": "Desconcertante", "3433": "Desconcertante", "3432": "Subactivo", "3431": "Subactivo",
    "3427": "Objetivo", "3426": "Objetivo", "3425": "Objetivo", "3424": "Subactivo", "3423": "Subactivo", "3422": "Subactivo", "3421": "Subactivo",
    "3417": "Objetivo", "3416": "Objetivo", "3415": "Objetivo", "3414": "Subactivo", "3413": "Subactivo", "3412": "Subactivo", "3411": "Subactivo",
    "3377": "Perfeccionista", "3376": "Perfeccionista", "3375": "Perfeccionista", "3374": "Especialista", "3373": "Especialista", "3372": "Especialista", "3371": "Especialista",
    "3367": "Perfeccionista", "3366": "Perfeccionista", "3365": "Perfeccionista", "3364": "Especialista", "3363": "Especialista", "3362": "Especialista", "3361": "Especialista",
    "3357": "Perfeccionista", "3356": "Perfeccionista", "3355": "Perfeccionista", "3354": "Especialista", "3353": "Especialista", "3352": "Especialista", "3351": "Especialista",
    "3347": "Objetivo", "3346": "Objetivo", "3345": "Objetivo", "3344": "Desconcertante", "3343": "Desconcertante", "3342": "Subactivo", "3341": "Subactivo",
    "3337": "Objetivo", "3336": "Objetivo", "3335": "Objetivo", "3334": "Desconcertante", "3333": "Subactivo", "3332": "Subactivo", "3331": "Subactivo",
    "3327": "Objetivo", "3326": "Objetivo", "3325": "Objetivo", "3324": "Subactivo", "3323": "Subactivo", "3322": "Subactivo", "3321": "Subactivo",
    "3317": "Objetivo", "3316": "Objetivo", "3315": "Objetivo", "3314": "Subactivo", "3313": "Subactivo", "3312": "Subactivo", "3311": "Subactivo",
    "3277": "Perfeccionista", "3276": "Perfeccionista", "3275": "Perfeccionista", "3274": "Especialista", "3273": "Especialista", "3272": "Especialista", "3271": "Especialista",
    "3267": "Perfeccionista", "3266": "Perfeccionista", "3265": "Perfeccionista", "3264": "Especialista", "3263": "Especialista", "3262": "Especialista", "3261": "Especialista",
    "3257": "Perfeccionista", "3256": "Perfeccionista", "3255": "Perfeccionista", "3254": "Especialista", "3253": "Especialista", "3252": "Especialista", "3251": "Especialista",
    "3247": "Objetivo", "3246": "Objetivo", "3245": "Objetivo", "3244": "Subactivo", "3243": "Subactivo", "3242": "Subactivo", "3241": "Subactivo",
    "3237": "Objetivo", "3236": "Objetivo", "3235": "Objetivo", "3234": "Subactivo", "3233": "Subactivo", "3232": "Subactivo", "3231": "Subactivo",
    "3227": "Objetivo", "3226": "Objetivo", "3225": "Objetivo", "3224": "Subactivo", "3223": "Subactivo", "3222": "Subactivo", "3221": "Subactivo",
    "3217": "Objetivo", "3216": "Objetivo", "3215": "Objetivo", "3214": "Subactivo", "3213": "Subactivo", "3212": "Subactivo", "3211": "Subactivo",
    "3177": "Perfeccionista", "3176": "Perfeccionista", "3175": "Perfeccionista", "3174": "Especialista", "3173": "Especialista", "3172": "Especialista", "3171": "Especialista",
    "3167": "Perfeccionista", "3166": "Perfeccionista", "3165": "Perfeccionista", "3164": "Especialista", "3163": "Especialista", "3162": "Especialista", "3161": "Especialista",
    "3157": "Perfeccionista", "3156": "Perfeccionista", "3155": "Perfeccionista", "3154": "Especialista", "3153": "Especialista", "3152": "Especialista", "3151": "Especialista",
    "3147": "Objetivo", "3146": "Objetivo", "3145": "Objetivo", "3144": "Subactivo", "3143": "Subactivo", "3142": "Subactivo", "3141": "Subactivo",
    "3137": "Objetivo", "3136": "Objetivo", "3135": "Objetivo", "3134": "Subactivo", "3133": "Subactivo", "3132": "Subactivo", "3131": "Subactivo",
    "3127": "Objetivo", "3126": "Objetivo", "3125": "Objetivo", "3124": "Subactivo", "3123": "Subactivo", "3122": "Subactivo", "3121": "Subactivo",
    "3117": "Objetivo", "3116": "Objetivo", "3115": "Objetivo", "3114": "Subactivo", "3113": "Subactivo", "3112": "Subactivo", "3111": "Subactivo",
    "2777": "Profesional", "2776": "Profesional", "2775": "Profesional", "2774": "Consejero", "2773": "Consejero", "2772": "Consejero", "2771": "Consejero",
    "2767": "Profesional", "2766": "Profesional", "2765": "Profesional", "2764": "Consejero", "2763": "Consejero", "2762": "Consejero", "2761": "Consejero",
    "2757": "Profesional", "2756": "Profesional", "2755": "Profesional", "2754": "Consejero", "2753": "Consejero", "2752": "Consejero", "2751": "Consejero",
    "2747": "Profesional", "2746": "Profesional", "2745": "Profesional", "2744": "Promotor", "2743": "Promotor", "2742": "Promotor", "2741": "Promotor",
    "2737": "Evaluador", "2736": "Evaluador", "2735": "Evaluador", "2734": "Promotor", "2733": "Promotor", "2732": "Promotor", "2731": "Promotor",
    "2727": "Evaluador", "2726": "Evaluador", "2725": "Evaluador", "2724": "Promotor", "2723": "Promotor", "2722": "Promotor", "2721": "Promotor",
    "2717": "Evaluador", "2716": "Evaluador", "2715": "Evaluador", "2714": "Promotor", "2713": "Promotor", "2712": "Promotor", "2711": "Promotor",
    "2677": "Profesional", "2676": "Profesional", "2675": "Profesional", "2674": "Agente", "2673": "Agente", "2672": "Agente", "2671": "Agente",
    "2667": "Profesional", "2666": "Profesional", "2665": "Profesional", "2664": "Consejero", "2663": "Consejero", "2662": "Consejero", "2661": "Consejero",
    "2657": "Profesional", "2656": "Profesional", "2655": "Profesional", "2654": "Consejero", "2653": "Consejero", "2652": "Consejero", "2651": "Consejero",
    "2647": "Profesional", "2646": "Profesional", "2645": "Profesional", "2644": "Promotor", "2643": "Promotor", "2642": "Promotor", "2641": "Promotor",
    "2637": "Evaluador", "2636": "Evaluador", "2635": "Evaluador", "2634": "Promotor", "2633": "Promotor", "2632": "Promotor", "2631": "Promotor",
    "2627": "Evaluador", "2626": "Evaluador", "2625": "Evaluador", "2624": "Promotor", "2623": "Promotor", "2622": "Promotor", "2621": "Promotor",
    "2617": "Evaluador", "2616": "Evaluador", "2615": "Evaluador", "2614": "Promotor", "2613": "Promotor", "2612": "Promotor", "2611": "Promotor",
    "2577": "Profesional", "2576": "Profesional", "2575": "Profesional", "2574": "Agente", "2573": "Agente", "2572": "Agente", "2571": "Agente",
    "2567": "Profesional", "2566": "Profesional", "2565": "Profesional", "2564": "Agente", "2563": "Agente", "2562": "Agente", "2561": "Agente",
    "2557": "Profesional", "2556": "Profesional", "2555": "Profesional", "2554": "Consejero", "2553": "Consejero", "2552": "Consejero", "2551": "Consejero",
    "2547": "Profesional", "2546": "Profesional", "2545": "Profesional", "2544": "Promotor", "2543": "Promotor", "2542": "Promotor", "2541": "Promotor",
    "2537": "Evaluador", "2536": "Evaluador", "2535": "Evaluador", "2534": "Promotor", "2533": "Promotor", "2532": "Promotor", "2531": "Promotor",
    "2527": "Evaluador", "2526": "Evaluador", "2525": "Evaluador", "2524": "Promotor", "2523": "Promotor", "2522": "Promotor", "2521": "Promotor",
    "2517": "Evaluador", "2516": "Evaluador", "2515": "Evaluador", "2514": "Promotor", "2513": "Promotor", "2512": "Promotor", "2511": "Promotor",
    "2477": "Perfeccionista", "2476": "Perfeccionista", "2475": "Perfeccionista", "2474": "Especialista", "2473": "Especialista", "2472": "Especialista", "2471": "Especialista",
    "2467": "Perfeccionista", "2466": "Perfeccionista", "2465": "Perfeccionista", "2464": "Especialista", "2463": "Especialista", "2462": "Especialista", "2461": "Especialista",
    "2457": "Perfeccionista", "2456": "Perfeccionista", "2455": "Perfeccionista", "2454": "Especialista", "2453": "Especialista", "2452": "Especialista", "2451": "Especialista",
    "2447": "Objetivo", "2446": "Objetivo", "2445": "Objetivo", "2444": "Subactivo", "2443": "Subactivo", "2442": "Subactivo", "2441": "Subactivo",
    "2437": "Objetivo", "2436": "Objetivo", "2435": "Objetivo", "2434": "Subactivo", "2433": "Subactivo", "2432": "Subactivo", "2431": "Subactivo",
    "2427": "Objetivo", "2426": "Objetivo", "2425": "Objetivo", "2424": "Subactivo", "2423": "Subactivo", "2422": "Subactivo", "2421": "Subactivo",
    "2417": "Objetivo", "2416": "Objetivo", "2415": "Objetivo", "2414": "Subactivo", "2413": "Subactivo", "2412": "Subactivo", "2411": "Subactivo",
    "2377": "Perfeccionista", "2376": "Perfeccionista", "2375": "Perfeccionista", "2374": "Especialista", "2373": "Especialista", "2372": "Especialista", "2371": "Especialista",
    "2367": "Perfeccionista", "2366": "Perfeccionista", "2365": "Perfeccionista", "2364": "Especialista", "2363": "Especialista", "2362": "Especialista", "2361": "Especialista",
    "2357": "Perfeccionista", "2356": "Perfeccionista", "2355": "Perfeccionista", "2354": "Especialista", "2353": "Especialista", "2352": "Especialista", "2351": "Especialista",
    "2347": "Objetivo", "2346": "Objetivo", "2345": "Objetivo", "2344": "Subactivo", "2343": "Subactivo", "2342": "Subactivo", "2341": "Subactivo",
    "2337": "Objetivo", "2336": "Objetivo", "2335": "Objetivo", "2334": "Subactivo", "2333": "Subactivo", "2332": "Subactivo", "2331": "Subactivo",
    "2327": "Objetivo", "2326": "Objetivo", "2325": "Objetivo", "2324": "Subactivo", "2323": "Subactivo", "2322": "Subactivo", "2321": "Subactivo",
    "2317": "Objetivo", "2316": "Objetivo", "2315": "Objetivo", "2314": "Subactivo", "2313": "Subactivo", "2312": "Subactivo", "2311": "Subactivo",
    "2277": "Perfeccionista", "2276": "Perfeccionista", "2275": "Perfeccionista", "2274": "Especialista", "2273": "Especialista", "2272": "Especialista", "2271": "Especialista",
    "2267": "Perfeccionista", "2266": "Perfeccionista", "2265": "Perfeccionista", "2264": "Especialista", "2263": "Especialista", "2262": "Especialista", "2261": "Especialista",
    "2257": "Perfeccionista", "2256": "Perfeccionista", "2255": "Perfeccionista", "2254": "Especialista", "2253": "Especialista", "2252": "Especialista", "2251": "Especialista",
    "2247": "Objetivo", "2246": "Objetivo", "2245": "Objetivo", "2244": "Subactivo", "2243": "Subactivo", "2242": "Subactivo", "2241": "Subactivo",
    "2237": "Objetivo", "2236": "Objetivo", "2235": "Objetivo", "2234": "Subactivo", "2233": "Subactivo", "2232": "Subactivo", "2231": "Subactivo",
    "2227": "Objetivo", "2226": "Objetivo", "2225": "Objetivo", "2224": "Subactivo", "2223": "Subactivo", "2222": "Subactivo", "2221": "Subactivo",
    "2217": "Objetivo", "2216": "Objetivo", "2215": "Objetivo", "2214": "Subactivo", "2213": "Subactivo", "2212": "Subactivo", "2211": "Subactivo",
    "2177": "Perfeccionista", "2176": "Perfeccionista", "2175": "Perfeccionista", "2174": "Especialista", "2173": "Especialista", "2172": "Especialista", "2171": "Especialista",
    "2167": "Perfeccionista", "2166": "Perfeccionista", "2165": "Perfeccionista", "2164": "Especialista", "2163": "Especialista", "2162": "Especialista", "2161": "Especialista",
    "2157": "Perfeccionista", "2156": "Perfeccionista", "2155": "Perfeccionista", "2154": "Especialista", "2153": "Especialista", "2152": "Especialista", "2151": "Especialista",
    "2147": "Objetivo", "2146": "Objetivo", "2145": "Objetivo", "2144": "Subactivo", "2143": "Subactivo", "2142": "Subactivo", "2141": "Subactivo",
    "2137": "Objetivo", "2136": "Objetivo", "2135": "Objetivo", "2134": "Subactivo", "2133": "Subactivo", "2132": "Subactivo", "2131": "Subactivo",
    "2127": "Objetivo", "2126": "Objetivo", "2125": "Objetivo", "2124": "Subactivo", "2123": "Subactivo", "2122": "Subactivo", "2121": "Subactivo",
    "2117": "Objetivo", "2116": "Objetivo", "2115": "Objetivo", "2114": "Subactivo", "2113": "Subactivo", "2112": "Subactivo", "2111": "Subactivo",
    "1777": "Profesional", "1776": "Profesional", "1775": "Profesional", "1774": "Consejero", "1773": "Consejero", "1772": "Consejero", "1771": "Consejero",
    "1767": "Profesional", "1766": "Profesional", "1765": "Profesional", "1764": "Consejero", "1763": "Consejero", "1762": "Consejero", "1761": "Consejero",
    "1757": "Profesional", "1756": "Profesional", "1755": "Profesional", "1754": "Consejero", "1753": "Consejero", "1752": "Consejero", "1751": "Consejero",
    "1747": "Profesional", "1746": "Profesional", "1745": "Profesional", "1744": "Promotor", "1743": "Promotor", "1742": "Promotor", "1741": "Promotor",
    "1737": "Evaluador", "1736": "Evaluador", "1735": "Evaluador", "1734": "Promotor", "1733": "Promotor", "1732": "Promotor", "1731": "Promotor",
    "1727": "Evaluador", "1726": "Evaluador", "1725": "Evaluador", "1724": "Promotor", "1723": "Promotor", "1722": "Promotor", "1721": "Promotor",
    "1717": "Evaluador", "1716": "Evaluador", "1715": "Evaluador", "1714": "Promotor", "1713": "Promotor", "1712": "Promotor", "1711": "Promotor",
    "1677": "Profesional", "1676": "Profesional", "1675": "Profesional", "1674": "Agente", "1673": "Agente", "1672": "Agente", "1671": "Agente",
    "1667": "Profesional", "1666": "Profesional", "1665": "Profesional", "1664": "Consejero", "1663": "Consejero", "1662": "Consejero", "1661": "Consejero",
    "1657": "Profesional", "1656": "Profesional", "1655": "Profesional", "1654": "Consejero", "1653": "Consejero", "1652": "Consejero", "1651": "Consejero",
    "1647": "Profesional", "1646": "Profesional", "1645": "Profesional", "1644": "Promotor", "1643": "Promotor", "1642": "Promotor", "1641": "Promotor",
    "1637": "Evaluador", "1636": "Evaluador", "1635": "Evaluador", "1634": "Promotor", "1633": "Promotor", "1632": "Promotor", "1631": "Promotor",
    "1627": "Evaluador", "1626": "Evaluador", "1625": "Evaluador", "1624": "Promotor", "1623": "Promotor", "1622": "Promotor", "1621": "Promotor",
    "1617": "Evaluador", "1616": "Evaluador", "1615": "Evaluador", "1614": "Promotor", "1613": "Promotor", "1612": "Promotor", "1611": "Promotor",
    "1577": "Profesional", "1576": "Profesional", "1575": "Profesional", "1574": "Agente", "1573": "Agente", "1572": "Agente", "1571": "Agente",
    "1567": "Profesional", "1566": "Profesional", "1565": "Profesional", "1564": "Agente", "1563": "Agente", "1562": "Agente", "1561": "Agente",
    "1557": "Profesional", "1556": "Profesional", "1555": "Profesional", "1554": "Consejero", "1553": "Consejero", "1552": "Consejero", "1551": "Consejero",
    "1547": "Profesional", "1546": "Profesional", "1545": "Profesional", "1544": "Promotor", "1543": "Promotor", "1542": "Promotor", "1541": "Promotor",
    "1537": "Evaluador", "1536": "Evaluador", "1535": "Evaluador", "1534": "Promotor", "1533": "Promotor", "1532": "Promotor", "1531": "Promotor",
    "1527": "Evaluador", "1526": "Evaluador", "1525": "Evaluador", "1524": "Promotor", "1523": "Promotor", "1522": "Promotor", "1521": "Promotor",
    "1517": "Evaluador", "1516": "Evaluador", "1515": "Evaluador", "1514": "Promotor", "1513": "Promotor", "1512": "Promotor", "1511": "Promotor",
    "1477": "Perfeccionista", "1476": "Perfeccionista", "1475": "Perfeccionista", "1474": "Especialista", "1473": "Especialista", "1472": "Especialista", "1471": "Especialista",
    "1467": "Perfeccionista", "1466": "Perfeccionista", "1465": "Perfeccionista", "1464": "Especialista", "1463": "Especialista", "1462": "Especialista", "1461": "Especialista",
    "1457": "Perfeccionista", "1456": "Perfeccionista", "1455": "Perfeccionista", "1454": "Especialista", "1453": "Especialista", "1452": "Especialista", "1451": "Especialista",
    "1447": "Objetivo", "1446": "Objetivo", "1445": "Objetivo", "1444": "Subactivo", "1443": "Subactivo", "1442": "Subactivo", "1441": "Subactivo",
    "1437": "Objetivo", "1436": "Objetivo", "1435": "Objetivo", "1434": "Subactivo", "1433": "Subactivo", "1432": "Subactivo", "1431": "Subactivo",
    "1427": "Objetivo", "1426": "Objetivo", "1425": "Objetivo", "1424": "Subactivo", "1423": "Subactivo", "1422": "Subactivo", "1421": "Subactivo",
    "1417": "Objetivo", "1416": "Objetivo", "1415": "Objetivo", "1414": "Subactivo", "1413": "Subactivo", "1412": "Subactivo", "1411": "Subactivo",
    "1377": "Perfeccionista", "1376": "Perfeccionista", "1375": "Perfeccionista", "1374": "Especialista", "1373": "Especialista", "1372": "Especialista", "1371": "Especialista",
    "1367": "Perfeccionista", "1366": "Perfeccionista", "1365": "Perfeccionista", "1364": "Especialista", "1363": "Especialista", "1362": "Especialista", "1361": "Especialista",
    "1357": "Perfeccionista", "1356": "Perfeccionista", "1355": "Perfeccionista", "1354": "Especialista", "1353": "Especialista", "1352": "Especialista", "1351": "Especialista",
    "1347": "Objetivo", "1346": "Objetivo", "1345": "Objetivo", "1344": "Subactivo", "1343": "Subactivo", "1342": "Subactivo", "1341": "Subactivo",
    "1337": "Objetivo", "1336": "Objetivo", "1335": "Objetivo", "1334": "Subactivo", "1333": "Subactivo", "1332": "Subactivo", "1331": "Subactivo",
    "1327": "Objetivo", "1326": "Objetivo", "1325": "Objetivo", "1324": "Subactivo", "1323": "Subactivo", "1322": "Subactivo", "1321": "Subactivo",
    "1317": "Objetivo", "1316": "Objetivo", "1315": "Objetivo", "1314": "Subactivo", "1313": "Subactivo", "1312": "Subactivo", "1311": "Subactivo",
    "1277": "Perfeccionista", "1276": "Perfeccionista", "1275": "Perfeccionista", "1274": "Especialista", "1273": "Especialista", "1272": "Especialista", "1271": "Especialista",
    "1267": "Perfeccionista", "1266": "Perfeccionista", "1265": "Perfeccionista", "1264": "Especialista", "1263": "Especialista", "1262": "Especialista", "1261": "Especialista",
    "1257": "Perfeccionista", "1256": "Perfeccionista", "1255": "Perfeccionista", "1254": "Especialista", "1253": "Especialista", "1252": "Especialista", "1251": "Especialista",
    "1247": "Objetivo", "1246": "Objetivo", "1245": "Objetivo", "1244": "Subactivo", "1243": "Subactivo", "1242": "Subactivo", "1241": "Subactivo",
    "1237": "Objetivo", "1236": "Objetivo", "1235": "Objetivo", "1234": "Subactivo", "1233": "Subactivo", "1232": "Subactivo", "1231": "Subactivo",
    "1227": "Objetivo", "1226": "Objetivo", "1225": "Objetivo", "1224": "Subactivo", "1223": "Subactivo", "1222": "Subactivo", "1221": "Subactivo",
    "1217": "Objetivo", "1216": "Objetivo", "1215": "Objetivo", "1214": "Subactivo", "1213": "Subactivo", "1212": "Subactivo", "1211": "Subactivo",
    "1177": "Perfeccionista", "1176": "Perfeccionista", "1175": "Perfeccionista", "1174": "Especialista", "1173": "Especialista", "1172": "Especialista", "1171": "Especialista",
    "1167": "Perfeccionista", "1166": "Perfeccionista", "1165": "Perfeccionista", "1164": "Especialista", "1163": "Especialista", "1162": "Especialista", "1161": "Especialista",
    "1157": "Perfeccionista", "1156": "Perfeccionista", "1155": "Perfeccionista", "1154": "Especialista", "1153": "Especialista", "1152": "Especialista", "1151": "Especialista",
    "1147": "Objetivo", "1146": "Objetivo", "1145": "Objetivo", "1144": "Subactivo", "1143": "Subactivo", "1142": "Subactivo", "1141": "Subactivo",
    "1137": "Objetivo", "1136": "Objetivo", "1135": "Objetivo", "1134": "Subactivo", "1133": "Subactivo", "1132": "Subactivo", "1131": "Subactivo",
    "1127": "Objetivo", "1126": "Objetivo", "1125": "Objetivo", "1124": "Subactivo", "1123": "Subactivo", "1122": "Subactivo", "1121": "Subactivo",
    "1117": "Objetivo", "1116": "Objetivo", "1115": "Objetivo", "1114": "Subactivo", "1113": "Subactivo", "1112": "Subactivo", "1111": "Subactivo"
}

# --- Diccionario con las descripciones detalladas de los perfiles (puedes completarlo o modificarlo) ---
DESCRIPCIONES_PERFILES = {
    "Alentador": {
        "Emociones": "Acepta la agresión, tiende a aparentar dar poca importancia a la necesidad que tiene de afecto.",
        "Meta": "Controlar su ambiente o a su público.",
        "Juzga a los demás por": "La forma en que proyecta su fuerza personal, carácter y posición social.",
        "Influye en los demás mediante": "Su encanto, dirección, intimidación , uso de recompensas.",
        "Su valor para la organización": "Mueve a la gente, inicia, ordena, felicita disciplina.",
        "Abusa de": "Su enfoque de que 'el fin justifica los medios'.",
        "Bajo presión": "Se vuelve manipulador, pendenciero, beligerante.",
        "Teme": "Ser demasiado blando, perder su posición social.",
        "Sería más eficaz si": "Fuera más genuina su sensibilidad; estuviera más dispuesto a ayudar a otros a tener éxito en su propio desarrollo personal.",
        "Observaciones Adicionales": "Las personas con patrón alentador saben con exactitud los resultados que quieren, pero no siempre los verbalizan de inmediato. Manifiestan cuáles son los resultados que quieren sólo después de que se haya creado un ambiente apropiado y la otra persona está dispuesta a aceptarlos. Por ejemplo, estas personas ofrecen amistad a quienes desean ser aceptados, más autoridad a quienes buscan poder y seguridad a quienes buscan un ambiente predecible.",
        "Obs 1": "El alentador pude ser encantador en su trato con los demás. Es persuasivo para obtener ayuda cuando se le presentan detalles repetitivos y que consumen mucho tiempo. Sin embargo, las personas a menudo experimentan ante ellos una sensación de conflicto, al sentirse por un lado atraídos, y curiosamente al mismo tiempo distanciados. Otras pueden sentirse 'utilizadas'. Aunque algunas veces el alentador inspira temor en los demás y rechaza sus decisiones, el Alentador suele ser apreciado por sus colaboradores. Esto lo consigue al usar siempre que le es posible su enorme capacidad de palabra para persuadir. El Alentador prefiere alcanzar sus objetivos no dominando a las personas sino haciendo de agente para realizar el trabajo.",
        "Obs 2": ""
    },
    "Realizador": {
        "Emociones": "Activo, diligente, muestra frustración.",
        "Meta": "Logros personales, en ocasiones a expensas de la meta de grupo.",
        "Juzga a los demás por": "El logro de resultados concretos.",
        "Influye en los demás mediante": "La aceptación de responsabilidad por su propio trabajo.",
        "Su valor para la organización": "Se propone y consigue resultados en áreas clave.",
        "Abusa de": "Confianza en si mismo, absorción en el trabajo.",
        "Bajo presión": "Se frustra e impacienta con los demás, se convierte en una persona que 'lo hace todo' en vez de ser alguien que delega.",
        "Teme": "A quienes tienen niveles inferiores o competitivos de trabajo, que afectan los resultados.",
        "Sería más eficaz si": "Dejara de pensar en 'esto o lo otro', estableciera su prioridades con mayor claridad y aceptara enfoques alternativos, estuviera dispuesto a sacrificar los beneficios a corto plazo por otros a largo plazo.",
        "Observaciones Adicionales": "La motivación del Patrón Realizador surge en gran parte de su interior y de metas personales muy profundas. Este compromiso previo con sus propias metas impide que acepte automáticamente las metas del grupo. El Realizador necesita combinar sus metas personales con las metas de la organización. Como el Realizador siempre ha ejercido control sobre los aspectos más importantes de su vida, desarrolla a menudo un fuerte sentido de la responsabilidad.",
        "Obs 1": "El Realizador demuestra un profundo interés por su trabajo y un continuo e intenso afán por conseguir lo que se propone. Tiene una alta opinión de su trabajo y suele realizar las cosas por él mismo para asegurarse de que todo esté bien hecho. Valora el trabajo arduo y bajo presión 'prefiere hacer' que delegar en otro. Cuando delega algo, suele volver ha realizarlo si no satisface sus expectativas. Su premisa dice: 'si tengo éxito, el mérito me corresponde, pero si fracaso, asumo la responsabilidad'.",
        "Obs 2": "Si el Realizador se comunica más con los demás dejaría de pensar en 'esto o lo otro', del 'yo mismo lo tengo que hacer' o 'quiero todo el crédito para mí'. Tal vez necesite ayuda para considerar otras propuestas y conseguir los resultados que desea. El Realizador sabe que funciona al máximo de su capacidad y espera un reconocimiento similar a su contribución, en ciertas organizaciones mediante ganancias elevadas y en otras con posiciones de mando."
    },
    "Perfeccionista": {
        "Emociones": "Competente para hacer bien las cosas, reservado, cauteloso.",
        "Meta": "Logros estables, predecible.",
        "Juzga a los demás por": "Normas precisas.",
        "Influye en los demás mediante": "La atención al detalle y precisión.",
        "Su valor para la organización": "Concienzudo, conserva las normas, control de calidad.",
        "Abusa de": "Los procedimientos y controles excesivos para evitar las fallas, depende demasiado de la gente, productos y procesos que le funcionaron en el pasado.",
        "Bajo presión": "Es discreto, diplomático.",
        "Teme": "El antagonismo.",
        "Sería más eficaz si": "Fuera más flexible en su papel, fuera más independiente e interdependiente, tuviera más fe en sí mismo y si se viera a sí mismo como una persona valiosa.",
        "Observaciones Adicionales": "El Perfeccionista es metódico y preciso en su forma de pensar y trabajar, por lo que suele seguir procedimientos ordenados tanto en su vida personal como laboral. Es extremadamente concienzudo y se esmera en el trabajo detallado y preciso. El Perfeccionista desea condiciones estables y actividades fáciles de predecir, por lo que se siente cómodo en un ambiente laboral claramente definido. Desea claridad respecto a lo que se espera de él en el trabajo, de cuánto tiempo dispone y cómo se va a evaluar su trabajo.",
        "Obs 1": "El perfeccionista se puede empantanar en los detalles cuando tiene que tomar decisiones. Sabe tomar decisiones importantes, pero se le puede criticar por el tiempo que le toma reunir y analizar la información antes de decidir. Aunque le agrada conocer la opinión de sus superiores, el Perfeccionista es capaz de arriesgarse cuando cuenta con datos que puede interpretar y usar para sacar conclusiones propias.",
        "Obs 2": "El Perfeccionista se evalúa y evalúa a los demás bajo normas precisas que aseguren resultados concretos y se adhiere a procedimientos operativos normales. Para la organización es valiosa esta atención concienzuda a las normas y calidad, sin embargo, el Perfeccionista tiende a definir su valor más por lo que hace que por lo que es como persona. Por lo tanto, suele reaccionar a los cumplidos personales con la idea de que: '¿Qué querrá esta persona?' , si aceptará un cumplido sincero por quien es, podría aumentar su confianza en sí mismo."
    },
    "Creativo": {
        "Emociones": "Acepta la agresión, puede contenerse al expresarse.",
        "Meta": "Dominar, logros únicos.",
        "Juzga a los demás por": "Sus propias normas, las ideas progresivas al llevar a cabo el trabajo.",
        "Influye en los demás mediante": "El establecimiento de un ritmo a seguir para desarrollar sistemas y enfoques innovadores.",
        "Su valor para la organización": "El iniciar o diseñar cambios.",
        "Abusa de": "La brusquedad, la actitud crítica o condescendiente.",
        "Bajo presión": "Se aburre fácilmente con el trabajo rutinario, cuando se le restringe se torna malhumorado, es independiente.",
        "Teme": "No poder influir, no alcanzar el nivel establecido.",
        "Sería más eficaz si": "Fuera más amable, usara más tacto al comunicarse, cooperara más con el equipo, reconociera que existen sanciones.",
        "Observaciones Adicionales": "Las personas con un Patrón Creativo muestran dos fuerzas opuestas en su comportamiento. El deseo de resultados tangibles se contrapone a un impulso de igual magnitud por la perfección. Su agresividad se templa con su sensibilidad. La rapidez de pensamiento y tiempo de reacción se ven frenados por el deseo de explorar todas las soluciones posibles antes de tomar una decisión.",
        "Obs 1": "Las personas creativas preveen de manera extraordinaria el enfoque que hay que dar a un proyecto y efectúan los cambios oportunos. En vista de que las personas con un Patrón Creativo son perfeccionistas y cuentan con una gran habilidad para planear, los cambios que efectúan suelen ser apropiados, aunque les pueda faltar atención a las relaciones interpersonales.",
        "Obs 2": "La persona creativa desea libertad para explorar y la autoridad para examinar y verificar los resultados. Puede tomar las decisiones diarias con rapidez, pero puede ser extremadamente cauteloso al tomar decisiones de verdadera importancia. '¿Debería aceptar este ascenso?', '¿debería mudarme a otro sitio?'. Por su necesidad de obtener resultados y perfección, la persona creativa no se preocupa mucho por las formas sociales. Puede parecer fría, ajena y brusca."
    },
    "Objetivo": {
        "Emociones": "Puede rechazar la agresión interpersonal.",
        "Meta": "La exactitud.",
        "Juzga a los demás por": "Su capacidad de pensamiento analítico.",
        "Influye en los demás mediante": "La información objetiva, los argumentos lógicos.",
        "Su valor para la organización": "Define, esclarece, obtiene información, evalúa, comprueba.",
        "Abusa de": "El análisis.",
        "Bajo presión": "Se vuelve aprensivo.",
        "Teme": "Actos irracionales, el ridículo.",
        "Sería más eficaz si": "Fuera más abierto, compartiera en público su perspicacia y opiniones.",
        "Observaciones Adicionales": "La capacidad de pensamiento crítico suele estar muy desarrollada en el Objetivo. Recalca la importancia de sacar conclusiones y basar las acciones en hechos. Busca la precisión y exactitud en todo lo que hace. Sin embargo, para llevar a cabo con eficiencia su trabajo, el Objetivo suele combinar la información intuitiva con los datos que posee. Cuando duda sobre el curso a tomar, evita hacer el ridículo preparándose meticulosamente. Por ejemplo, el Objetivo perfeccionará una nueva habilidad en privado antes de usarla en alguna actividad de grupo.",
        "Obs 1": "El Objetivo prefiere trabajar con personas que , como él, prefieren mantener un ambiente laboral tranquilo. Como puede mostrarse reticente en expresar sus sentimiento, hay quienes lo consideran tímido. Se siente particularmente incómodo ante personas agresivas. A pesar de esta apariencia templada, el Objetivo tiene un fuerte necesidad de controlar el ambiente. Suele ejercer este control en forma indirecta solicitando el apego a reglas y normas.",
        "Obs 2": "El Objetivo se preocupa por llegar a respuestas 'correctas' y le puede resultar difícil tomar decisiones en situaciones ambiguas. Su tendencia a preocuparse le puede llevar a una 'parálisis por análisis'. Con demasiada frecuencia, cuando comete un error, titubea en reconocerlo y se empreña en buscar información que le permita apoyar su postura."
    },
    "Persuasivo": {
        "Emociones": "Confía en los demás es entusiasta.",
        "Meta": "Autoridad y prestigio; diversos símbolos de prestigio.",
        "Juzga a los demás por": "Su capacidad de expresión verbal; su flexibilidad.",
        "Influye en los demás mediante": "Un comportamiento amistoso; franqueza; habilidad en su expresión verbal.",
        "Su valor para la organización": "Sabe vender y cerrar tratos; delega responsabilidades; sereno, seguridad en sí mismo.",
        "Abusa de": "Su entusiasmo; su habilidad para vender; su optimismo.",
        "Bajo presión": "Es discreto, diplomático.",
        "Teme": "Un ambiente inalterable; relaciones complejas.",
        "Sería más eficaz si": "Se le asignaran tareas que le impliquen un reto; prestara más atención al servicio y detalles elementales clave para el trabajo; hiciera un análisis objetivo de la información.",
        "Observaciones Adicionales": "El persuasivo trabaja con y a través de otros. Esto es, se esfuerza por hacer negocios en forma amistosa al mismo tiempo que pugna por alcanzar sus propios objetivos. El Persuasivo, al ser franco por naturaleza y mostrar interés por las personas, se gana el respeto y confianza de diversos tipos de personas. El Persuasivo tiene la capacidad de convencer a los demás de su punto de vista, no sólo los conquista, también los retiene como clientes o amigos. Esta habilidad les es particularmente útil para obtener puestos de autoridad al venderse a sí mismos y sus ideas.",
        "Obs 1": "El trabajo con gente, las tareas que le suponen un reto y la variedad de trabajos y actividades que impliquen movilidad , proporcionan un ambiente favorable para el Persuasivo. Además, suele buscar tareas laborales que le proporcionen oportunidades de quedar bien. Como resultado de su entusiasmo natural, el persuasivo tiende a ser demasiado optimista respecto a los resultados de los proyectos y el potencial de otras personas. El Persuasivo también suele sobreestimar su capacidad de cambiar el comportamiento de los demás.",
        "Obs 2": "Al mismo tiempo que rechaza las rutinas y reglamentos, el Persuasivo necesita que se le proporcione información analítica de manera sistemática y periódica. Cuando se le hace ver la importancia de los 'pequeños detalles', la información adecuada les ayuda a equilibrar su entusiasmo con una evaluación realista de la situación."
    },
    "Promotor": {
        "Emociones": "Dispuesto a aceptar a los demás.",
        "Meta": "Aprobación, popularidad.",
        "Juzga a los demás por": "Su forma de expresarse.",
        "Influye en los demás mediante": "Alabanzas, oportunidades, haciendo favores.",
        "Su valor para la organización": "Alivia tensiones; promueve proyectos y personas, incluso a sí mismo.",
        "Abusa de": "Los elogios, optimismo.",
        "Bajo presión": "Descuidado y sentimental; actúa en forma desorganizada; no sabe cómo llevar a cabo las cosas.",
        "Teme": "Perder aceptación social y su autoestima.",
        "Sería más eficaz si": "Tuviera más control del tiempo; fuera más objetivo; fuera más sensible a lo que significa 'urgente', controlara sus emociones; cumpliera hasta el final sus promesas, tareas.",
        "Observaciones Adicionales": "El promotor cuenta con una extensa red de contactos que le proporciona una base activa para realizar sus negocios. Gregario y sociable, le es fácil hacer amigos. Rara vez se opone intencionalmente a alguien. El promotor busca ambientes socialmente favorables donde pueda continuar desarrollando y conservando sus contactos. Con su excelente capacidad de palabra, promueve muy bien sus propias ideas y genera entusiasmo hacia proyectos ajenos. Gracias a su amplia esfera de contactos, el Promotor tiene acceso a las personas apropiadas cuando necesita ayuda.",
        "Obs 1": "En vista de que el promotor prefiere por naturaleza la interacción con otros y participa en actividades que implican contacto con gente, se interesa menos en la realización del trabajo. Aunque su trabajo imponga actividades solitarias, seguirá buscando situaciones que impliquen reuniones y vida social activa. Le agrada participar en reuniones, comités y conferencias.",
        "Obs 2": "Por su optimismo natural, el Promotor tiende a sobreestimar la capacidad de los demás. Suele llegar a conclusiones favorables sin haber considerado todos los hechos. Con entrenamiento y dirección adecuados se puede ayudar al Promotor a desarrollar objetividad y a dar la importancia debida a los resultados. Planear y controlar el tiempo le puede significar un reto. Le conviene limitar el tiempo dedicado a conversar y de esta manera recordarse a sí mismo la urgencia de 'concluir' y llevar a término una tarea."
    },
    "Consejero": {
        "Emociones": "Es fácil de abordar, afectuoso y comprensivo.",
        "Meta": "La amistad; la felicidad.",
        "Juzga a los demás por": "Su aceptación positiva; generalmente busca el lado bueno de las personas.",
        "Influye en los demás mediante": "Las relaciones personales, al practicar la política de 'puertas abiertas'.",
        "Su valor para la organización": "Estable, predecible; una amplia esfera de amistades; sabe escuchar.",
        "Abusa de": "Acercamiento indirecto, tolerancia.",
        "Bajo presión": "Se torna demasiado flexible e íntimo; confía demasiado en todos sin distinción.",
        "Teme": "Presionar a los demás; que se le acuse de hacer daño.",
        "Sería más eficaz si": "Presenta más atención a las fechas límite; tuviera más iniciativa para realizar el trabajo.",
        "Observaciones Adicionales": "El Consejero tiene el don particular de resolver los problemas de los demás. Impresiona con su afecto, empatía y comprensión. Al Consejero le es fácil encontrar lo bueno en las personas y asume una actitud optimista. El consejero prefiere tratar con la gente sobre la base de una relación íntima. Al saber escuchar, en especial a los problemas, es discreto en sus sugerencias y no trata de imponer sus ideas a los demás.",
        "Obs 1": "El Consejero suele ser en extremo tolerante y paciente con las personas que no rinden en el trabajo. Bajo presión, se le dificulta confrontar los problemas de desempeño en forma directa. Suele ser demasiado indirecto para ordenar, exigir o disciplinar a otros. Con su actitud de que la 'gente es importante', el Consejero suele dar menos importancia al rendimiento. En ocasiones requiere ayuda para fijar y cumplir fechas límites realistas.",
        "Obs 2": "A menudo, el Consejero toma la crítica como una afrenta personal, pero responde en forma positiva si recibe atención y cumplidos por un trabajo bien hecho. Cuando tiene un puesto de responsabilidad, suele prestar atención a la calidad de las condiciones de trabajo y proporcionar reconocimiento adecuado a los miembros de su equipo."
    },
    "Agente": {
        "Emociones": "Acepta el afecto; rechaza la agresión.",
        "Meta": "Ser aceptado por los demás.",
        "Juzga a los demás por": "La tolerancia y participación.",
        "Influye en los demás mediante": "La Comprensión; amistad.",
        "Su valor para la organización": "Apoya; armoniza; proyecta empatía; está orientado al servicio.",
        "Abusa de": "La amabilidad.",
        "Bajo presión": "Se vuelve persuasivo haciendo, si fuese necesario, uso de información que posee o de amistades clave.",
        "Teme": "El desacuerdo, el conflicto.",
        "Sería más eficaz si": "Tuviera más conciencia de quién es y de lo que puede hacer; mostrara más firmeza y agresividad; dijera 'no' en los momentos adecuados.",
        "Observaciones Adicionales": "Al Agente le interesa tanto las relaciones humanas como los variados aspectos del trabajo. Gracias a su empatía y tolerancia sabe escuchar y se le conoce por su buena disposición. El Agente hace que los demás sientan que se les quiere y necesita. No hay quien tema ser rechazado por un Agente. Es más, el agente ofrece amistad y está dispuesto a ayudar.",
        "Obs 1": "En cuanto al trabajo, el Agente cuenta con un excelente potencial para la organización y eficiente ejecución. Es excelente en hacer para otros lo que ellos encuentran difícil de realizar. El Agente busca por naturaleza la armonía y cooperación en el grupo.",
        "Obs 2": "Sin embargo, el Agente teme el conflicto y desacuerdo. Su tendencia a ayudar puede instar a otros a tolerar una situación en lugar de buscar una solución del problema. Además, la tendencia del Agente a adoptar un perfil 'bajo' en lugar de aceptar una confrontación franca con personas agresivas, lo que puede ser visto como una falta de 'dureza'. A pesar de todo, el Agente cuenta con un buen nivel de independencia aunque le preocupa su integración en el grupo."
    },
    "Evaluador": {
        "Emociones": "Un fuerte impulso por causar buena impresión.",
        "Meta": "'Ganar' con estilo.",
        "Juzga a los demás por": "Su capacidad de tomar iniciativa.",
        "Influye en los demás mediante": "Hacerles competir por su reconocimiento.",
        "Su valor para la organización": "Obtiene sus metas a través de los demás.",
        "Abusa de": "Su autoridad e ingenio.",
        "Bajo presión": "Se torna intranquilo; crítico; impaciente.",
        "Teme": "'Perder'; quedar mal ante los demás.",
        "Sería más eficaz si": "Llevara a cabo el seguimiento hasta el final; mostrara empatía al estar en desacuerdo; se marcara un ritmo más realista para sus actividades.",
        "Observaciones Adicionales": "El Evaluador toma las ideas creativas y las utiliza para fines prácticos. Es competitivo y usa métodos directos para conseguir resultados. Sin embargo, hay quienes consideran al Evaluador menos agresivo ya que suele mostrar consideración hacia los demás. En lugar de ordenar o mandar, el Evaluador involucra a las personas en el trabajo usando métodos persuasivos. Obtiene la cooperación de quienes le rodean al explicar la lógica de las actividades propuestas.",
        "Obs 1": "El Evaluador suele ser capaz de ayudar a los demás a visualizar los pasos necesarios para lograr resultados. Por lo general, habla de un plan de acción detallado que él mismo desarrollará para asegurar una progresión ordenada hacia los resultados. Sin embargo, en su afán de ganar, el Evaluador se puede impacientar cuando no se mantiene a los niveles establecidos o cuando se requiere mucho seguimiento.",
        "Obs 2": "El Evaluador tiene un pensamiento bastante analítico y es hábil para expresar en palabras sus críticas. Sus palabras pueden ser bastante hirientes. El Evaluador controla mejor la situación si se relaja y disminuye su ritmo de trabajo. Un axioma que le sería útil para lograrlo es: 'algunas veces se gana y otras se pierde'."
    },
    "Resolutivo": {
        "Emociones": "Individualista en lo que se refiere a sus necesidades personales.",
        "Meta": "Una nueva oportunidad; un nuevo reto.",
        "Juzga a los demás por": "Su capacidad para alcanzar las normas establecidas por él mismo.",
        "Influye en los demás mediante": "Las soluciones a los problemas; al proyectar una imagen de poder.",
        "Su valor para la organización": "Acepta la responsabilidad, no dice 'no es mi culpa'; ofrece formas nuevas e innovadoras de resolver problemas.",
        "Abusa de": "Del control que ejerce sobre los demás en su afán de alcanzar sus propios resultados.",
        "Bajo presión": "Se aparta cuando se tienen que hacer las cosas; se torna beligerante cuando ve su individualidad amenazada o se le cierran las puertas al reto.",
        "Teme": "Al aburrimiento; a la pérdida del control.",
        "Sería más eficaz si": "Mostrara más paciencia, empatía; participara y colaborara con los demás; diera más seguimiento y atención a la importancia del control de calidad.",
        "Observaciones Adicionales": "El Resolutivo suele ser una persona fuertemente individualista que busca continuamente nuevos horizontes. Como es extremadamente autosuficiente e independiente de pensamiento y acción, prefiere encontrar sus propias soluciones. Relativamente libre de la influencia restrictiva del grupo, el Resolutivo es capaz de eludir los convencionalismos y suele aportar soluciones innovadoras.",
        "Obs 1": "Aunque con bastante frecuencia tiende a ser directo y enérgico, el Resolutivo es asimismo astuto para manipular personas y situaciones. Sin embargo, cuando se requiere que el Resolutivo coopere con otros en situaciones que limitan su individualidad, el Resolutivo pude tornarse beligerante. Es sumamente persistente para conseguir los resultados que desea, y hace todo lo que está en sus manos para vencer los obstáculos que se le presentan. Además, sus expectativas respecto a los demás son altas y puede ser muy crítico cuando no se cumplen sus normas.",
        "Obs 2": "Al Resolutivo le interesa mucho alcanzar sus propias metas, así como tener oportunidades de progreso y retos. Como su empeño se enfoca tanto en el resultado final, suele carecer de empatía y parecer indiferente a las personas. Podría decir algo como: 'tómate una aspirina, yo estoy igual' o 'no seas niño, ya se te pasará'."
    },
    "Profesional": {
        "Emociones": "Quiere mantenerse a la altura de los demás en cuanto a esfuerzo y desempeño técnico.",
        "Meta": "Profundo afán por el desarrollo personal.",
        "Juzga a los demás por": "Su autodisciplina; sus posiciones y ascensos.",
        "Influye en los demás mediante": "La confianza en su habilidad para perfeccionar nuevos conocimientos; al desarrollar y seguir procedimientos y acciones 'correctos'.",
        "Su valor para la organización": "Hábil para resolver problemas técnicos y humanos; profesionalismo en su especialidad.",
        "Abusa de": "Una atención excesiva a objetivos personales; expectativas poco realistas sobre los demás.",
        "Bajo presión": "Se cohibe; sensible a la crítica.",
        "Teme": "Ser demasiado predecible; que no se le reconozca como 'experto'.",
        "Sería más eficaz si": "Colaborara en forma genuina para beneficio general; delegara tareas importantes a las personas apropiadas.",
        "Observaciones Adicionales": "El profesional valora la destreza en áreas especializadas. Su enorme deseo de 'destacar en algo', lo lleva a un esmerado control de su propio desempeño en el trabajo. Aunque su meta es ser 'el' experto en un área determinada, el Profesional da la impresión de saber un poco de todo. Esta imagen es más marcada cuando pone en palabras el conocimiento que posee sobre diversos temas.",
        "Obs 1": "En su relación con otros, el Profesional suele proyectar un estilo relajado, diplomático y afable. Esta actitud puede cambiar de súbito en su área de especialización cuando se concentra demasiado en alcanzar altos niveles de rendimiento. Al valorar la autodisciplina, el Profesional evalúa a los demás sobre la base de su autodisciplina, la que mide por su rendimiento diario. Sus expectativas en relación consigo mismo y con los demás son elevadas. Suele exteriorizar su desilusión.",
        "Obs 2": "Al mismo tiempo que su naturaleza le pide concentrarse en desarrollar una propuesta organizada del trabajo y en aumentar sus propias capacidades, El Profesional necesita asimismo ayudar a otros a perfeccionar sus talentos. Además, necesita saber apreciar mejor a quienes contribuyen en el esfuerzo del trabajo, aunque no usen lo que el Profesional considera el 'método correcto'."
    },
    "Investigador": {
        "Emociones": "Desapasionado; autodisciplinado.",
        "Meta": "El poder que generan la autoridad, la posición y los roles formales.",
        "Juzga a los demás por": "El uso de la información objetiva.",
        "Influye en los demás mediante": "Su determinación; su tenacidad.",
        "Su valor para la organización": "Seguimiento concienzudo para realizar su trabajo en forma constante y persistente sea individual o en grupos pequeños.",
        "Abusa de": "La franqueza; su desconfianza hacia los demás.",
        "Bajo presión": "Tiende a interiorizar los conflictos; recuerda el mal que se le ha hecho.",
        "Teme": "Involucrarse con las masas; vender ideas abstractas.",
        "Sería más eficaz si": "Fuera más flexible; aceptara a los demás; si participara más con los demás.",
        "Observaciones Adicionales": "Objetivo y analítico, el investigador, está 'enclavado en la realidad'. Por lo general reservado, sigue con calma y firmeza un camino independiente hacia la meta establecida. El Investigador tiene éxito en muchas cosas, no por su versatilidad sino por la tenaz determinación de llegar hasta el final. Busca un claro propósito o meta sobre el que puede desarrollar un plan ordenado y organizar sus acciones. Una vez embarcado en un proyecto, el Investigador lucha con tenacidad por alcanzar sus objetivos. En ocasiones es necesario intervenir para que cambie de parecer. Puede ser visto por otros como terco y obstinado.",
        "Obs 1": "El investigador se desempeña de maravilla en tareas de naturaleza técnica que le impliquen un reto, donde pueda usar e interpretar información real y sacar conclusiones. Responde a la lógica más que a la emoción. Al vender o comercializar una idea, puede lograr gran éxito si su producto es concreto.",
        "Obs 2": "El Investigador prefiere trabajar solo y no se interesa en agradar a los demás. Se le puede considerar sumamente directo, brusco y sin tacto. Al valorar su propia capacidad de pensamiento, el Investigador evalúa a los demás por su objetividad y lógica. Para mejorar la efectividad de sus relaciones con las personas necesita desarrollar una mayor comprensión de los demás, incluso de sus emociones."
    },
    "Especialista": {
        "Emociones": "Moderación calculada; afán de servir, de adaptarse a los demás.",
        "Meta": "Conservar el 'status quo', controlar el ambiente.",
        "Juzga a los demás por": "Las normas de amistad, después por su capacidad.",
        "Influye en los demás mediante": "Su constancia en el desempeño; por su afán de servir, de adaptarse a las necesidades de los demás.",
        "Su valor para la organización": "Planifica a corto plazo; es predecible, es congruente; mantiene un ritmo uniforme y seguro.",
        "Abusa de": "La modestia; su miedo a correr riesgos; su resistencia pasiva hacia las innovaciones.",
        "Bajo presión": "Se adapta a quienes tienen autoridad y a lo que opina el grupo.",
        "Teme": "Los cambios; la desorganización.",
        "Sería más eficaz si": "Compartiera más sus ideas; aumentara su confianza en sí mismo basándose en la retroalimentación que recibe; utilizara métodos más sencillos y directos.",
        "Observaciones Adicionales": "El Especialista se 'lleva bien' con los demás. Por su actitud moderada y controlada y por su comportamiento modesto, puede trabajar en armonía con diversos estilos de conducta. El Especialista es considerado paciente y siempre está dispuesto a ayudar a quienes considera sus amigos. De hecho, tiende a desarrollar en el trabajo una estrecha relación con un grupo relativamente reducido de compañeros.",
        "Obs 1": "Se esfuerza por conservar pautas de comportamiento conocidos y predecibles. El Especialista, al ser bastante eficiente en áreas especializadas, planea su trabajo, lo enfoca de manera clara y directa y consigue una notoria constancia en su desempeño. El reconocimiento que recibe de los demás le ayuda a conservar este nivel.",
        "Obs 2": "El Especialista es lento para adaptarse a los cambios. Una preparación previa le concede el tiempo que requiere para cambiar sus procedimientos y conservar su nivel de rendimiento. El Especialista puede necesitar ayuda al inicio de un nuevo proyecto y para desarrollar métodos prácticos y sencillos para cubrir plazos establecidos. Suele dejar a un lado los proyectos terminados para posteriormente concluirlos. Un pequeño consejo: ¡tire algunas de esas carpetas viejas de su archivo!."
    },
    # Perfiles que faltaban en la lista de descripciones
    "Superactivo": {}, "Desconcertante": {}, "Subactivo": {}
}


# --- Funciones para evaluar los resultados ---
def get_code_for_score(score):
    if score <= -8: return "1"
    if -7 <= score <= -4: return "2"
    if -3 <= score <= -1: return "3"
    if 0 <= score <= 1: return "4"
    if 2 <= score <= 4: return "5"
    if 5 <= score <= 8: return "6"
    return "7" # >= 9

def evaluate_disc(resultados_raw):
    mas_letras = [v[0] for v in resultados_raw.values()]
    menos_letras = [v[1] for v in resultados_raw.values()]
    
    mas_counts = Counter(mas_letras)
    menos_counts = Counter(menos_letras)
    
    net_d = mas_counts.get('D', 0) - menos_counts.get('D', 0)
    net_i = mas_counts.get('I', 0) - menos_counts.get('I', 0)
    net_s = mas_counts.get('S', 0) - menos_counts.get('S', 0)
    net_c = mas_counts.get('C', 0) - menos_counts.get('C', 0)
    
    code_d = get_code_for_score(net_d)
    code_i = get_code_for_score(net_i)
    code_s = get_code_for_score(net_s)
    code_c = get_code_for_score(net_c)
    
    final_code = f"{code_d}{code_i}{code_s}{code_c}"
    profile_name = PERFILES_DISC.get(final_code, "Perfil no definido")
    profile_details = DESCRIPCIONES_PERFILES.get(profile_name, {})
    
    return {
        "raw_results": resultados_raw, # <-- Se necesita para el PDF
        "net_scores": {"D": net_d, "I": net_i, "S": net_s, "C": net_c},
        "profile_code": final_code,
        "profile_name": profile_name, # <-- Se guardará en DB
        "profile_details": profile_details # <-- Se necesita para el PDF
    }

def crear_interfaz_disc(supabase: Client):
    st.components.v1.html("<script>window.top.scrollTo(0, 0);</script>", height=0)
    st.title("Test de Comportamiento (DISC)")
    st.markdown("---")
    st.info(
        """
        **Instrucciones:** En cada uno de los 28 grupos a continuación, seleccione la cualidad que **MÁS** lo describe y la cualidad que **MENOS** lo describe.
        Debe realizar una selección en la fila "Más" y una en la fila "Menos" para cada grupo, y no pueden ser la misma cualidad. Cada grupo de opciones debe
        ser respondido, es decir, este test debe ser completado en su totalidad para poder avanzar.
        """
    )

    with st.form(key="disc_form"):
        # --- Nuevo Checkbox de Consentimiento ---
        st.markdown("---")
        comprende = st.checkbox("Sí, comprendo las instrucciones.", key="comprende_disc")
        st.markdown("---")
        respuestas = {}
        for i in range(1, 29):
            st.markdown(f"---")
            st.write(f"**Grupo {i}**")
            
            # Asegurarse que GRUPOS_DISC esté definido
            if not GRUPOS_DISC:
                st.error("Error: Diccionario GRUPOS_DISC no definido.")
                return
            
            cualidades = list(GRUPOS_DISC.get(i, {}).keys())
            if not cualidades:
                st.error(f"Error: No se encontraron cualidades para el Grupo {i}.")
                continue # Saltar a la siguiente iteración si faltan datos
                
            respuestas[f"grupo_{i}_mas"] = st.radio(
                f"Me identifico **más** con:",
                options=cualidades,
                key=f"mas_{i}",
                horizontal=True,
                index=None
            )

            respuestas[f"grupo_{i}_menos"] = st.radio(
                f"Me identifico **menos** con:",
                options=cualidades,
                key=f"menos_{i}",
                horizontal=True,
                index=None
            )

        siguiente_button = st.form_submit_button("Siguiente")

        if siguiente_button:
            if 'ficha_id' not in st.session_state:
                st.error("Error crítico: No se encontró el ID de la ficha de ingreso. Por favor, vuelva a empezar.")
                return
            
            # --- Validación del Checkbox ---
            if not comprende:
                st.warning("Debe marcar la casilla indicando que comprende las instrucciones para continuar.")
                return

            resultados_raw = {}
            errores = []

            for i in range(1, 29):
                mas_seleccion = respuestas.get(f"grupo_{i}_mas")
                menos_seleccion = respuestas.get(f"grupo_{i}_menos")
                grupo_actual = GRUPOS_DISC.get(i, {})

                if not mas_seleccion or not menos_seleccion:
                    errores.append(f"Grupo {i}")
                elif mas_seleccion == menos_seleccion:
                    errores.append(f"Grupo {i} (la selección 'Más' y 'Menos' no puede ser la misma)")
                elif not grupo_actual:
                     errores.append(f"Grupo {i} (datos de cualidades no encontrados)")
                else:
                    letra_mas = grupo_actual.get(mas_seleccion)
                    letra_menos = grupo_actual.get(menos_seleccion)
                    if letra_mas is None or letra_menos is None:
                         errores.append(f"Grupo {i} (error interno al obtener letras)")
                    else:
                      # Guardamos las respuestas como un array de dos strings
                      resultados_raw[f"grupo_{i}"] = [letra_mas, letra_menos]

            if errores:
                st.error("Por favor, complete o corrija su selección para los siguientes grupos: " + ", ".join(errores))
            else:
                with st.spinner("Guardando respuestas..."):
                    # 1. Calcular resultados
                    resultados_evaluados = evaluate_disc(resultados_raw)
                    
                    # 2. Guardar resultados evaluados en session_state para el PDF
                    if 'form_data' not in st.session_state:
                        st.session_state.form_data = {}
                    resultados_evaluados['comprende'] = comprende
                    st.session_state.form_data['test_disc'] = resultados_evaluados

                    # 3. Preparar datos para Supabase (formato de respuestas brutas + perfil)
                    disc_data_to_save = resultados_raw.copy() # <-- Se guardan las respuestas grupo_X: [letra, letra]
                    disc_data_to_save['id'] = st.session_state.ficha_id
                    disc_data_to_save['perfil_personalidad'] = resultados_evaluados['profile_name'] # <-- Se añade el perfil calculado
                    disc_data_to_save['comprende'] = comprende  # <-- Guardar en la base de datos

                    # 4. Enviar a Supabase
                    try:
                        response = supabase.from_('test_disc').insert(disc_data_to_save).execute()
                        if response.data:
                            if 'current_test_index' not in st.session_state:
                                st.session_state.current_test_index = 0
                            st.session_state.current_test_index += 1
                            st.rerun()
                        else:
                            st.error(f"Error al guardar los resultados del test DISC: {response.error.message if response.error else 'Error desconocido.'}")

                    except Exception as e:
                        st.error(f"Ocurrió una excepción al intentar guardar los resultados del test DISC: {e}")



