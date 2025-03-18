import streamlit as st
import pandas as pd
import config
import utils

# Check authentication
utils.check_authentication()

# Page title
st.title("👮‍♂️ Gestión de Agentes")

# Create tabs
tab1, tab2, tab3 = st.tabs(["Ver Agentes", "Añadir Agente", "Editar Agente"])

# Tab 1: View Agents
with tab1:
    st.subheader("Lista de Agentes")
    
    # Search functionality
    search_query = st.text_input("Buscar agente (NIP, nombre, apellidos...)", "")
    
    # Get agents data
    agents_df = utils.get_all_agents()
    
    if not agents_df.empty:
        # Apply search filter if provided
        if search_query:
            search_query = search_query.lower()
            filtered_df = agents_df[
                agents_df['nip'].astype(str).str.contains(search_query) |
                agents_df['nombre'].str.lower().str.contains(search_query) |
                agents_df['apellido1'].str.lower().str.contains(search_query) |
                agents_df['apellido2'].str.lower().str.contains(search_query) |
                agents_df['email'].str.lower().str.contains(search_query) |
                agents_df['seccion'].str.lower().str.contains(search_query) |
                agents_df['grupo'].str.lower().str.contains(search_query)
            ]
        else:
            filtered_df = agents_df
        
        # Format boolean columns
        display_df = filtered_df.copy()
        display_df['activo'] = display_df['activo'].apply(utils.format_bool)
        display_df['monitor'] = display_df['monitor'].apply(utils.format_bool)
        
        # Create a new column with full name
        display_df['nombre_completo'] = display_df.apply(
            lambda x: f"{x['nombre']} {x['apellido1']} {x['apellido2']}".strip(), 
            axis=1
        )
        
        # Reorder columns for display
        columns_order = ['nip', 'nombre_completo', 'seccion', 'grupo', 'email', 
                         'telefono', 'activo', 'monitor']
        
        # Select only the columns we want to display
        display_columns = [col for col in columns_order if col in display_df.columns]
        
        # Rename columns for display
        columns_rename = {
            'nip': 'NIP',
            'nombre_completo': 'Nombre Completo',
            'seccion': 'Sección',
            'grupo': 'Grupo',
            'email': 'Email',
            'telefono': 'Teléfono',
            'activo': 'Activo',
            'monitor': 'Monitor'
        }
        
        # Display the dataframe
        st.dataframe(
            display_df[display_columns].rename(columns=columns_rename),
            use_container_width=True,
            hide_index=True
        )
        
        st.info(f"Total de agentes: {len(filtered_df)}")
    else:
        st.warning("No hay agentes disponibles en la base de datos.")

# Tab 2: Add Agent
with tab2:
    st.subheader("Añadir Nuevo Agente")
    
    # Create form
    with st.form("add_agent_form"):
        # Form fields
        col1, col2 = st.columns(2)
        
        with col1:
            nip = st.text_input("NIP *", "")
            nombre = st.text_input("Nombre *", "")
            apellido1 = st.text_input("Primer Apellido *", "")
            apellido2 = st.text_input("Segundo Apellido", "")
            email = st.text_input("Email", "")
        
        with col2:
            telefono = st.text_input("Teléfono", "")
            seccion = st.selectbox("Sección", [""] + config.SECTIONS)
            grupo = st.selectbox("Grupo", [""] + config.GROUPS)
            activo = st.checkbox("Activo", True)
            monitor = st.checkbox("Monitor", False)
        
        # Submit button
        submitted = st.form_submit_button("Añadir Agente")
        
        if submitted:
            # Validate form data
            validation_errors = utils.validate_agent(nip, nombre, apellido1, email, telefono)
            
            if validation_errors:
                for error in validation_errors:
                    st.error(error)
            else:
                # Check if NIP already exists
                try:
                    existing_agent = config.supabase.table(config.AGENTS_TABLE).select("nip").eq("nip", nip).execute()
                    
                    if existing_agent.data:
                        st.error(f"Ya existe un agente con el NIP {nip}")
                    else:
                        # Prepare data
                        agent_data = {
                            'nip': nip,
                            'nombre': nombre,
                            'apellido1': apellido1,
                            'apellido2': apellido2,
                            'email': email,
                            'telefono': telefono,
                            'seccion': seccion,
                            'grupo': grupo,
                            'activo': activo,
                            'monitor': monitor
                        }
                        
                        # Insert data
                        result = config.supabase.table(config.AGENTS_TABLE).insert(agent_data).execute()
                        
                        if result.data:
                            st.success(f"Agente {nombre} {apellido1} añadido correctamente")
                        else:
                            st.error("Error al añadir el agente")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

