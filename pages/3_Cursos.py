import streamlit as st
import pandas as pd
import config
import utils

# Check authentication
utils.check_authentication()

# Configura el sidebar y el botón de cerrar sesión
utils.setup_sidebar()

# Page title
st.title("📚 Gestión de Cursos")

# Inicializar variables de estado para el modo de confirmación
if "confirm_delete" not in st.session_state:
    st.session_state.confirm_delete = False
    
if "course_to_delete_id" not in st.session_state:
    st.session_state.course_to_delete_id = None
    
if "course_to_delete_name" not in st.session_state:
    st.session_state.course_to_delete_name = None

# Diseño de dos columnas
col_izquierda, col_derecha = st.columns([2, 3])

# Columna izquierda - Formularios de Gestión
with col_izquierda:
    # Sección para añadir nuevo curso
    st.subheader("Añadir Nuevo Curso")
    with st.form("add_course_form"):
        nombre = st.text_input("Nombre del Curso *", "")
        descripcion = st.text_area("Descripción (opcional)", "")
        ocultar = st.checkbox("Ocultar Curso", False)
        
        # Submit button
        submitted = st.form_submit_button("Añadir Curso")
        
        if submitted:
            # Validate form data (ahora la descripción es opcional)
            validation_errors = utils.validate_course(nombre, descripcion)
            
            if validation_errors:
                for error in validation_errors:
                    st.error(error)
            else:
                # Check if course already exists
                try:
                    existing_course = config.supabase.table(config.COURSES_TABLE).select("nombre").eq("nombre", nombre).execute()
                    
                    if existing_course.data:
                        st.error(f"Ya existe un curso con el nombre '{nombre}'")
                    else:
                        # Prepare data
                        course_data = {
                            'nombre': nombre,
                            'descripcion': descripcion,
                            'ocultar': ocultar
                        }
                        
                        # Insert data
                        result = config.supabase.table(config.COURSES_TABLE).insert(course_data).execute()
                        
                        if result.data:
                            st.success(f"Curso '{nombre}' añadido correctamente")
                            st.rerun()
                        else:
                            st.error("Error al añadir el curso")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    # Sección para editar curso existente
    st.subheader("Editar Curso Existente")
    
    # Get all courses for selection
    courses_df = utils.get_all_courses(include_hidden=True)
    
    if not courses_df.empty:
        # Create a dropdown to select a course by name
        course_names = courses_df['nombre'].tolist()
        selected_course = st.selectbox("Seleccionar curso a editar", options=course_names)
        
        if selected_course:
            # Get course data
            course_data = courses_df[courses_df['nombre'] == selected_course].iloc[0].to_dict()
            
            # Si está en modo de confirmación de eliminación
            if st.session_state.confirm_delete:
                st.warning(f"¿Estás seguro de que deseas eliminar el curso '{st.session_state.course_to_delete_name}'?")
                
                confirm_col1, confirm_col2 = st.columns(2)
                with confirm_col1:
                    if st.button("Sí, eliminar"):
                        try:
                            # Check if course is used in any activity
                            activities = config.supabase.table(config.ACTIVITIES_TABLE).select("id").eq("curso_id", st.session_state.course_to_delete_id).execute()
                            
                            if activities.data:
                                st.error("No se puede eliminar el curso porque está siendo utilizado en actividades")
                            else:
                                # Delete course
                                result = config.supabase.table(config.COURSES_TABLE).delete().eq("id", st.session_state.course_to_delete_id).execute()
                                
                                if result.data:
                                    st.success(f"Curso '{st.session_state.course_to_delete_name}' eliminado correctamente")
                                    # Limpiar modo de confirmación
                                    st.session_state.confirm_delete = False
                                    st.session_state.course_to_delete_id = None
                                    st.session_state.course_to_delete_name = None
                                    st.rerun()
                                else:
                                    st.error("Error al eliminar el curso")
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
                
                with confirm_col2:
                    if st.button("No, cancelar"):
                        # Limpiar modo de confirmación
                        st.session_state.confirm_delete = False
                        st.session_state.course_to_delete_id = None
                        st.session_state.course_to_delete_name = None
                        st.rerun()
            
            # Si no está en modo de confirmación, mostrar el formulario de edición
            else:
                # Create form for editing
                with st.form("edit_course_form"):
                    course_id = course_data['id']
                    nombre = st.text_input("Nombre del Curso *", course_data['nombre'])
                    descripcion = st.text_area("Descripción (opcional)", course_data['descripcion'])
                    ocultar = st.checkbox("Ocultar Curso", course_data['ocultar'])
                    
                    edit_col1, edit_col2 = st.columns(2)
                    with edit_col1:
                        submit_button = st.form_submit_button("Actualizar Curso")
                    with edit_col2:
                        delete_button = st.form_submit_button("Eliminar Curso", type="secondary")
                    
                    if submit_button:
                        # Validate form data
                        validation_errors = utils.validate_course(nombre, descripcion)
                        
                        if validation_errors:
                            for error in validation_errors:
                                st.error(error)
                        else:
                            # Check if course name already exists (if changed)
                            try:
                                if nombre != course_data['nombre']:
                                    existing_course = config.supabase.table(config.COURSES_TABLE).select("nombre").eq("nombre", nombre).execute()
                                    
                                    if existing_course.data:
                                        st.error(f"Ya existe un curso con el nombre '{nombre}'")
                                        st.stop()
                                
                                # Prepare updated data
                                updated_data = {
                                    'nombre': nombre,
                                    'descripcion': descripcion,
                                    'ocultar': ocultar
                                }
                                
                                # Update data
                                result = config.supabase.table(config.COURSES_TABLE).update(updated_data).eq("id", course_id).execute()
                                
                                if result.data:
                                    st.success(f"Curso '{nombre}' actualizado correctamente")
                                    st.rerun()
                                else:
                                    st.error("Error al actualizar el curso")
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
                    
                    if delete_button:
                        # Preparar el modo de confirmación
                        st.session_state.confirm_delete = True
                        st.session_state.course_to_delete_id = course_id
                        st.session_state.course_to_delete_name = nombre
                        st.rerun()
    else:
        st.warning("No hay cursos disponibles para editar.")

# Columna derecha - Vista de cursos
with col_derecha:
    st.subheader("Lista de Cursos")
    
    # Filter option
    show_hidden = st.checkbox("Mostrar cursos ocultos", False)
    
    # Get courses data
    courses_df = utils.get_all_courses(include_hidden=True)
    
    if not courses_df.empty:
        # Apply filter if needed
        if not show_hidden:
            display_df = courses_df[courses_df['ocultar'] == False].copy()
        else:
            display_df = courses_df.copy()
        
        if not display_df.empty:
            # Format boolean columns
            display_df['ocultar'] = display_df['ocultar'].apply(utils.format_bool)
            
            # Eliminar ID y created_at y renombrar columnas para mostrar
            display_df_clean = display_df[['nombre', 'descripcion', 'ocultar']].copy()
            
            columns_rename = {
                'nombre': 'Nombre',
                'descripcion': 'Descripción',
                'ocultar': 'Oculto'
            }
            
            # Display the dataframe
            st.dataframe(
                display_df_clean.rename(columns=columns_rename),
                use_container_width=True,
                hide_index=True
            )
            
            st.info(f"Total de cursos: {len(display_df)}")
        else:
            st.warning("No hay cursos visibles. Marca la casilla 'Mostrar cursos ocultos' para ver todos los cursos.")
    else:
        st.warning("No hay cursos disponibles en la base de datos.")
