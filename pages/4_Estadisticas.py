import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import config
import utils

# Check authentication
utils.check_authentication()

# Configura el sidebar y el botón de cerrar sesión
utils.setup_sidebar()

# Page title
st.title("📊 Estadísticas")

# Inicializar variables de estado para las vistas personalizadas
if 'view_mode' not in st.session_state:
    st.session_state.view_mode = "dashboard"  # Opciones: "dashboard", "custom"
    
if 'selected_view' not in st.session_state:
    st.session_state.selected_view = "participacion_seccion"
    
if 'saved_views' not in st.session_state:
    # Inicializar con algunas vistas predefinidas
    st.session_state.saved_views = {
        "participacion_seccion": {
            "name": "Participación por Sección",
            "description": "Muestra la distribución de participación por sección",
            "view_type": "bar",
            "x_axis": "seccion",
            "y_axis": "count"
        },
        "participacion_grupo": {
            "name": "Participación por Grupo",
            "description": "Muestra la distribución de participación por grupo",
            "view_type": "bar",
            "x_axis": "grupo",
            "y_axis": "count"
        },
        "agentes_activos": {
            "name": "Top Agentes Activos",
            "description": "Muestra los agentes con más participación",
            "view_type": "bar",
            "x_axis": "agente",
            "y_axis": "count",
            "limit": 10
        }
    }

