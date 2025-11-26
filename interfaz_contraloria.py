import streamlit as st
from supabase import Client
import io

BUCKET_NAME = "ficha_ingreso_SM_bucket"

def crear_interfaz_contraloria(supabase: Client):
    st.title("Búsqueda de Informes de Tests")
    st.write("Ingrese el RUT del paciente para buscar los informes de los tests EPWORTH y EPQ-R.")

    rut_busqueda = st.text_input("RUT del Paciente", placeholder="Ej. 12345678-9")

    if st.button("Buscar Informes"):
        if not rut_busqueda:
            st.warning("Por favor, ingrese un RUT para buscar.")
            return

        with st.spinner("Buscando informes..."):
            try:
                # Primero, necesitamos los IDs de las fichas asociadas a ese RUT
                ids_response = supabase.from_('ficha_ingreso').select('id, nombre_completo').eq('rut', rut_busqueda).execute()
                
                if not ids_response.data:
                    st.warning(f"No se encontró ningún paciente con el RUT: {rut_busqueda}")
                    return

                fichas_ids = [item['id'] for item in ids_response.data]
                nombre_paciente = ids_response.data[0]['nombre_completo']
                
                todos_los_paths = set()

                # Buscar en 'test_epworth'
                epworth_response = supabase.from_('test_epworth').select('pdf_path').in_('id', fichas_ids).execute()
                if epworth_response.data:
                    for test in epworth_response.data:
                        if test.get('pdf_path'):
                            todos_los_paths.add(test['pdf_path'])
                
                # Buscar en 'test_epq_r'
                epq_r_response = supabase.from_('test_epq_r').select('pdf_path').in_('id', fichas_ids).execute()
                if epq_r_response.data:
                    for test in epq_r_response.data:
                        if test.get('pdf_path'):
                            todos_los_paths.add(test['pdf_path'])

                # Procesar y mostrar los informes encontrados
                if todos_los_paths:
                    st.success(f"Se encontraron {len(todos_los_paths)} informes para el paciente: {nombre_paciente}")
                    st.markdown("---")

                    for path in todos_los_paths:
                        nombre_archivo = path.split('/')[-1]
                        
                        tipo_informe = "Informe Desconocido"
                        if "Epworth" in nombre_archivo:
                            tipo_informe = "Informe de Test de Epworth"
                        elif "EPQR" in nombre_archivo:
                            tipo_informe = "Informe de Test EPQ-R"
                        
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
                                key=path
                            )
                            st.markdown("---")
                        except Exception as download_error:
                            st.error(f"No se pudo descargar el archivo '{nombre_archivo}': {download_error}")
                else:
                    st.warning(f"No se encontraron informes de tests EPWORTH o EPQ-R para el RUT: {rut_busqueda}")

            except Exception as db_error:
                st.error(f"Error al consultar la base de datos: {db_error}")
