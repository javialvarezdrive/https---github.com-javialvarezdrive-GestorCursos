import streamlit as st
import pandas as pd
from datetime import datetime
import config
import utils

# Check authentication
utils.check_authentication()

# Inicialización del estado de la sesión para confirmaciones de eliminación
if "activity_confirm_delete" not in st.session_state:
    st.session_state.activity_confirm_delete = False
    
if "activity_to_delete_id" not in st.session_state:
    st.session_state.activity_to_delete_id = None

# Inicializar datos en el estado de la sesión
if "activities_df" not in st.session_state:
    st.session_state.activities_df = utils.get_all_activities()

# Page title
st.title("🗓️ Gestión de Actividades")

# Create tabs
tab_lista, tab_anadir, tab_editar = st.tabs(["Próximas Actividades", "Añadir Actividad", "Editar Actividad"])

# Tab: Próximas Actividades
with tab_lista:
    st.subheader("Próximas Actividades")
    
    # Usar el DataFrame almacenado en session_state
    activities_df = st.session_state.activities_df
    
    if not activities_df.empty:
        # Obtener listas de filtros posibles
        cursos = []
        monitores = []
        all_participants = []
        
        # Recopilar datos para filtros
        for _, activity in activities_df.iterrows():
            # Obtener nombre del curso
            try:
                if activity['curso_id']:
                    curso_response = config.supabase.table(config.COURSES_TABLE).select("nombre").eq("id", activity['curso_id']).execute()
                    if curso_response.data and len(curso_response.data) > 0:
                        curso_nombre = curso_response.data[0].get('nombre', 'Sin nombre')
                        if curso_nombre and curso_nombre not in cursos:
                            cursos.append(curso_nombre)
            except Exception as e:
                print(f"Error al obtener curso para filtros: {str(e)}")
                
            # Obtener monitor
            try:
                if activity['monitor_nip']:
                    monitor_name = utils.get_agent_name(activity['monitor_nip'])
                    if monitor_name and monitor_name not in monitores:
                        monitores.append(monitor_name)
            except:
                pass
                
            # Obtener participantes
            try:
                participants_response = config.supabase.table(config.PARTICIPANTS_TABLE).select("agent_nip").eq("activity_id", activity['id']).execute()
                if participants_response.data:
                    for p in participants_response.data:
                        participant_name = utils.get_agent_name(p['agent_nip'])
                        if participant_name and participant_name not in all_participants:
                            all_participants.append(participant_name)
            except:
                pass
        
        # Ordenar las listas para los filtros
        cursos.sort()
        monitores.sort()
        all_participants.sort()
        
        # Definir fechas por defecto
        fecha_actual = datetime.now().date()
        fecha_fin_default = fecha_actual + pd.Timedelta(days=30)
        
        # Poner filtros en un expander
        with st.expander("Filtros avanzados"):
            # Filtros en 3 columnas
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Filtro de rango de fechas
                fecha_inicio = st.date_input("Fecha inicio", fecha_actual)
                fecha_fin = st.date_input("Fecha fin", fecha_fin_default)
            
            with col2:
                # Filtro de cursos
                filtro_curso = st.multiselect("Filtrar por curso", ["Todos"] + cursos, default="Todos")
                
            with col3:
                # Filtro de monitor
                filtro_monitor = st.multiselect("Filtrar por monitor", ["Todos"] + monitores, default="Todos")
                
                # Filtro de participante
                filtro_participante = st.multiselect("Filtrar por participante", ["Todos"] + all_participants, default="Todos")
        
        # Create a display dataframe with additional information
        display_df = pd.DataFrame()
        filtered_count = 0
        
        # Process each activity to get full information
        for idx, activity in activities_df.iterrows():
            # Get course name
            try:
                curso_nombre = "Sin curso"
                if activity['curso_id'] is not None:
                    curso_response = config.supabase.table(config.COURSES_TABLE).select("nombre").eq("id", activity['curso_id']).execute()
                    if curso_response.data and len(curso_response.data) > 0:
                        curso_nombre = curso_response.data[0].get('nombre', 'Sin nombre')
            except Exception as e:
                curso_nombre = "Sin curso"
            
            # Get monitor name
            try:
                monitor_name = utils.get_agent_name(activity['monitor_nip']) if activity['monitor_nip'] else "Sin monitor"
            except:
                monitor_name = "Error"
            
            # Get participants
            try:
                participants_response = config.supabase.table(config.PARTICIPANTS_TABLE).select("agent_nip").eq("activity_id", activity['id']).execute()
                participant_nips = [p['agent_nip'] for p in participants_response.data] if participants_response.data else []
                
                participant_names = []
                if participant_nips:
                    for nip in participant_nips:
                        participant_names.append(utils.get_agent_name(nip))
                    participants_str = ", ".join(participant_names)
                else:
                    participants_str = "Sin participantes"
            except:
                participants_str = "Error"
                participant_names = []
            
            # Format date
            fecha_formatted = utils.format_date(activity['fecha'])
            fecha_obj = datetime.strptime(activity['fecha'], "%Y-%m-%d").date()
            
            # Aplicar filtros
            pasa_filtro = True
            
            # Filtro de fechas
            if fecha_obj < fecha_inicio or fecha_obj > fecha_fin:
                pasa_filtro = False
            
            # Filtro de curso
            if "Todos" not in filtro_curso and curso_nombre not in filtro_curso:
                pasa_filtro = False
                
            # Filtro de monitor
            if "Todos" not in filtro_monitor and monitor_name not in filtro_monitor:
                pasa_filtro = False
                
            # Filtro de participante
            if "Todos" not in filtro_participante:
                participante_encontrado = False
                for participante in participant_names:
                    if participante in filtro_participante:
                        participante_encontrado = True
                        break
                if not participante_encontrado:
                    pasa_filtro = False
            
            if pasa_filtro:
                filtered_count += 1
                # Add to display dataframe
                display_df = pd.concat([display_df, pd.DataFrame({
                    'Fecha': [fecha_formatted],
                    'Turno': [activity['turno']],
                    'Curso': [curso_nombre],
                    'Monitor': [monitor_name],
                    'Participantes': [participants_str]
                })], ignore_index=True)
        
        # Visualización de participantes más clara
        if not display_df.empty:
            # Display the dataframe
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True
            )
            
            # Mostrar actividades seleccionadas para ver detalles
            st.write("### Detalles de participantes")
            if len(display_df) > 0:
                # Usar el índice porque ya no tenemos IDs visibles
                selected_idx = st.selectbox("Seleccionar actividad para ver detalles de participantes", 
                                         range(len(display_df)),
                                         format_func=lambda i: f"{display_df.iloc[i]['Fecha']} - {display_df.iloc[i]['Turno']} - {display_df.iloc[i]['Curso']}")
                
                if selected_idx is not None:
                    st.write(f"**Participantes de la actividad:**")
                    participants_str = display_df.iloc[selected_idx]['Participantes']
                    
                    if participants_str != "Sin participantes" and participants_str != "Error":
                        participant_list = participants_str.split(", ")
                        cols = st.columns(min(3, len(participant_list)))
                        
                        for i, participant in enumerate(participant_list):
                            with cols[i % 3]:
                                st.markdown(f"**{i+1}.** {participant}")
                    else:
                        st.info("Esta actividad no tiene participantes asignados.")
            
            st.info(f"Mostrando {len(display_df)} de {len(activities_df)} actividades (filtradas: {filtered_count})")
        else:
            st.warning("No hay actividades que coincidan con los filtros seleccionados.")
    else:
        st.warning("No hay actividades disponibles en la base de datos.")