# Main function
def show_statistics():
    # Sidebar filters
    st.sidebar.header("Filtros")
    
    # Date range filter
    st.sidebar.subheader("Rango de fechas")
    
    # Calculate default date ranges (current month)
    today = datetime.now()
    start_of_month = datetime(today.year, today.month, 1)
    
    # Default start and end dates
    default_start_date = start_of_month
    default_end_date = today
    
    # Date inputs
    start_date = st.sidebar.date_input("Fecha inicio", default_start_date)
    end_date = st.sidebar.date_input("Fecha fin", default_end_date)
    
    # Toggle para vistas dinámicas
    st.sidebar.subheader("Tipo de visualización")
    view_mode = st.sidebar.radio(
        "Modo de visualización",
        ["Dashboard estándar", "Vista personalizada"],
        index=0 if st.session_state.view_mode == "dashboard" else 1,
        key="view_mode_radio"
    )
    
    # Actualizar modo de visualización
    st.session_state.view_mode = "dashboard" if view_mode == "Dashboard estándar" else "custom"
    
    # Section filter
    try:
        agents_df = utils.get_all_agents()
        if not agents_df.empty:
            # Get unique sections
            sections = sorted(agents_df['seccion'].unique().tolist())
            sections = [s for s in sections if s]  # Remove empty values
            
            selected_sections = st.sidebar.multiselect(
                "Secciones",
                options=sections,
                default=[]
            )
        else:
            selected_sections = []
    except:
        selected_sections = []
        st.sidebar.warning("No se pudieron cargar las secciones")
    
    # Group filter
    try:
        if not agents_df.empty:
            # Get unique groups
            groups = sorted(agents_df['grupo'].unique().tolist())
            groups = [g for g in groups if g]  # Remove empty values
            
            selected_groups = st.sidebar.multiselect(
                "Grupos",
                options=groups,
                default=[]
            )
        else:
            selected_groups = []
    except:
        selected_groups = []
        st.sidebar.warning("No se pudieron cargar los grupos")
        
    # Si estamos en modo Vista personalizada, mostrar selector de vistas
    if st.session_state.view_mode == "custom":
        st.sidebar.subheader("Vistas personalizadas")
        
        # Opciones de vistas guardadas
        view_options = list(st.session_state.saved_views.keys())
        view_names = [st.session_state.saved_views[key]["name"] for key in view_options]
        
        # Selector de vista
        selected_view_name = st.sidebar.selectbox(
            "Seleccionar vista",
            view_names,
            index=view_options.index(st.session_state.selected_view) if st.session_state.selected_view in view_options else 0
        )
        
        # Actualizar la vista seleccionada
        for key, view in st.session_state.saved_views.items():
            if view["name"] == selected_view_name:
                st.session_state.selected_view = key
                break
        
        # Sección para crear nueva vista personalizada
        with st.sidebar.expander("Crear nueva vista", expanded=False):
            new_view_name = st.text_input("Nombre de la vista", key="new_view_name")
            new_view_desc = st.text_area("Descripción", key="new_view_desc")
            new_view_type = st.selectbox("Tipo de gráfico", ["bar", "line", "pie", "scatter"], key="new_view_type")
            
            # Opciones para los ejes
            axis_options = {
                "seccion": "Sección",
                "grupo": "Grupo",
                "agente": "Agente",
                "fecha": "Fecha",
                "curso": "Curso",
                "count": "Cantidad"
            }
            
            new_x_axis = st.selectbox("Eje X", list(axis_options.keys()), format_func=lambda x: axis_options[x], key="new_x_axis")
            new_y_axis = st.selectbox("Eje Y", list(axis_options.keys()), index=list(axis_options.keys()).index("count"), format_func=lambda x: axis_options[x], key="new_y_axis")
            
            # Límite de datos (opcional)
            new_limit = st.number_input("Límite de datos (0 = sin límite)", min_value=0, value=0, key="new_limit")
            
            if st.button("Guardar vista"):
                if new_view_name:
                    # Generar un ID único para la vista
                    new_view_id = f"custom_view_{len(st.session_state.saved_views) + 1}"
                    
                    # Guardar la nueva vista
                    st.session_state.saved_views[new_view_id] = {
                        "name": new_view_name,
                        "description": new_view_desc,
                        "view_type": new_view_type,
                        "x_axis": new_x_axis,
                        "y_axis": new_y_axis,
                        "limit": new_limit if new_limit > 0 else None
                    }
                    
                    # Seleccionar automáticamente la nueva vista
                    st.session_state.selected_view = new_view_id
                    st.success(f"Vista '{new_view_name}' creada con éxito!")
                    st.rerun()
                else:
                    st.error("Por favor, proporciona un nombre para la vista.")
    
    # Apply filters and load data
    try:
        # Get all activities within date range
        activities_response = config.supabase.table(config.ACTIVITIES_TABLE).select("*").gte("fecha", start_date.strftime("%Y-%m-%d")).lte("fecha", end_date.strftime("%Y-%m-%d")).execute()
        
        if not activities_response.data:
            st.warning("No hay actividades en el rango de fechas seleccionado")
            return
        
        activities_df = pd.DataFrame(activities_response.data)
        
        # Get all participants
        participants_response = config.supabase.table(config.PARTICIPANTS_TABLE).select("*").execute()
        
        if not participants_response.data:
            st.warning("No hay participantes registrados en actividades")
            return
        
        participants_df = pd.DataFrame(participants_response.data)
        
        # Filter activities to only those in our dataset
        activity_ids = activities_df['id'].tolist()
        participants_df = participants_df[participants_df['activity_id'].isin(activity_ids)]
        
        # Get agent details
        agents_df = utils.get_all_agents()
        
        # Apply section and group filters to agents
        if selected_sections:
            agents_df = agents_df[agents_df['seccion'].isin(selected_sections)]
        
        if selected_groups:
            agents_df = agents_df[agents_df['grupo'].isin(selected_groups)]
        
        # Filter participants to only include agents that match our filters
        agent_nips = agents_df['nip'].tolist()
        filtered_participants_df = participants_df[participants_df['agent_nip'].isin(agent_nips)]
        
        # Get courses data
        courses_response = config.supabase.table(config.COURSES_TABLE).select("*").execute()
        courses_df = pd.DataFrame(courses_response.data) if courses_response.data else pd.DataFrame()
        
        # Proceed with data analysis
        if not filtered_participants_df.empty:
            # Display statistics
            st.header("Análisis de Participación")
            
            # 1. Overview metrics
            col1, col2, col3, col4 = st.columns(4)
            
            total_activities = len(activities_df)
            with col1:
                st.metric("Total Actividades", total_activities)
            
            total_participations = len(filtered_participants_df)
            with col2:
                st.metric("Total Participaciones", total_participations)
            
            unique_participants = filtered_participants_df['agent_nip'].nunique()
            with col3:
                st.metric("Agentes Únicos", unique_participants)
            
            avg_participants = round(total_participations / total_activities, 2) if total_activities > 0 else 0
            with col4:
                st.metric("Media Participantes/Actividad", avg_participants)
            
            # 2. Participation by section
            st.subheader("Participación por Sección")
            
            # Create participation by section data
            section_participation = []
            for _, participant in filtered_participants_df.iterrows():
                agent_data = agents_df[agents_df['nip'] == participant['agent_nip']]
                if not agent_data.empty:
                    section = agent_data.iloc[0]['seccion']
                    if section:  # Only include if section is not empty
                        section_participation.append(section)
            
            section_counts = pd.Series(section_participation).value_counts().reset_index()
            section_counts.columns = ['Sección', 'Participaciones']
            
            if not section_counts.empty:
                fig = px.bar(
                    section_counts, 
                    x='Sección', 
                    y='Participaciones',
                    color='Participaciones',
                    color_continuous_scale='Blues',
                    title='Participaciones por Sección'
                )
                fig.update_layout(xaxis_title='Sección', yaxis_title='Número de Participaciones')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No hay datos de participación por sección")
            
            # 3. Participation by group
            st.subheader("Participación por Grupo")
            
            # Create participation by group data
            group_participation = []
            for _, participant in filtered_participants_df.iterrows():
                agent_data = agents_df[agents_df['nip'] == participant['agent_nip']]
                if not agent_data.empty:
                    group = agent_data.iloc[0]['grupo']
                    if group:  # Only include if group is not empty
                        group_participation.append(group)
            
            group_counts = pd.Series(group_participation).value_counts().reset_index()
            group_counts.columns = ['Grupo', 'Participaciones']
            
            if not group_counts.empty:
                fig = px.bar(
                    group_counts, 
                    x='Grupo', 
                    y='Participaciones',
                    color='Participaciones',
                    color_continuous_scale='Greens',
                    title='Participaciones por Grupo'
                )
                fig.update_layout(xaxis_title='Grupo', yaxis_title='Número de Participaciones')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No hay datos de participación por grupo")
            
            # 4. Activity participation over time
            st.subheader("Participación a lo largo del tiempo")
            
            # Create time series data
            time_data = []
            for _, activity in activities_df.iterrows():
                activity_id = activity['id']
                activity_date = activity['fecha']
                
                # Count participants for this activity (filtered by our criteria)
                participants_count = len(filtered_participants_df[filtered_participants_df['activity_id'] == activity_id])
                
                time_data.append({
                    'Fecha': activity_date,
                    'Participantes': participants_count
                })
            
            time_df = pd.DataFrame(time_data)
            if not time_df.empty:
                time_df['Fecha'] = pd.to_datetime(time_df['Fecha'])
                time_df = time_df.sort_values('Fecha')
                
                fig = px.line(
                    time_df, 
                    x='Fecha', 
                    y='Participantes',
                    markers=True,
                    title='Número de Participantes por Fecha'
                )
                fig.update_layout(xaxis_title='Fecha', yaxis_title='Número de Participantes')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No hay datos de participación a lo largo del tiempo")
            
            # 5. Top participating agents
            st.subheader("Agentes con Mayor Participación")
            
            agent_participation = filtered_participants_df['agent_nip'].value_counts().reset_index()
            agent_participation.columns = ['NIP', 'Participaciones']
            
            if not agent_participation.empty:
                # Get agent names
                agent_participation['Nombre'] = agent_participation['NIP'].apply(utils.get_agent_name)
                
                # Display top 10
                top_agents = agent_participation.head(10)
                
                fig = px.bar(
                    top_agents, 
                    x='Nombre', 
                    y='Participaciones',
                    color='Participaciones',
                    color_continuous_scale='Reds',
                    title='Top 10 Agentes con Mayor Participación'
                )
                fig.update_layout(xaxis_title='Agente', yaxis_title='Número de Participaciones')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No hay datos de participación por agente")
            
            # 6. Course popularity
            if not courses_df.empty:
                st.subheader("Popularidad de Cursos")
                
                # Join activity data with course data
                activities_with_courses = activities_df.copy()
                
                # Create a dictionary for course lookup
                course_dict = {course['id']: course['nombre'] for _, course in courses_df.iterrows()}
                
                # Add course name to activities
                activities_with_courses['curso_nombre'] = activities_with_courses['curso_id'].apply(
                    lambda x: course_dict.get(x, "Sin curso") if x else "Sin curso"
                )
                
                # Count participants by course
                course_participation = []
                for _, activity in activities_with_courses.iterrows():
                    activity_id = activity['id']
                    course_name = activity['curso_nombre']
                    
                    # Count participants for this activity (filtered by our criteria)
                    participants_count = len(filtered_participants_df[filtered_participants_df['activity_id'] == activity_id])
                    
                    course_participation.append({
                        'Curso': course_name,
                        'Participantes': participants_count
                    })
                
                course_df = pd.DataFrame(course_participation)
                course_summary = course_df.groupby('Curso')['Participantes'].sum().reset_index()
                
                if not course_summary.empty:
                    # Sort by participation count
                    course_summary = course_summary.sort_values('Participantes', ascending=False)
                    
                    fig = px.bar(
                        course_summary, 
                        x='Curso', 
                        y='Participantes',
                        color='Participantes',
                        color_continuous_scale='Purples',
                        title='Participación por Curso'
                    )
                    fig.update_layout(xaxis_title='Curso', yaxis_title='Número de Participantes')
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No hay datos de participación por curso")
            
            # Mostrar vistas dinámicas si estamos en modo personalizado
            if st.session_state.view_mode == "custom":
                # Crear un DataFrame unificado con todos los datos para las vistas personalizadas
                unified_data = []
                
                # Preparar dataset para visualización
                for _, activity in activities_df.iterrows():
                    activity_id = activity['id']
                    activity_date = activity['fecha']
                    activity_shift = activity['turno']
                    
                    # Obtener nombre del curso
                    course_name = "Sin curso"
                    if activity['curso_id'] and not courses_df.empty:
                        course_data = courses_df[courses_df['id'] == activity['curso_id']]
                        if not course_data.empty:
                            course_name = course_data.iloc[0]['nombre']
                    
                    # Obtener nombre del monitor
                    monitor_name = "Sin monitor"
                    if activity['monitor_nip']:
                        monitor_name = utils.get_agent_name(activity['monitor_nip'])
                    
                    # Obtener participantes para esta actividad
                    activity_participants = filtered_participants_df[filtered_participants_df['activity_id'] == activity_id]
                    
                    if not activity_participants.empty:
                        for _, participant in activity_participants.iterrows():
                            agent_nip = participant['agent_nip']
                            agent_name = utils.get_agent_name(agent_nip)
                            
                            # Obtener sección y grupo del agente
                            agent_data = agents_df[agents_df['nip'] == agent_nip]
                            section = agent_data.iloc[0]['seccion'] if not agent_data.empty else "Sin sección"
                            group = agent_data.iloc[0]['grupo'] if not agent_data.empty else "Sin grupo"
                            
                            unified_data.append({
                                'fecha': activity_date,
                                'turno': activity_shift,
                                'curso': course_name,
                                'monitor': monitor_name,
                                'nip': agent_nip,
                                'agente': agent_name,
                                'seccion': section,
                                'grupo': group
                            })
                
                unified_df = pd.DataFrame(unified_data)
                
                if not unified_df.empty:
                    # Mostrar la vista personalizada seleccionada
                    view_config = st.session_state.saved_views[st.session_state.selected_view]
                    
                    st.subheader(view_config["name"])
                    if view_config["description"]:
                        st.caption(view_config["description"])
                    
                    # Extraer configuración
                    x_axis = view_config["x_axis"]
                    y_axis = view_config["y_axis"]
                    view_type = view_config["view_type"]
                    limit = view_config.get("limit", None)
                    
                    # Preparar datos según configuración
                    if x_axis == "fecha":
                        unified_df['fecha'] = pd.to_datetime(unified_df['fecha'])
                    
                    # Preparar datos para la vista
                    if y_axis == "count":
                        # Si el eje Y es "count", agrupar por el eje X y contar
                        if x_axis in unified_df.columns:
                            plot_data = unified_df[x_axis].value_counts().reset_index()
                            plot_data.columns = [x_axis, 'count']
                            
                            # Ordenar de mayor a menor
                            plot_data = plot_data.sort_values('count', ascending=False)
                            
                            # Aplicar límite si existe
                            if limit and limit > 0:
                                plot_data = plot_data.head(limit)
                                
                            # Renombrar columnas para visualización
                            name_mapping = {
                                'seccion': 'Sección',
                                'grupo': 'Grupo',
                                'agente': 'Agente',
                                'fecha': 'Fecha',
                                'curso': 'Curso',
                                'count': 'Cantidad'
                            }
                            
                            # Crear el gráfico según el tipo seleccionado
                            if view_type == "bar":
                                fig = px.bar(
                                    plot_data, 
                                    x=x_axis, 
                                    y='count',
                                    labels={
                                        x_axis: name_mapping.get(x_axis, x_axis.capitalize()),
                                        'count': 'Cantidad'
                                    },
                                    color='count',
                                    color_continuous_scale='Viridis'
                                )
                                st.plotly_chart(fig, use_container_width=True)
                                
                            elif view_type == "pie":
                                fig = px.pie(
                                    plot_data, 
                                    names=x_axis, 
                                    values='count',
                                    title=f'Distribución por {name_mapping.get(x_axis, x_axis.capitalize())}'
                                )
                                st.plotly_chart(fig, use_container_width=True)
                                
                            elif view_type == "line" and x_axis == "fecha":
                                # Para gráficos de línea con fechas, asegurarse de ordenar por fecha
                                plot_data = plot_data.sort_values('fecha')
                                fig = px.line(
                                    plot_data, 
                                    x='fecha', 
                                    y='count',
                                    markers=True,
                                    labels={
                                        'fecha': 'Fecha',
                                        'count': 'Cantidad'
                                    }
                                )
                                st.plotly_chart(fig, use_container_width=True)
                                
                            elif view_type == "scatter":
                                fig = px.scatter(
                                    plot_data, 
                                    x=x_axis, 
                                    y='count',
                                    size='count',
                                    color='count',
                                    labels={
                                        x_axis: name_mapping.get(x_axis, x_axis.capitalize()),
                                        'count': 'Cantidad'
                                    }
                                )
                                st.plotly_chart(fig, use_container_width=True)
                            
                            # Mostrar datos en formato tabla
                            with st.expander("Ver datos", expanded=False):
                                # Renombrar columnas para visualización
                                display_df = plot_data.copy()
                                display_df.columns = [name_mapping.get(col, col.capitalize()) for col in display_df.columns]
                                st.dataframe(display_df, use_container_width=True)
                        else:
                            st.warning(f"No se encontró la columna '{x_axis}' en los datos")
                    else:
                        st.warning("La configuración actual de ejes no es compatible. Solo se soporta 'count' para el eje Y en esta versión.")
                else:
                    st.warning("No hay datos disponibles para la visualización personalizada")
            
            # 7. Data table for detailed view
            if st.session_state.view_mode == "dashboard":
                st.subheader("Datos Detallados")
                
                show_data = st.checkbox("Mostrar datos completos", False)
                
                if show_data:
                    # Create a detailed dataframe
                    detailed_data = []
                    
                    for _, activity in activities_df.iterrows():
                        activity_id = activity['id']
                        activity_date = utils.format_date(activity['fecha'])
                        activity_shift = activity['turno']
                        
                        # Get course name
                        course_name = "Sin curso"
                        if activity['curso_id'] and not courses_df.empty:
                            course_data = courses_df[courses_df['id'] == activity['curso_id']]
                            if not course_data.empty:
                                course_name = course_data.iloc[0]['nombre']
                        
                        # Get monitor name
                        monitor_name = "Sin monitor"
                        if activity['monitor_nip']:
                            monitor_name = utils.get_agent_name(activity['monitor_nip'])
                        
                        # Get participants for this activity
                        activity_participants = filtered_participants_df[filtered_participants_df['activity_id'] == activity_id]
                        
                        if not activity_participants.empty:
                            for _, participant in activity_participants.iterrows():
                                agent_nip = participant['agent_nip']
                                agent_name = utils.get_agent_name(agent_nip)
                                
                                # Get agent section and group
                                agent_data = agents_df[agents_df['nip'] == agent_nip]
                                section = agent_data.iloc[0]['seccion'] if not agent_data.empty else ""
                                group = agent_data.iloc[0]['grupo'] if not agent_data.empty else ""
                                
                                detailed_data.append({
                                    'Fecha': activity_date,
                                    'Turno': activity_shift,
                                    'Curso': course_name,
                                    'Monitor': monitor_name,
                                    'NIP': agent_nip,
                                    'Agente': agent_name,
                                    'Sección': section,
                                    'Grupo': group
                                })
                    
                    detailed_df = pd.DataFrame(detailed_data)
                    
                    if not detailed_df.empty:
                        st.dataframe(detailed_df, use_container_width=True)
                    else:
                        st.info("No hay datos detallados disponibles")
            
        else:
            st.warning("No hay datos de participación que cumplan con los filtros seleccionados")
    
    except Exception as e:
        st.error(f"Error al cargar los datos: {str(e)}")
        st.exception(e)  # Mostrar detalles de la excepción para depuración

# Run the main function
show_statistics()
