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
tab1, tab2, tab3, tab4 = st.tabs(["Ver Actividades", "Añadir Actividad", "Asignar Agentes", "Editar Actividad"])

# Tab 1: View Activities
with tab1:
    st.subheader("Lista de Actividades")
    
    # Usar el DataFrame almacenado en session_state
    activities_df = st.session_state.activities_df
    
    if not activities_df.empty:
        # Create a display dataframe with additional information
        display_df = pd.DataFrame()
        
        # Process each activity to get full information
        for idx, activity in activities_df.iterrows():
            # Get course name
            try:
                curso_response = config.supabase.table(config.COURSES_TABLE).select("nombre").eq("id", activity['curso_id']).execute()
                curso_nombre = curso_response.data[0]['nombre'] if curso_response.data else "Sin curso"
            except:
                curso_nombre = "Error"
            
            # Get monitor name
            try:
                monitor_name = utils.get_agent_name(activity['monitor_nip']) if activity['monitor_nip'] else "Sin monitor"
            except:
                monitor_name = "Error"
            
            # Get participants
            try:
                participants_response = config.supabase.table(config.PARTICIPANTS_TABLE).select("agent_nip").eq("activity_id", activity['id']).execute()
                participant_nips = [p['agent_nip'] for p in participants_response.data] if participants_response.data else []
                
                if participant_nips:
                    participant_names = []
                    for nip in participant_nips:
                        participant_names.append(utils.get_agent_name(nip))
                    participants_str = ", ".join(participant_names)
                else:
                    participants_str = "Sin participantes"
            except:
                participants_str = "Error"
            
            # Format date
            fecha_formatted = utils.format_date(activity['fecha'])
            
            # Add to display dataframe
            display_df = pd.concat([display_df, pd.DataFrame({
                'ID': [activity['id']],
                'Fecha': [fecha_formatted],
                'Turno': [activity['turno']],
                'Curso': [curso_nombre],
                'Monitor': [monitor_name],
                'Participantes': [participants_str]
            })], ignore_index=True)
        
        # Display the dataframe
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )
        
        st.info(f"Total de actividades: {len(display_df)}")
    else:
        st.warning("No hay actividades disponibles en la base de datos.")

# Tab 2: Add Activity
with tab2:
    st.subheader("Añadir Nueva Actividad")
    
    # Check if user is monitor
    is_monitor = False
    try:
        # Get username from session
        username = st.session_state.get('username', '')
        if username:
            # Get user NIP from database
            user_response = config.supabase.table(config.USERS_TABLE).select("agent_nip").eq("username", username).execute()
            if user_response.data:
                user_nip = user_response.data[0]['agent_nip']
                
                # Check if user is a monitor
                agent_response = config.supabase.table(config.AGENTS_TABLE).select("monitor").eq("nip", user_nip).execute()
                if agent_response.data:
                    is_monitor = agent_response.data[0]['monitor']
    except Exception as e:
        st.error(f"Error al verificar el rol de monitor: {str(e)}")
    
    if not is_monitor:
        st.warning("Solo los monitores pueden programar actividades.")
    else:
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

# Tab 3: Assign Agents
with tab3:
    st.subheader("Asignar Agentes a Actividades")
    
    # Usar el DataFrame almacenado en session_state
    activities_df = st.session_state.activities_df
    
    if not activities_df.empty:
        # Create activity options for selection
        activity_options = []
        for _, activity in activities_df.iterrows():
            # Get course name
            try:
                curso_response = config.supabase.table(config.COURSES_TABLE).select("nombre").eq("id", activity['curso_id']).execute()
                curso_nombre = curso_response.data[0]['nombre'] if curso_response.data else "Sin curso"
            except:
                curso_nombre = "Error"
            
            # Format date
            fecha_formatted = utils.format_date(activity['fecha'])
            
            option_text = f"{activity['id']} - {fecha_formatted} - {activity['turno']} - {curso_nombre}"
            activity_options.append((option_text, activity['id']))
        
        # Dropdown to select activity
        selected_activity_text = st.selectbox(
            "Seleccionar actividad",
            options=[text for text, _ in activity_options],
            format_func=lambda x: x
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
            
            # Display activity details
            st.write(f"**Fecha:** {utils.format_date(activity_data['fecha'])}")
            st.write(f"**Turno:** {activity_data['turno']}")
            
            # Get course details
            try:
                if activity_data['curso_id']:
                    curso_response = config.supabase.table(config.COURSES_TABLE).select("nombre").eq("id", activity_data['curso_id']).execute()
                    st.write(f"**Curso:** {curso_response.data[0]['nombre'] if curso_response.data else 'Sin curso'}")
                else:
                    st.write("**Curso:** Sin curso asignado")
            except:
                st.write("**Curso:** Error al cargar")
            
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
            
            # Get all active agents
            agents_df = utils.get_all_agents(active_only=True)
            
            if not agents_df.empty:
                st.subheader("Seleccionar Participantes")
                
                # Create multiselect with all agents
                agent_options = {f"{agent['nip']} - {agent['nombre']} {agent['apellido1']} {agent['apellido2']}".strip(): agent['nip'] for _, agent in agents_df.iterrows()}
                
                # Determine default selections
                default_values = []
                for option, nip in agent_options.items():
                    if nip in current_participants:
                        default_values.append(option)
                
                selected_agents = st.multiselect(
                    "Seleccionar agentes participantes",
                    options=list(agent_options.keys()),
                    default=default_values
                )
                
                # Convert selections to NIPs
                selected_nips = [agent_options[agent] for agent in selected_agents]
                
                # Save button
                if st.button("Guardar Participantes"):
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
        st.warning("No hay actividades disponibles para asignar agentes.")

# Tab 4: Edit Activity
with tab4:
    st.subheader("Editar Actividad Existente")
    
    # Usar el DataFrame almacenado en session_state
    activities_df = st.session_state.activities_df
    
    if not activities_df.empty:
        # Create activity options for selection (same as in Tab 3)
        activity_options = []
        for _, activity in activities_df.iterrows():
            # Get course name
            try:
                curso_response = config.supabase.table(config.COURSES_TABLE).select("nombre").eq("id", activity['curso_id']).execute()
                curso_nombre = curso_response.data[0]['nombre'] if curso_response.data else "Sin curso"
            except:
                curso_nombre = "Error"
            
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
    else:
        st.warning("No hay actividades disponibles para editar.")
