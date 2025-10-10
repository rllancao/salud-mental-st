import streamlit as st
from supabase import Client
import io

BUCKET_NAME = "ficha_ingreso_SM_bucket"

def crear_interfaz_psicologo(supabase: Client):
    st.title("Búsqueda y Descarga de Informes de Pacientes")
    st.write("Ingrese el RUT del paciente para buscar todos sus informes de salud mental asociados.")

    rut_busqueda = st.text_input("RUT del Paciente", placeholder="Ej. 12345678-9")

    if st.button("Buscar Informes"):
        if not rut_busqueda:
            st.warning("Por favor, ingrese un RUT para buscar.")
            return

        with st.spinner("Buscando todos los informes del paciente..."):
            try:
                todos_los_paths = set() # Usamos un 'set' para evitar duplicados automáticamente
                nombre_paciente = ""

                # 1. Buscar en 'registros_fichas_sm'
                fichas_response = supabase.from_('registros_fichas_sm').select('nombre_completo, pdf_path').eq('rut', rut_busqueda).execute()
                if fichas_response.data:
                    if not nombre_paciente:
                        nombre_paciente = fichas_response.data[0]['nombre_completo']
                    for ficha in fichas_response.data:
                        if ficha.get('pdf_path'):
                            todos_los_paths.add(ficha['pdf_path'])

                # 2. Buscar en 'test_epworth'
                ids_response = supabase.from_('ficha_ingreso').select('id').eq('rut', rut_busqueda).execute()
                if ids_response.data:
                    fichas_ids = [item['id'] for item in ids_response.data]
                    epworth_response = supabase.from_('test_epworth').select('pdf_path').in_('id', fichas_ids).execute()
                    if epworth_response.data:
                        for test in epworth_response.data:
                            if test.get('pdf_path'):
                                todos_los_paths.add(test['pdf_path'])
                
                # (Aquí se agregarían búsquedas en otras tablas de tests)

                # 3. Procesar y mostrar los informes únicos
                if todos_los_paths:
                    st.success(f"Se encontraron {len(todos_los_paths)} informes únicos para el paciente: {nombre_paciente}")
                    st.markdown("---")

                    for path in todos_los_paths:
                        nombre_archivo = path.split('/')[-1]
                        
                        # Identificar el tipo de informe por el nombre del archivo
                        tipo_informe = "Informe Desconocido"
                        if "FichaIngreso" in nombre_archivo:
                            tipo_informe = "Informe de Ficha de Ingreso"
                        elif "Epworth" in nombre_archivo:
                            tipo_informe = "Informe de Test de Epworth"
                        
                        st.subheader(f"📄 {tipo_informe}")
                        st.write(f"Nombre del archivo: `{nombre_archivo}`")

                        try:
                            res = supabase.storage.from_(BUCKET_NAME).download(path=path)
                            pdf_bytes = io.BytesIO(res)

                            st.download_button(
                                label=f"Descargar {tipo_informe}",
                                data=pdf_bytes,
                                file_name=nombre_archivo,
                                mime="application/pdf",
                                key=path # El path ahora es garantizadamente único
                            )
                            st.markdown("---")
                        except Exception as download_error:
                            st.error(f"No se pudo descargar el archivo '{nombre_archivo}': {download_error}")

                else:
                    st.warning(f"No se encontró ningún informe para el RUT: {rut_busqueda}")

            except Exception as db_error:
                st.error(f"Error al consultar la base de datos: {db_error}")