# Tab 3: Edit Agent
with tab3:
    st.subheader("Editar Agente Existente")
    
    # Get all agents for selection
    agents_df = utils.get_all_agents()
    
    if not agents_df.empty:
        # Create a dropdown to select an agent by NIP
        agents_list = []
        for _, row in agents_df.iterrows():
            agent_name = f"{row['nip']} - {row['nombre']} {row['apellido1']} {row['apellido2']}".strip()
            agents_list.append((agent_name, row['nip']))
        
        selected_agent = st.selectbox(
            "Seleccionar agente a editar",
            options=[name for name, _ in agents_list],
            format_func=lambda x: x
        )
        
        # Get the NIP of the selected agent
        selected_nip = None
        for name, nip in agents_list:
            if name == selected_agent:
                selected_nip = nip
                break
        
        if selected_nip:
            # Get agent data
            agent_data = agents_df[agents_df['nip'] == selected_nip].iloc[0].to_dict()
            
            # Create form for editing
            # Delete button outside the form
            delete_button = st.button("Eliminar Agente", type="secondary")
            
            with st.form("edit_agent_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    nip = st.text_input("NIP *", agent_data['nip'], disabled=True)
                    nombre = st.text_input("Nombre *", agent_data['nombre'])
                    apellido1 = st.text_input("Primer Apellido *", agent_data['apellido1'])
                    apellido2 = st.text_input("Segundo Apellido", agent_data['apellido2'])
                    email = st.text_input("Email", agent_data['email'])
                
                with col2:
                    telefono = st.text_input("Teléfono", agent_data['telefono'])
                    seccion = st.selectbox("Sección", [""] + config.SECTIONS, 
                                           index=0 if not agent_data['seccion'] else config.SECTIONS.index(agent_data['seccion'])+1)
                    grupo = st.selectbox("Grupo", [""] + config.GROUPS, 
                                        index=0 if not agent_data['grupo'] else config.GROUPS.index(agent_data['grupo'])+1)
                    activo = st.checkbox("Activo", agent_data['activo'])
                    monitor = st.checkbox("Monitor", agent_data['monitor'])
                
                submit_button = st.form_submit_button("Actualizar Agente")
                
                if submit_button:
                    # Validate form data
                    validation_errors = utils.validate_agent(nip, nombre, apellido1, email, telefono)
                    
                    if validation_errors:
                        for error in validation_errors:
                            st.error(error)
                    else:
                        # Prepare updated data
                        updated_data = {
                            'nombre': nombre,
                            'apellido1': apellido1,
                            'apellido2': apellido2,
                            'email': email,
                            'telefono': telefono,
                            'seccion': seccion,
                            'grupo': grupo,
                            'activo': activo,
                            'monitor': monitor
                        }
                        
                        try:
                            # Update data
                            result = config.supabase.table(config.AGENTS_TABLE).update(updated_data).eq("nip", nip).execute()
                            
                            if result.data:
                                st.success(f"Agente {nombre} {apellido1} actualizado correctamente")
                            else:
                                st.error("Error al actualizar el agente")
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
                
                if delete_button:
                    # Define key for tracking deletion confirmation for this agent
                    confirm_delete_key = f"confirm_delete_{nip}"
                    
                    # Initialize key in session state if it doesn't exist
                    if confirm_delete_key not in st.session_state:
                        st.session_state[confirm_delete_key] = False
                    
                    # Delete agent confirmation
                    st.warning(f"¿Estás seguro de que deseas eliminar al agente {nombre} {apellido1}?")
                    
                    # Create a form for confirmation buttons
                    with st.form(key=f"confirm_delete_form_{nip}", clear_on_submit=True):
                        col1, col2 = st.columns(2)
                        with col1:
                            confirm_yes = st.form_submit_button("Sí, eliminar")
                        with col2:
                            confirm_no = st.form_submit_button("No, cancelar")
                        
                        if confirm_yes:
                            try:
                                # Delete agent
                                result = config.supabase.table(config.AGENTS_TABLE).delete().eq("nip", nip).execute()
                                
                                if result.data:
                                    st.session_state[confirm_delete_key] = True
                                    st.success(f"Agente {nombre} {apellido1} eliminado correctamente")
                                    # Use a rerun flag in session state
                                    st.session_state.need_rerun = True
                                else:
                                    st.error("Error al eliminar el agente")
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
                        
                        if confirm_no:
                            st.session_state[confirm_delete_key] = False
                    
                    # Check if rerun is needed
                    if st.session_state.get("need_rerun", False):
                        st.session_state.need_rerun = False
                        st.rerun()
    else:
        st.warning("No hay agentes disponibles para editar.")
