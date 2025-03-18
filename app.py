import streamlit as st
import pandas as pd
import yaml
from yaml.loader import SafeLoader
import config
import utils
import time

# Configure the page
st.set_page_config(
    page_title=config.APP_NAME,
    page_icon="👮‍♂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize all session state variables
def init_session_state():
    # Initialize Supabase session variables
    utils.init_session_state_supabase()
    
    # Additional app state variables
    if 'username' not in st.session_state:
        st.session_state.username = None
        
    if 'password_recovery' not in st.session_state:
        st.session_state.password_recovery = False
        
    # Login form fields
    if 'form_nip' not in st.session_state:
        st.session_state.form_nip = ""
    if 'form_password' not in st.session_state:
        st.session_state.form_password = ""
    if 'login_error' not in st.session_state:
        st.session_state.login_error = ""
    if 'remember_me' not in st.session_state:
        st.session_state.remember_me = False
        
    # Recovery form fields
    if 'recovery_username' not in st.session_state:
        st.session_state.recovery_username = ""
    if 'recovery_email' not in st.session_state:
        st.session_state.recovery_email = ""
    if 'recovery_message' not in st.session_state:
        st.session_state.recovery_message = {"type": "", "text": ""}

# Initialize all session state variables
init_session_state()

# Main function
def main():
    # Add a title
    st.title("👮‍♂️ Policía Local de Vigo")
    
    # Verificar si hay una sesión de Supabase activa
    is_authenticated = utils.check_supabase_auth()
    
    # Interfaz de usuario según el estado de autenticación
    if not is_authenticated:
        # Intentar recuperar sesión desde credenciales guardadas
        if not st.session_state.password_recovery:
            # Si no estamos en recuperación de contraseña, mostrar formulario de login
            st.subheader("Iniciar Sesión")
            
            # Función para procesar el login
            def process_login():
                nip = st.session_state.nip_input
                password = st.session_state.password_input
                remember = st.session_state.get("remember_me", False)
                
                # Almacenar valores en session_state para persistencia
                st.session_state.form_nip = nip
                st.session_state.form_password = password
                
                # Iniciar sesión usando el nuevo método de Supabase
                success, result = utils.sign_in_with_nip(nip, password)
                if success:
                    # Autenticación exitosa - la sesión ya se ha configurado en sign_in_with_nip
                    st.session_state.login_error = ""
                    
                    # Si se seleccionó "Recordar sesión", guardar las credenciales
                    if remember:
                        utils.save_credentials(nip, password, remember)
                    
                    # Recargar la página para mostrar la interfaz autenticada
                    st.rerun()
                else:
                    # Error de autenticación
                    st.session_state.login_error = result
                    # Limpiar credenciales guardadas en caso de error
                    utils.clear_saved_credentials()
            
            # Formulario de login
            with st.form("login_form", clear_on_submit=False):
                st.text_input("NIP (Número de Identificación Personal)", 
                             key="nip_input", 
                             value=st.session_state.form_nip)
                
                st.text_input("Contraseña", 
                             type="password", 
                             key="password_input",
                             value=st.session_state.form_password)
                
                st.checkbox("Recordar sesión", 
                           key="remember_me", 
                           value=st.session_state.get("remember_me", False),
                           help="Guarda tus credenciales para iniciar sesión automáticamente en este dispositivo")
                
                submit_button = st.form_submit_button("Acceder", on_click=process_login)
            
            # Mostrar errores de login
            if st.session_state.login_error:
                st.error(st.session_state.login_error)
            
            # Sección de recuperación de contraseña
            st.markdown("---")
            st.subheader("¿Olvidaste tu contraseña?")
            
            if st.button("Recuperar contraseña"):
                st.session_state.password_recovery = True
                st.rerun()
                
        else:
            # Formulario de recuperación de contraseña
            st.subheader("Recuperación de Contraseña")
            
            # Función para procesar la recuperación
            def process_recovery():
                username = st.session_state.username_recovery_input
                email = st.session_state.email_recovery_input
                
                # Almacenar valores en session_state para persistencia
                st.session_state.recovery_username = username
                st.session_state.recovery_email = email
                
                if username and email:
                    success, message = utils.reset_password(username, email)
                    if success:
                        st.session_state.recovery_message = {"type": "success", "text": message}
                    else:
                        st.session_state.recovery_message = {"type": "error", "text": message}
                else:
                    st.session_state.recovery_message = {"type": "error", "text": "Por favor, completa todos los campos"}
            
            # Formulario de recuperación
            with st.form("recovery_form", clear_on_submit=False):
                st.text_input("NIP (Número de Identificación Personal)", 
                             key="username_recovery_input", 
                             value=st.session_state.recovery_username)
                
                st.text_input("Email registrado", 
                             key="email_recovery_input", 
                             value=st.session_state.recovery_email)
                
                recovery_submitted = st.form_submit_button("Enviar solicitud", on_click=process_recovery)
            
            # Mostrar mensajes de recuperación
            if st.session_state.recovery_message["type"] == "success":
                st.success(st.session_state.recovery_message["text"])
            elif st.session_state.recovery_message["type"] == "error":
                st.error(st.session_state.recovery_message["text"])
            
            # Botón para volver al login
            if st.button("Volver al inicio de sesión"):
                st.session_state.password_recovery = False
                # Limpiar datos del formulario de recuperación
                st.session_state.recovery_username = ""
                st.session_state.recovery_email = ""
                st.session_state.recovery_message = {"type": "", "text": ""}
                st.rerun()
    
    else:
        # Usuario autenticado - Mostrar interfaz principal
        # Sidebar para navegación
        with st.sidebar:
            # Modo claro configurado en .streamlit/config.toml
            st.markdown("### Navegación")
            
            # Botón de cierre de sesión
            if st.button("Cerrar Sesión"):
                # Usar el método nativo de Supabase para cerrar sesión
                utils.clear_supabase_session()
                utils.clear_saved_credentials()  # Limpiar credenciales guardadas locales
                st.rerun()
        
        # Mostrar la página principal después de la autenticación
        # Usamos el nombre del agente para la bienvenida si está disponible
        if 'agent_name' in st.session_state:
            st.write(f"## Bienvenido, {st.session_state.agent_name}")
        else:
            st.write(f"## Bienvenido, Agente {st.session_state.user_nip}")
        
        st.write("## Sistema de Gestión de Agentes, Cursos y Actividades")
        
        # Información sobre la aplicación
        st.write("""
        Esta aplicación permite la gestión de Agentes, Cursos y Actividades de la Policía Local de Vigo.
        
        Utiliza la barra lateral para navegar entre las diferentes secciones:
        
        1. **Agentes**: Gestión de los agentes de la Policía Local
        2. **Cursos**: Gestión de los cursos disponibles
        3. **Actividades**: Programación y gestión de actividades
        4. **Estadísticas**: Visualización de datos y estadísticas
        """)
        
        # Mostrar algunas estadísticas básicas
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
        
        # Footer
        st.markdown("---")
        st.markdown("© 2023 Policía Local de Vigo - Sistema de Gestión")

if __name__ == "__main__":
    main()