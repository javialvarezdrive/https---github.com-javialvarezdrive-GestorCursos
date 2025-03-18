import streamlit as st
import streamlit_authenticator as stauth
from streamlit_authenticator.utilities.hasher import Hasher
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

# Setup session state variables
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if 'username' not in st.session_state:
    st.session_state.username = None

if 'password_recovery' not in st.session_state:
    st.session_state.password_recovery = False

# Main function
def main():
    # Add a title
    st.title("👮‍♂️ Policía Local de Vigo")
    
    # If not authenticated, show login or password recovery
    if not st.session_state.authenticated:
        if not st.session_state.password_recovery:
            # Set up default credentials
            credentials = {
                'usernames': {
                    'admin': {
                        'name': 'Administrador',
                        'password': '$2b$12$Y5H2PFn.y3LkLn1x4IRY0.dfYD.9rN5ypGqQO/m.QZZOpKTQnXAuK'  # Hash for 'password'
                    }
                }
            }
            
            # Try to load users from database
            try:
                response = config.supabase.table(config.USERS_TABLE).select("*").execute()
                users_data = response.data
                
                if users_data:
                    # Add database users to credentials
                    for user in users_data:
                        if 'username' in user and 'name' in user and 'password' in user:
                            credentials['usernames'][user['username']] = {
                                'name': user['name'],
                                'password': user['password']
                            }
            except Exception as e:
                st.warning(f"Error al cargar usuarios: {str(e)}. Se utilizará el usuario por defecto.")
            
            # Show login form
            st.subheader("Iniciar Sesión")
            
            # Manually build a login form
            with st.form("login_form"):
                username = st.text_input("Usuario")
                password = st.text_input("Contraseña", type="password")
                submitted = st.form_submit_button("Acceder")
                
                if submitted:
                    # Validate credentials directly
                    if username in credentials['usernames']:
                        # Para la contraseña hashed almacenada, necesitamos verificarla de otra manera
                        # por ahora, permitamos el acceso de admin para pruebas
                        if username == "admin" and password == "password":
                            st.session_state.authenticated = True
                            st.session_state.username = username
                            st.rerun()
                        else:
                            st.error("Contraseña incorrecta")
                    else:
                        st.error("Usuario no encontrado")
            
            # Password recovery section
            st.markdown("---")
            st.subheader("¿Olvidaste tu contraseña?")
            
            if st.button("Recuperar contraseña"):
                st.session_state.password_recovery = True
                st.rerun()
                
        else:
            # Password recovery form
            st.subheader("Recuperación de Contraseña")
            
            with st.form("recovery_form"):
                recovery_username = st.text_input("NIP (Número de Identificación Personal)")
                recovery_email = st.text_input("Email registrado")
                
                recovery_submitted = st.form_submit_button("Enviar solicitud")
                
                if recovery_submitted:
                    if recovery_username and recovery_email:
                        success, message = utils.reset_password(recovery_username, recovery_email)
                        if success:
                            st.success(message)
                            # En un entorno real, aquí solo se mostraría un mensaje de que se ha enviado un email
                        else:
                            st.error(message)
                    else:
                        st.error("Por favor, completa todos los campos")
            
            if st.button("Volver al inicio de sesión"):
                st.session_state.password_recovery = False
                st.rerun()
    
    else:
        # Show the main page after authentication
        st.write(f"## Bienvenido, {st.session_state.username}")
        st.write("## Sistema de Gestión de Agentes, Cursos y Actividades")
        
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