# Tab: Añadir Actividad
with tab_anadir:
    st.subheader("Añadir Nueva Actividad")
    
    # Obtener información del usuario para asignar como monitor predeterminado
    user_nip = None
    try:
        # Get username from session
        username = st.session_state.get('username', '')
        if username:
            # Get user NIP from database
            user_response = config.supabase.table(config.USERS_TABLE).select("agent_nip").eq("username", username).execute()
            if user_response.data:
                user_nip = user_response.data[0]['agent_nip']
    except Exception as e:
        st.error(f"Error al obtener información del usuario: {str(e)}")
    
    # Todos los usuarios autenticados pueden programar actividades
    # Create form
    with st.form("add_activity_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            fecha = st.date_input("Fecha *", datetime.now())
            turno = st.selectbox("Turno *", [""] + config.SHIFTS)
        
        with col2:
            # Get available courses
            courses_df = utils.get_all_courses()
            course_options = [""] + [f"{course['id']} - {course['nombre']}" for _, course in courses_df.iterrows()] if not courses_df.empty else [""]
            
            selected_course = st.selectbox("Curso", course_options)
            
            # Extract course ID from selection
            curso_id = None
            if selected_course and selected_course != "":
                curso_id = int(selected_course.split(" - ")[0])
            
            # Get user NIP as default monitor
            user_nip = None
            try:
                user_response = config.supabase.table(config.USERS_TABLE).select("agent_nip").eq("username", st.session_state.username).execute()
                if user_response.data:
                    user_nip = user_response.data[0]['agent_nip']
            except:
                pass
            
            # Get monitors for selection
            monitors_df = utils.get_all_monitors()
            monitor_options = [""] + [f"{monitor['nip']} - {monitor['nombre']} {monitor['apellido1']}" for _, monitor in monitors_df.iterrows()] if not monitors_df.empty else [""]
            
            # Find index of user_nip in monitor_options
            default_index = 0
            if user_nip:
                for i, option in enumerate(monitor_options):
                    if option and option.startswith(f"{user_nip} -"):
                        default_index = i
                        break
            
            selected_monitor = st.selectbox("Monitor", monitor_options, index=default_index)
            
            # Extract monitor NIP from selection
            monitor_nip = None
            if selected_monitor and selected_monitor != "":
                monitor_nip = selected_monitor.split(" - ")[0]
            
        # Submit button
        submitted = st.form_submit_button("Añadir Actividad")
        
        if submitted:
            # Validate form data
            validation_errors = utils.validate_activity(fecha, turno)
            
            if validation_errors:
                for error in validation_errors:
                    st.error(error)
            else:
                # Check if activity already exists on the same date and shift
                try:
                    existing_activity = config.supabase.table(config.ACTIVITIES_TABLE).select("*").eq("fecha", fecha.strftime("%Y-%m-%d")).eq("turno", turno).execute()
                    
                    if existing_activity.data:
                        st.error(f"Ya existe una actividad programada para esa fecha y turno")
                    else:
                        # Prepare data
                        activity_data = {
                            'fecha': fecha.strftime("%Y-%m-%d"),
                            'turno': turno,
                            'curso_id': curso_id,
                            'monitor_nip': monitor_nip
                        }
                        
                        # Insert data
                        result = config.supabase.table(config.ACTIVITIES_TABLE).insert(activity_data).execute()
                        
                        if result.data:
                            st.success(f"Actividad añadida correctamente para el {fecha.strftime('%d/%m/%Y')} en turno {turno}")
                            # Actualizar DataFrame en session_state
                            st.session_state.activities_df = utils.get_all_activities()
                            st.rerun()
                        else:
                            st.error("Error al añadir la actividad")
                except Exception as e:
                    st.error(f"Error: {str(e)}")



# Tab: Edit Activity
with tab_editar:
    st.subheader("Editar Actividad Existente")
    
    # Usar el DataFrame almacenado en session_state
    activities_df = st.session_state.activities_df
    
    if not activities_df.empty:
        # Create activity options for selection (same as in Tab 3)
        activity_options = []
        for _, activity in activities_df.iterrows():
            # Get course name
            try:
                curso_nombre = "Sin curso"
                if activity['curso_id'] is not None:
                    curso_response = config.supabase.table(config.COURSES_TABLE).select("nombre").eq("id", activity['curso_id']).execute()
                    if curso_response.data and len(curso_response.data) > 0:
                        curso_nombre = curso_response.data[0].get('nombre', 'Sin nombre')
            except Exception as e:
                st.error(f"Error al obtener el curso: {str(e)}")
                curso_nombre = "Sin curso"
            
            # Format date
            fecha_formatted = utils.format_date(activity['fecha'])
            
            option_text = f"{activity['id']} - {fecha_formatted} - {activity['turno']} - {curso_nombre}"
            activity_options.append((option_text, activity['id']))
        
        # Dropdown to select activity
        selected_activity_text = st.selectbox(
            "Seleccionar actividad a editar",
            options=[text for text, _ in activity_options],
            format_func=lambda x: x,
            key="edit_activity_select"
        )
        
        # Get the ID of the selected activity
        selected_activity_id = None
        for text, id in activity_options:
            if text == selected_activity_text:
                selected_activity_id = id
                break
        
        if selected_activity_id:
            # Get activity details
            activity_data = activities_df[activities_df['id'] == selected_activity_id].iloc[0].to_dict()
            
            # Si estamos en modo de confirmación de eliminación
            if st.session_state.activity_confirm_delete and st.session_state.activity_to_delete_id == selected_activity_id:
                st.warning(f"¿Estás seguro de que deseas eliminar esta actividad?")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Sí, eliminar"):
                        try:
                            # First delete all participants
                            config.supabase.table(config.PARTICIPANTS_TABLE).delete().eq("activity_id", selected_activity_id).execute()
                            
                            # Then delete the activity
                            result = config.supabase.table(config.ACTIVITIES_TABLE).delete().eq("id", selected_activity_id).execute()
                            
                            if result.data:
                                st.success(f"Actividad eliminada correctamente")
                                # Limpiar modo de confirmación
                                st.session_state.activity_confirm_delete = False
                                st.session_state.activity_to_delete_id = None
                                # Actualizar DataFrame de actividades
                                st.session_state.activities_df = utils.get_all_activities()
                                st.rerun()
                            else:
                                st.error("Error al eliminar la actividad")
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
                
                with col2:
                    if st.button("No, cancelar"):
                        # Limpiar modo de confirmación
                        st.session_state.activity_confirm_delete = False
                        st.session_state.activity_to_delete_id = None
                        st.rerun()
            
            # Si no estamos en modo de confirmación, mostrar el formulario de edición
            tabs_edicion = st.tabs(["Datos de la actividad", "Gestión de participantes"])
            
            with tabs_edicion[0]:
                with st.form("edit_activity_form"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Convert string date to datetime
                        try:
                            current_date = datetime.strptime(activity_data['fecha'], "%Y-%m-%d")
                        except:
                            current_date = datetime.now()
                        
                        fecha = st.date_input("Fecha *", current_date)
                        turno = st.selectbox(
                            "Turno *", 
                            config.SHIFTS,
                            index=config.SHIFTS.index(activity_data['turno']) if activity_data['turno'] in config.SHIFTS else 0
                        )
                    
                    with col2:
                        # Get available courses
                        courses_df = utils.get_all_courses()
                        course_options = [""] + [f"{course['id']} - {course['nombre']}" for _, course in courses_df.iterrows()] if not courses_df.empty else [""]
                        
                        # Determine default course selection
                        default_course_index = 0
                        current_course_id = activity_data['curso_id']
                        if current_course_id:
                            for i, option in enumerate(course_options):
                                if option and option.startswith(f"{current_course_id} -"):
                                    default_course_index = i
                                    break
                        
                        selected_course = st.selectbox("Curso", course_options, index=default_course_index)
                        
                        # Extract course ID from selection
                        curso_id = None
                        if selected_course and selected_course != "":
                            curso_id = int(selected_course.split(" - ")[0])
                        
                        # Get monitors for selection
                        monitors_df = utils.get_all_monitors()
                        monitor_options = [""] + [f"{monitor['nip']} - {monitor['nombre']} {monitor['apellido1']}" for _, monitor in monitors_df.iterrows()] if not monitors_df.empty else [""]
                        
                        # Determine default monitor selection
                        default_monitor_index = 0
                        current_monitor_nip = activity_data['monitor_nip']
                        if current_monitor_nip:
                            for i, option in enumerate(monitor_options):
                                if option and option.startswith(f"{current_monitor_nip} -"):
                                    default_monitor_index = i
                                    break
                        
                        selected_monitor = st.selectbox("Monitor", monitor_options, index=default_monitor_index)
                        
                        # Extract monitor NIP from selection
                        monitor_nip = None
                        if selected_monitor and selected_monitor != "":
                            monitor_nip = selected_monitor.split(" - ")[0]
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        submit_button = st.form_submit_button("Actualizar Actividad")
                    with col2:
                        delete_button = st.form_submit_button("Eliminar Actividad", type="secondary")
                    
                    if submit_button:
                        # Validate form data
                        validation_errors = utils.validate_activity(fecha, turno)
                        
                        if validation_errors:
                            for error in validation_errors:
                                st.error(error)
                        else:
                            # Check if activity already exists on the same date and shift (excluding this one)
                            try:
                                existing_activity = config.supabase.table(config.ACTIVITIES_TABLE).select("*").eq("fecha", fecha.strftime("%Y-%m-%d")).eq("turno", turno).neq("id", selected_activity_id).execute()
                                
                                if existing_activity.data:
                                    st.error(f"Ya existe otra actividad programada para esa fecha y turno")
                                else:
                                    # Prepare updated data
                                    updated_data = {
                                        'fecha': fecha.strftime("%Y-%m-%d"),
                                        'turno': turno,
                                        'curso_id': curso_id,
                                        'monitor_nip': monitor_nip
                                    }
                                    
                                    # Update data
                                    result = config.supabase.table(config.ACTIVITIES_TABLE).update(updated_data).eq("id", selected_activity_id).execute()
                                    
                                    if result.data:
                                        st.success(f"Actividad actualizada correctamente")
                                        # Actualizar DataFrame en session_state
                                        st.session_state.activities_df = utils.get_all_activities()
                                        st.rerun()
                                    else:
                                        st.error("Error al actualizar la actividad")
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
                    
                    if delete_button:
                        # Activar modo de confirmación
                        st.session_state.activity_confirm_delete = True
                        st.session_state.activity_to_delete_id = selected_activity_id
                        st.rerun()
                        
            # Tab para gestionar participantes
            with tabs_edicion[1]:
                st.subheader("Gestión de Participantes")
                
                # Mostrar detalles de la actividad seleccionada
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Fecha:** {utils.format_date(activity_data['fecha'])}")
                    st.write(f"**Turno:** {activity_data['turno']}")
                
                with col2:
                    # Get course details
                    try:
                        curso_nombre = "Sin curso asignado"
                        if activity_data['curso_id'] is not None:
                            curso_response = config.supabase.table(config.COURSES_TABLE).select("nombre").eq("id", activity_data['curso_id']).execute()
                            if curso_response.data and len(curso_response.data) > 0:
                                curso_nombre = curso_response.data[0].get('nombre', 'Sin nombre')
                            st.write(f"**Curso:** {curso_nombre}")
                        else:
                            st.write("**Curso:** Sin curso asignado")
                    except Exception as e:
                        st.error(f"Error al obtener el curso para los detalles: {str(e)}")
                        st.write("**Curso:** Sin curso asignado")
                    
                    # Get monitor details
                    try:
                        if activity_data['monitor_nip']:
                            monitor_name = utils.get_agent_name(activity_data['monitor_nip'])
                            st.write(f"**Monitor:** {monitor_name}")
                        else:
                            st.write("**Monitor:** Sin monitor asignado")
                    except:
                        st.write("**Monitor:** Error al cargar")
                
                # Get current participants
                current_participants = []
                try:
                    participants_response = config.supabase.table(config.PARTICIPANTS_TABLE).select("agent_nip").eq("activity_id", selected_activity_id).execute()
                    current_participants = [p['agent_nip'] for p in participants_response.data] if participants_response.data else []
                except Exception as e:
                    st.error(f"Error al cargar participantes: {str(e)}")
                
                # Si hay participantes actuales, mostrarlos
                if current_participants:
                    participant_names = []
                    for nip in current_participants:
                        participant_names.append(utils.get_agent_name(nip))
                    
                    st.write("### Participantes actuales")
                    cols_participants = st.columns(min(3, len(participant_names)))
                    for i, name in enumerate(participant_names):
                        with cols_participants[i % 3]:
                            st.markdown(f"**{i+1}.** {name}")
                else:
                    st.info("Esta actividad no tiene participantes asignados.")
                
                # Get all active agents
                agents_df = utils.get_all_agents(active_only=True)
                
                if not agents_df.empty:
                    st.write("### Seleccionar Participantes")
                    
                    # Create multiselect with all agents
                    agent_options = {f"{agent['nip']} - {agent['nombre']} {agent['apellido1']} {agent['apellido2']}".strip(): agent['nip'] for _, agent in agents_df.iterrows()}
                    
                    # Determine default selections
                    default_values = []
                    for option, nip in agent_options.items():
                        if nip in current_participants:
                            default_values.append(option)
                    
                    # Usar formulario para gestionar participantes
                    with st.form("participantes_form"):
                        selected_agents = st.multiselect(
                            "Seleccionar agentes participantes",
                            options=list(agent_options.keys()),
                            default=default_values
                        )
                        
                        # Convert selections to NIPs
                        selected_nips = [agent_options[agent] for agent in selected_agents]
                        
                        # Save button
                        save_participants = st.form_submit_button("Guardar Participantes")
                        
                        if save_participants:
                            try:
                                # First delete all current participants
                                config.supabase.table(config.PARTICIPANTS_TABLE).delete().eq("activity_id", selected_activity_id).execute()
                                
                                # Then add new participants
                                for nip in selected_nips:
                                    participant_data = {
                                        'activity_id': selected_activity_id,
                                        'agent_nip': nip
                                    }
                                    config.supabase.table(config.PARTICIPANTS_TABLE).insert(participant_data).execute()
                                
                                st.success("Participantes actualizados correctamente")
                                # Actualizar DataFrame en session_state
                                st.session_state.activities_df = utils.get_all_activities()
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error al actualizar participantes: {str(e)}")
                else:
                    st.warning("No hay agentes activos disponibles.")
    else:
        st.warning("No hay actividades disponibles para editar.")
