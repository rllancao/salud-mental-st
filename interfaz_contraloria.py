import streamlit as st
from supabase import Client
import io
import pymysql
import json
import pandas as pd
from datetime import datetime, date, timedelta
import plotly.graph_objects as go

BUCKET_NAME = "ficha_ingreso_SM_bucket"
# Solo interesan estos tests para Contraloría
TESTS_CONTRALORIA = ["EPWORTH", "EPQ-R"]
# Lista completa necesaria para parsear correctamente agenda MySQL
ALL_TESTS = [
    "EPWORTH", "DISC", "WONDERLIC", "ALERTA", "BARRATT", 
    "PBLL", "16 PF", "KOSTICK", "PSQI", "D-48", "WESTERN", "EPQ-R"
]

# --- Conexión MySQL (Reutilizable) ---
@st.cache_resource
def connect_to_mysql():
    try:
        return pymysql.connect(
            host=st.secrets["mysql"]["host"], user=st.secrets["mysql"]["user"],
            password=st.secrets["mysql"]["password"], database=st.secrets["mysql"]["database"],
            port=st.secrets["mysql"]["port"]
        )
    except Exception as e:
        st.error(f"Error conexión MySQL: {e}")
        return None

# --- Obtener Pacientes Filtrados para Contraloría ---
@st.cache_data(ttl=300)
def fetch_pacientes_contraloria(sede, _supabase: Client):
    conn = connect_to_mysql()
    if not conn: return []
    
    # 1. Buscar en Agenda (MySQL)
    sede_b = "CENTRO DE SALUD WORKMED SANTIAGO" if "SANTIAGO" in sede else sede
    
    # Traemos todos los que tengan prestaciones, luego filtramos en Python
    query = "SELECT datosPersona, prestacionesSalud FROM `agendaViewPrest` WHERE fecha = CURDATE() AND nombre_lab LIKE %s AND prestacionesSalud IS NOT NULL"
    
    pacientes_filtrados = []
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, (f"%{sede_b}%",))
            results = cursor.fetchall()
        
        # 2. Obtener Asignaciones Manuales del día (Supabase) para cruzar
        today_str = date.today().isoformat()
        
        # Manuales (Tabla nueva)
        manuales_res = _supabase.from_('asignaciones_manuales').select('rut, tests_asignados').gte('created_at', f'{today_str}T00:00:00').execute()
        mapa_manuales = {m['rut']: m['tests_asignados'] for m in manuales_res.data} if manuales_res.data else {}
        
        # Aeronáutica (Tabla original)
        aero_res = _supabase.from_('asignaciones_aeronautica').select('rut, tests_asignados').gte('created_at', f'{today_str}T00:00:00').execute()
        mapa_aero = {a['rut']: a['tests_asignados'] for a in aero_res.data} if aero_res.data else {}

        for row in results:
            try:
                d = json.loads(row[0])
                rut = d.get('rut')
                nombre = " ".join(filter(None, [d.get('nombre','').strip(), d.get('nombre2','').strip(), d.get('apellidoP','').strip(), d.get('apellidoM','').strip()]))
                
                # Determinar Tests Finales (Prioridad: Manual > Aero > Agenda)
                tests_finales = []
                
                if rut in mapa_manuales:
                    tests_finales = mapa_manuales[rut]
                elif rut in mapa_aero:
                    tests_finales = mapa_aero[rut]
                else:
                    # Parsear Agenda
                    prest_str = row[1] or ""
                    if prest_str:
                        try:
                            l = json.loads(prest_str)
                            for p in l:
                                for t in ALL_TESTS:
                                    if t in p.upper() and t not in tests_finales: 
                                        tests_finales.append(t)
                        except: pass
                
                # FILTRO CRÍTICO: Solo incluir si tiene EPWORTH o EPQ-R
                # Intersección entre los asignados y los de interés
                tests_relevantes = [t for t in tests_finales if t in TESTS_CONTRALORIA]
                
                if tests_relevantes:
                    pacientes_filtrados.append({
                        "rut": rut,
                        "nombre": nombre,
                        "tests_relevantes": tests_relevantes # Solo guardamos estos para mostrar
                    })
            except: continue
            
    except Exception as e:
        st.error(f"Error procesando datos: {e}")
        
    return pacientes_filtrados

# --- Obtener Progreso Específico ---
@st.cache_data(ttl=60)
def fetch_progreso_contraloria(_supabase: Client, ruts: list):
    progreso = {r: [] for r in ruts}
    if not ruts: return progreso
    try:
        # Obtener IDs de fichas de hoy
        today = datetime.now(); start = today.strftime('%Y-%m-%d 00:00:00'); end = (today + timedelta(days=1)).strftime('%Y-%m-%d 00:00:00')
        
        res = _supabase.from_('ficha_ingreso').select('id, rut').in_('rut', ruts).gte('created_at', start).lt('created_at', end).execute()
        if not res.data: return progreso
        
        id_map = {i['id']: i['rut'] for i in res.data}
        ids = list(id_map.keys())
        
        # Solo consultar tablas de interés
        tablas_map = {"EPWORTH": "test_epworth", "EPQ-R": "test_epq_r"}
        
        for nombre_test, tabla in tablas_map.items():
            r_test = _supabase.from_(tabla).select('id').in_('id', ids).execute()
            if r_test.data:
                for item in r_test.data:
                    rut = id_map.get(item['id'])
                    if rut: progreso[rut].append(nombre_test)
    except Exception as e:
        st.error(f"Error fetch progreso: {e}")
    return progreso

