import streamlit as st
from supabase import Client
from datetime import datetime

def crear_interfaz_pbll(supabase: Client):
    st.components.v1.html("<script>window.top.scrollTo(0, 0);</script>", height=0)
    st.title("Test Proyectivo PBLL")
    st.markdown("---")
    st.info(
        """
        **Instrucciones:** 1. En una hoja de papel, por favor dibuje una persona bajo la lluvia.
        2. Una vez que haya terminado su dibujo, tómale una fotografía o escanéalo.
        3. Sube la imagen del dibujo en el recuadro de abajo. Asegúrate de que la imagen sea clara y legible.
        """
    )

    with st.form(key="pbll_form"):
        st.markdown("---")
        comprende = st.checkbox("Sí, comprendo las instrucciones.", key="comprende_pbll")
        st.markdown("---")
        
        uploaded_file = st.file_uploader(
            "Cargue aquí la imagen de su dibujo",
            type=["png", "jpg", "jpeg"],
            help="Arrastre y suelte el archivo aquí, o haga clic para seleccionarlo."
        )

        siguiente_button = st.form_submit_button("Siguiente")

        if siguiente_button:
            if 'ficha_id' not in st.session_state:
                st.error("Error crítico: No se encontró el ID de la ficha de ingreso. Por favor, vuelva a empezar.")
                return

            if uploaded_file is None:
                st.warning("Por favor, suba una imagen de su dibujo para continuar.")
            else:
                with st.spinner("Subiendo y guardando su dibujo..."):
                    try:
                        # Generar un nombre de archivo único
                        rut_paciente = st.session_state.datos_paciente.get('rut', 'SIN_RUT')
                        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                        file_extension = uploaded_file.name.split('.')[-1]
                        file_name = f"{rut_paciente}_{timestamp}_PBLL.{file_extension}"
                        path_on_storage = f"fichas_ingreso_SM/pbll_images/{file_name}"

                        # Subir el archivo a Supabase Storage
                        file_bytes = uploaded_file.getvalue()
                        supabase.storage.from_("ficha_ingreso_SM_bucket").upload(
                            path=path_on_storage,
                            file=file_bytes,
                            file_options={"content-type": uploaded_file.type}
                        )

                        # Guardar la ruta en la tabla de la base de datos
                        pbll_data_to_save = {
                            "id": st.session_state.ficha_id,
                            "comprende": comprende,
                            "image_path": path_on_storage
                        }
                        
                        response = supabase.from_('test_pbll').insert(pbll_data_to_save).execute()

                        if response.data:
                            # Guardar localmente para la generación del PDF final
                            if 'form_data' not in st.session_state:
                                st.session_state.form_data = {}
                            st.session_state.form_data['test_pbll'] = pbll_data_to_save
                            
                            st.session_state.current_test_index += 1
                            st.rerun()
                        else:
                            st.error(f"Error al guardar los datos del test: {response.error.message if response.error else 'Error desconocido'}")

                    except Exception as e:
                        st.error(f"Ocurrió una excepción al procesar el archivo: {e}")
