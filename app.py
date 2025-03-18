import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
import yaml
from yaml.loader import SafeLoader
import config
import utils

# Configure the page
st.set_page_config(
    page_title=config.APP_NAME,
    page_icon="👮‍♂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Authentication function
def setup_authentication():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if 'username' not in st.session_state:
        st.session_state.username = None
    
    # Check for stored credentials
    try:
        response = config.supabase.table(config.USERS_TABLE).select("*").execute()
        users_data = response.data
        
        if not users_data:
            # If no users found, set up a default user
            st.warning("No se encontraron usuarios en la base de datos. Se utilizará un usuario por defecto.")
            credentials = {
                'usernames': {
                    'admin': {
                        'name': 'Administrador',
                        'password': '$2b$12$Y5H2PFn.y3LkLn1x4IRY0.dfYD.9rN5ypGqQO/m.QZZOpKTQnXAuK'  # Hash for 'password'
                    }
                }
            }
        else:
            # Create credentials from users in database
            credentials = {'usernames': {}}
            for user in users_data:
                credentials['usernames'][user['username']] = {
                    'name': user['name'],
                    'password': user['password']
                }
        
        # Create the authenticator object
        authenticator = stauth.Authenticate(
            credentials,
            cookie_name="vigo_police_app",
            key="vigo_police_auth",
            cookie_expiry_days=30
        )
        
        # Display login form
        fields = {"Form name": "Iniciar Sesión", "Username": "Usuario", "Password": "Contraseña", "Login": "Acceder"}
        name, authentication_status, username = authenticator.login("main", fields=fields)
        
        # Handle authentication status
        if authentication_status is False:
            st.error("Usuario o contraseña incorrectos")
        elif authentication_status is None:
            st.warning("Por favor, introduce tu usuario y contraseña")
        elif authentication_status:
            st.session_state.authenticated = True
            st.session_state.username = username
            return authenticator
        
    except Exception as e:
        st.error(f"Error de autenticación: {str(e)}")
    
    return None

# Main function
def main():
    # Add a title
    st.title("👮‍♂️ Policía Local de Vigo")
    
    # If not authenticated, show the login form
    if not st.session_state.get('authenticated', False):
        authenticator = setup_authentication()
        if authenticator:
            st.success(f"Bienvenido, {st.session_state.username}!")
            st.rerun()
    else:
        # Show the main page after authentication
        st.write("## Bienvenido al Sistema de Gestión de Agentes, Cursos y Actividades")
        
        # Show information about the app
        st.write("""
        Esta aplicación permite la gestión de Agentes, Cursos y Actividades de la Policía Local de Vigo.
        
        Utiliza la barra lateral para navegar entre las diferentes secciones:
        
        1. **Agentes**: Gestión de los agentes de la Policía Local
        2. **Cursos**: Gestión de los cursos disponibles
        3. **Actividades**: Programación y gestión de actividades
        4. **Estadísticas**: Visualización de datos y estadísticas
        """)
        
        # Display some basic statistics
        col1, col2, col3 = st.columns(3)
        
        # Agents count
        try:
            agents_df = utils.get_all_agents()
            active_agents = len(agents_df[agents_df['activo'] == True]) if not agents_df.empty else 0
            total_agents = len(agents_df) if not agents_df.empty else 0
            
            with col1:
                st.metric("Agentes Activos", active_agents, f"{active_agents}/{total_agents}")
        except:
            with col1:
                st.metric("Agentes Activos", "Error", "")
        
        # Courses count
        try:
            courses_df = utils.get_all_courses(include_hidden=True)
            visible_courses = len(courses_df[courses_df['ocultar'] == False]) if not courses_df.empty else 0
            total_courses = len(courses_df) if not courses_df.empty else 0
            
            with col2:
                st.metric("Cursos Visibles", visible_courses, f"{visible_courses}/{total_courses}")
        except:
            with col2:
                st.metric("Cursos Visibles", "Error", "")
        
        # Activities count
        try:
            activities_df = utils.get_all_activities()
            activities_count = len(activities_df) if not activities_df.empty else 0
            
            with col3:
                st.metric("Actividades Programadas", activities_count)
        except:
            with col3:
                st.metric("Actividades Programadas", "Error")
        
        # Add a footer
        st.markdown("---")
        st.markdown("© 2023 Policía Local de Vigo - Sistema de Gestión")

if __name__ == "__main__":
    main()
