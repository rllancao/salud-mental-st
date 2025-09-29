import streamlit as st
from supabase import Client
import io

BUCKET_NAME = "ficha_ingreso_SM_bucket"

def crear_interfaz_psicologo(supabase: Client):
    st.title("Búsqueda y Descarga de Fichas de Ingreso")
    st.write("Ingrese el RUT del paciente para buscar todas sus fichas de salud mental asociadas.")

    rut_busqueda = st.text_input("RUT del Paciente", placeholder="Ej. 12345678-9")

    if st.button("Buscar Fichas"):
        if not rut_busqueda:
            st.warning("Por favor, ingrese un RUT para buscar.")
            return

        try:
            # --- CAMBIO CLAVE: Se elimina .limit(1) para obtener TODOS los registros ---
            response = supabase.from_('registros_fichas_sm').select('nombre_completo, pdf_path').eq('rut', rut_busqueda).execute()

            if response.data:
                # Obtenemos el nombre del primer registro (asumimos que es el mismo para todos)
                nombre_completo = response.data[0]['nombre_completo']
                num_fichas = len(response.data)
                
                st.success(f"Se encontraron {num_fichas} fichas para el paciente: {nombre_completo}")
                st.markdown("---")

                # --- CAMBIO CLAVE: Iterar sobre cada ficha encontrada ---
                for ficha in response.data:
                    pdf_path_from_db = ficha['pdf_path']
                    # El nombre del archivo ahora contiene la fecha (ej: 12345678-9_2025-09-26.pdf)
                    file_name_for_download = pdf_path_from_db.split('/')[-1]

                    # Extraer la fecha del nombre del archivo para mostrarla
                    try:
                        fecha_ficha = file_name_for_download.split('_')[1].replace('.pdf', '')
                        st.subheader(f"Ficha del {fecha_ficha}")
                    except IndexError:
                        st.subheader(f"Archivo: {file_name_for_download}")


                    try:
                        # Descargar los bytes del archivo específico
                        res = supabase.storage.from_(BUCKET_NAME).download(path=pdf_path_from_db)
                        pdf_bytes = io.BytesIO(res)

                        # Mostrar un botón de descarga para cada ficha
                        st.download_button(
                            label=f"Descargar Ficha",
                            data=pdf_bytes,
                            file_name=file_name_for_download,
                            mime="application/pdf",
                            # Usamos la ruta completa como una 'key' única para el botón
                            key=pdf_path_from_db 
                        )
                        st.markdown("---")

                    except Exception as download_error:
                        st.error(f"No se pudo descargar el archivo '{file_name_for_download}': {download_error}")
            else:
                st.warning(f"No se encontró ninguna ficha para el RUT: {rut_busqueda}")

        except Exception as db_error:
            st.error(f"Error al consultar la base de datos: {db_error}")