def crear_interfaz_contraloria(supabase: Client):
    st.title("Panel de Contraloría")
    
    tab1, tab2 = st.tabs(["Búsqueda de Informes", "Estado Diario (Epworth/EPQ-R)"])

    # --- Pestaña 1: Búsqueda Original ---
    with tab1:
        st.header("Búsqueda de Informes")
        st.write("Ingrese el RUT del paciente para buscar informes específicos (Epworth, EPQ-R).")
        rut_busqueda = st.text_input("RUT del Paciente", placeholder="Ej. 12345678-9", key="rut_contraloria")

        if st.button("Buscar Informes", key="btn_buscar_contraloria"):
            if not rut_busqueda:
                st.warning("Por favor, ingrese un RUT.")
            else:
                with st.spinner("Buscando informes..."):
                    try:
                        ids_response = supabase.from_('ficha_ingreso').select('id, nombre_completo').eq('rut', rut_busqueda).execute()
                        
                        if not ids_response.data:
                            st.warning(f"No se encontró paciente con RUT: {rut_busqueda}")
                        else:
                            fichas_ids = [i['id'] for i in ids_response.data]
                            nombre = ids_response.data[0]['nombre_completo']
                            paths = set()
                            
                            # Solo buscar en tablas de interés
                            for t in ["test_epworth", "test_epq_r"]:
                                res = supabase.from_(t).select('pdf_path').in_('id', fichas_ids).execute()
                                if res.data:
                                    for item in res.data:
                                        if item.get('pdf_path'): paths.add(item['pdf_path'])
                            
                            if paths:
                                st.success(f"Informes encontrados para {nombre}")
                                for path in paths:
                                    name = path.split("/")[-1]
                                    try:
                                        data = supabase.storage.from_(BUCKET_NAME).download(path)
                                        st.download_button(f"Descargar {name}", data, name, "application/pdf", key=f"dl_{path}")
                                    except: st.error(f"Error descargando {name}")
                            else:
                                st.info("No hay informes de Epworth o EPQ-R disponibles para este paciente.")

                    except Exception as e:
                        st.error(f"Error: {e}")

    # --- Pestaña 2: Estado Diario ---
    with tab2:
        st.header("Estado Diario - Tests de Sueño y Personalidad")
        st.write("Monitoreo de pacientes agendados hoy que requieren Epworth o EPQ-R.")
        
        user_sedes = st.session_state.get("user_sedes", [])
        if not user_sedes:
            st.error("Sin sedes asignadas.")
        else:
            sede = user_sedes[0]
            if len(user_sedes) > 1: sede = st.selectbox("Sede", user_sedes, key="sede_contraloria_diario")
            
            if st.button("🔄 Actualizar Tabla", key="refresh_contraloria"):
                st.cache_data.clear()
                st.rerun()
            
            with st.spinner("Cargando datos de agenda y progreso..."):
                # 1. Traer pacientes filtrados (Solo los que tienen EPWORTH o EPQ-R)
                pacientes = fetch_pacientes_contraloria(sede, supabase)
                
                # 2. Traer progreso de esos pacientes
                progreso = fetch_progreso_contraloria(supabase, [p['rut'] for p in pacientes])
            
            if not pacientes:
                st.info("No hay pacientes con estos tests agendados para hoy en esta sede.")
            else:
                # Construir filas
                rows = []
                stats = {"Pendiente": 0, "En Progreso": 0, "Finalizado": 0}
                
                for p in pacientes:
                    rut = p['rut']
                    asignados = set(p['tests_relevantes'])
                    completados = set(progreso.get(rut, []))
                    
                    # Lógica de estado simplificada para estos 2 tests
                    # Si completó todos los relevantes -> Finalizado
                    # Si completó alguno pero faltan -> En Progreso
                    # Si no completó ninguno -> Pendiente
                    
                    matches = len(asignados.intersection(completados))
                    total = len(asignados)
                    
                    estado = "🟡 Pendiente"
                    if matches == total and total > 0:
                        estado = "✅ Finalizado"
                        stats["Finalizado"] += 1
                    elif matches > 0:
                        estado = "🔵 En Progreso"
                        stats["En Progreso"] += 1
                    else:
                        stats["Pendiente"] += 1
                    
                    detalle = [f"{'✅' if t in completados else '⏳'} {t}" for t in sorted(list(asignados))]
                    
                    rows.append({
                        "RUT": rut,
                        "Nombre": p['nombre'],
                        "Estado": estado,
                        "Tests Requeridos": ", ".join(detalle)
                    })
                
                # Métricas visuales
                c1, c2, c3 = st.columns(3)
                c1.metric("Pendientes", stats["Pendiente"])
                c2.metric("En Progreso", stats["En Progreso"])
                c3.metric("Finalizados", stats["Finalizado"])

                st.divider()
                
                # Filtros
                filtro = st.radio("Filtrar:", ["Todos", "Pendientes", "Finalizados"], horizontal=True, key="filtro_contraloria")
                
                df = pd.DataFrame(rows)
                if filtro == "Pendientes":
                    df = df[df["Estado"].str.contains("Pendiente|Progreso")]
                elif filtro == "Finalizados":
                    df = df[df["Estado"].str.contains("Finalizado")]
                
                st.dataframe(df, use_container_width=True)