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

# Tabs para diferentes vistas
tab1, tab2 = st.tabs(["Dashboard General", "Vista Dinámica"])

# Main function
def show_statistics():
    # Valores predeterminados para fechas
    today = datetime.now()
    start_of_year = datetime(today.year, 1, 1)
    
    # Default start and end dates
    default_start_date = start_of_year
    default_end_date = today
    
    # Parte 1: Dashboard General
    with tab1:
        st.header("Dashboard General")
        
        # Crear contenedor para filtros
        filter_container = st.container()
        
        with filter_container:
            # Filtros en columnas
            fcol1, fcol2 = st.columns(2)
            
            with fcol1:
                # Date range filter
                dash_start_date = st.date_input("Fecha inicio", default_start_date, key="dash_start_date")
                dash_end_date = st.date_input("Fecha fin", default_end_date, key="dash_end_date")
                
                # Course filter
                try:
                    courses_data = utils.get_all_courses(include_hidden=False)
                    if not courses_data.empty:
                        course_options = [("", "Todos los cursos")]
                        for _, course in courses_data.iterrows():
                            course_options.append((course['id'], course['nombre']))
                        
                        dash_selected_course = st.selectbox(
                            "Curso",
                            options=[c[0] for c in course_options],
                            format_func=lambda x: next((c[1] for c in course_options if c[0] == x), x),
                            key="dash_course"
                        )
                    else:
                        dash_selected_course = ""
                except Exception as e:
                    dash_selected_course = ""
                    st.warning(f"No se pudieron cargar los cursos: {str(e)}")
            
            with fcol2:
                # Section filter
                try:
                    agents_df = utils.get_all_agents()
                    if not agents_df.empty:
                        # Get unique sections
                        sections = sorted(agents_df['seccion'].unique().tolist())
                        sections = [s for s in sections if s]  # Remove empty values
                        
                        dash_selected_sections = st.multiselect(
                            "Secciones",
                            options=sections,
                            default=[],
                            key="dash_sections"
                        )
                    else:
                        dash_selected_sections = []
                except Exception as e:
                    dash_selected_sections = []
                    st.warning(f"No se pudieron cargar las secciones: {str(e)}")
                
                # Agents filter
                try:
                    all_agents = utils.get_all_agents()
                    if not all_agents.empty:
                        # Get agent names in format NIP - Nombre Apellido
                        agent_options = []
                        for _, agent in all_agents.iterrows():
                            agent_name = f"{agent['nip']} - {agent['nombre']} {agent['apellido1']}"
                            agent_options.append((agent['nip'], agent_name))
                        
                        # Sort by name
                        agent_options.sort(key=lambda x: x[1])
                        
                        agent_nips = [a[0] for a in agent_options]
                        agent_labels = [a[1] for a in agent_options]
                        
                        dash_selected_agents = st.multiselect(
                            "Agentes",
                            options=agent_nips,
                            default=[],
                            format_func=lambda nip: next((label for n, label in zip(agent_nips, agent_labels) if n == nip), nip),
                            key="dash_agents"
                        )
                    else:
                        dash_selected_agents = []
                except Exception as e:
                    dash_selected_agents = []
                    st.warning(f"No se pudieron cargar los agentes: {str(e)}")

        # Apply filters and load data
        try:
            # Get all activities within date range
            activities_response = config.supabase.table(config.ACTIVITIES_TABLE).select("*").gte("fecha", dash_start_date.strftime("%Y-%m-%d")).lte("fecha", dash_end_date.strftime("%Y-%m-%d")).execute()
            
            if not activities_response.data:
                st.warning("No hay actividades en el rango de fechas seleccionado")
                return
            
            activities_df = pd.DataFrame(activities_response.data)
            
            # Apply course filter if specified
            if dash_selected_course:
                activities_df = activities_df[activities_df['curso_id'] == dash_selected_course]
                if activities_df.empty:
                    st.warning("No hay actividades para el curso seleccionado en el rango de fechas")
                    return
            
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
            
            # Apply section filter to agents
            if dash_selected_sections:
                agents_df = agents_df[agents_df['seccion'].isin(dash_selected_sections)]
            
            # Apply agent filter if specified
            if dash_selected_agents:
                # Si se seleccionaron agentes específicos, filtramos solo por ellos
                agents_df = agents_df[agents_df['nip'].isin(dash_selected_agents)]
            
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
                
                # 7. Data table for detailed view
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
            st.error(f"Error al cargar los datos del dashboard: {str(e)}")
    
    # Parte 2: Vista Dinámica con DataFrames
    with tab2:
        st.header("Vista Dinámica")
        
        # Crear contenedor para filtros
        dyn_filter_container = st.container()
        
        with dyn_filter_container:
            # Filtros en columnas
            dyn_fcol1, dyn_fcol2 = st.columns(2)
            
            with dyn_fcol1:
                # Date range filter
                dyn_start_date = st.date_input("Fecha inicio", default_start_date, key="dyn_start_date")
                dyn_end_date = st.date_input("Fecha fin", default_end_date, key="dyn_end_date")
                
                # Course filter
                try:
                    dyn_courses_data = utils.get_all_courses(include_hidden=False)
                    if not dyn_courses_data.empty:
                        dyn_course_options = [("", "Todos los cursos")]
                        for _, course in dyn_courses_data.iterrows():
                            dyn_course_options.append((course['id'], course['nombre']))
                        
                        dyn_selected_course = st.selectbox(
                            "Curso",
                            options=[c[0] for c in dyn_course_options],
                            format_func=lambda x: next((c[1] for c in dyn_course_options if c[0] == x), x),
                            key="dyn_course"
                        )
                    else:
                        dyn_selected_course = ""
                except Exception as e:
                    dyn_selected_course = ""
                    st.warning(f"No se pudieron cargar los cursos: {str(e)}")
            
            with dyn_fcol2:
                # Section filter
                try:
                    dyn_agents_df = utils.get_all_agents()
                    if not dyn_agents_df.empty:
                        # Get unique sections
                        dyn_sections = sorted(dyn_agents_df['seccion'].unique().tolist())
                        dyn_sections = [s for s in dyn_sections if s]  # Remove empty values
                        
                        dyn_selected_sections = st.multiselect(
                            "Secciones",
                            options=dyn_sections,
                            default=[],
                            key="dyn_sections"
                        )
                    else:
                        dyn_selected_sections = []
                except Exception as e:
                    dyn_selected_sections = []
                    st.warning(f"No se pudieron cargar las secciones: {str(e)}")
                
                # Agents filter
                try:
                    if not dyn_agents_df.empty:
                        # Get agent names in format NIP - Nombre Apellido
                        dyn_agent_options = []
                        for _, agent in dyn_agents_df.iterrows():
                            dyn_agent_name = f"{agent['nip']} - {agent['nombre']} {agent['apellido1']}"
                            dyn_agent_options.append((agent['nip'], dyn_agent_name))
                        
                        # Sort by name
                        dyn_agent_options.sort(key=lambda x: x[1])
                        
                        dyn_agent_nips = [a[0] for a in dyn_agent_options]
                        dyn_agent_labels = [a[1] for a in dyn_agent_options]
                        
                        dyn_selected_agents = st.multiselect(
                            "Agentes",
                            options=dyn_agent_nips,
                            default=[],
                            format_func=lambda nip: next((label for n, label in zip(dyn_agent_nips, dyn_agent_labels) if n == nip), nip),
                            key="dyn_agents"
                        )
                    else:
                        dyn_selected_agents = []
                except Exception as e:
                    dyn_selected_agents = []
                    st.warning(f"No se pudieron cargar los agentes: {str(e)}")
        
        # Botón para generar el informe
        generate_report = st.button("Generar Informe", type="primary")
        
        if generate_report:
            with st.spinner("Generando informe..."):
                # Obtener los datos usando la función y los filtros
                stats_df = utils.get_agents_activity_stats(
                    start_date=dyn_start_date,
                    end_date=dyn_end_date,
                    curso_id=dyn_selected_course if dyn_selected_course else None,
                    secciones=dyn_selected_sections if dyn_selected_sections else None,
                    agentes=dyn_selected_agents if dyn_selected_agents else None
                )
                
                if not stats_df.empty:
                    # Mostrar el número total de resultados
                    st.success(f"Se encontraron {len(stats_df)} agentes que cumplen con los criterios")
                    
                    # Renombrar columnas para mejor visualización
                    stats_df = stats_df.rename(columns={
                        'nip': 'NIP',
                        'nombre': 'Nombre',
                        'apellidos': 'Apellidos',
                        'seccion': 'Sección',
                        'total_actividades': 'Total Actividades'
                    })
                    
                    # Agregar opciones de descarga
                    csv = stats_df.to_csv(index=False)
                    st.download_button(
                        label="Descargar CSV",
                        data=csv,
                        file_name="estadisticas_agentes.csv",
                        mime="text/csv"
                    )
                    
                    # Mostrar el dataframe con los datos
                    st.dataframe(stats_df, use_container_width=True)
                    
                    # Mostrar gráfico de barras con los agentes más activos (top 10)
                    if len(stats_df) > 1:  # Solo si hay más de un agente
                        st.subheader("Top Agentes por Actividades")
                        
                        # Ordenar por total de actividades
                        top_agents_df = stats_df.sort_values('Total Actividades', ascending=False).head(10)
                        
                        # Crear etiquetas para el gráfico
                        top_agents_df['Etiqueta'] = top_agents_df.apply(
                            lambda row: f"{row['NIP']} - {row['Nombre']}", axis=1
                        )
                        
                        # Crear gráfico
                        fig = px.bar(
                            top_agents_df,
                            x='Etiqueta',
                            y='Total Actividades',
                            color='Total Actividades',
                            color_continuous_scale='viridis',
                            title='Top 10 Agentes por Número de Actividades'
                        )
                        fig.update_layout(xaxis_title='Agente', yaxis_title='Número de Actividades')
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Mostrar distribución por sección si hay datos
                        if 'Sección' in stats_df.columns and stats_df['Sección'].notna().any():
                            st.subheader("Distribución por Sección")
                            
                            section_data = stats_df.groupby('Sección')['Total Actividades'].sum().reset_index()
                            
                            if not section_data.empty:
                                # Ordenar por total de actividades
                                section_data = section_data.sort_values('Total Actividades', ascending=False)
                                
                                # Crear gráfico
                                fig = px.pie(
                                    section_data,
                                    values='Total Actividades',
                                    names='Sección',
                                    title='Distribución de Actividades por Sección'
                                )
                                st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("No se encontraron datos que cumplan con los criterios seleccionados")

# Run the main function
show_statistics()