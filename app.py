import streamlit as st
import streamlit_authenticator as stauth
from streamlit_authenticator.utilities.hasher import Hasher
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
    # No longer using dark mode - using theme from config.toml
    # Generate a persistent session ID
    if 'session_id' not in st.session_state:
        # Generate a unique session ID for this session
        st.session_state.session_id = str(int(time.time()))

    # Authentication variables
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

    if 'username' not in st.session_state:
        st.session_state.username = None
        
    if 'user_nip' not in st.session_state:
        st.session_state.user_nip = None
        
    if 'user_data' not in st.session_state:
        st.session_state.user_data = None
        
    if 'agent_name' not in st.session_state:
        st.session_state.agent_name = None

    if 'password_recovery' not in st.session_state:
        st.session_state.password_recovery = False
        
    # Login form fields
    if 'remember_me' not in st.session_state:
        st.session_state.remember_me = False
        
    # UI control flags
    if 'need_rerun' not in st.session_state:
        st.session_state.need_rerun = False
        
    # User role and permissions (for future use)
    if 'user_role' not in st.session_state:
        st.session_state.user_role = None

# Initialize all session state variables
init_session_state()

# Main function
def main():
    # Add a title
    st.title("👮‍♂️ Policía Local de Vigo")
    
    # Intentar autenticar con credenciales guardadas (archivo o cookies)
    if not st.session_state.get("authenticated", False):
        with st.spinner("Comprobando sesión guardada..."):
            # Primero intentamos cargar desde el archivo
            saved_credentials = utils.load_credentials()
            
            # También crear un componente oculto para recibir token de cookie
            # Este código se insertará en la página y creará un campo oculto
            st.markdown("""
            <div id="session-data-container" style="display:none;"></div>
            <input type="hidden" id="token-input" name="token" />
            """, unsafe_allow_html=True)
            
            # Componente para obtener token de cookie/localStorage
            cookie_data_js = """
            <script>
            // Función para obtener una cookie por nombre
            function getCookie(name) {
                const value = `; ${document.cookie}`;
                const parts = value.split(`; ${name}=`);
                if (parts.length === 2) return parts.pop().split(';').shift();
                return null;
            }
            
            // Intentar obtener datos de sesión
            (function() {
                try {
                    // Buscar token en diferentes formas de almacenamiento
                    let authToken = getCookie('vigo_police_session');
                    
                    if (!authToken) {
                        authToken = localStorage.getItem('vigo_police_session');
                    }
                    
                    if (!authToken) {
                        authToken = localStorage.getItem('auth_token');
                    }
                    
                    if (authToken) {
                        console.log('Token de sesión encontrado, auto-login iniciado');
                        
                        // Crear campo oculto con el token
                        const tokenInput = document.getElementById('token-input');
                        if (tokenInput) {
                            tokenInput.value = authToken;
                            
                            // Crear un botón para activar streamlit
                            const loginButton = document.createElement('button');
                            loginButton.id = 'auto-login-button';
                            loginButton.style.display = 'none';
                            loginButton.textContent = 'Auto Login';
                            document.body.appendChild(loginButton);
                            
                            // Simular clic para que Streamlit tome el valor
                            setTimeout(() => {
                                console.log('Ejecutando auto-login');
                                loginButton.click();
                            }, 500);
                        }
                    } else {
                        console.log('No hay datos de sesión guardados');
                    }
                } catch (e) {
                    console.error('Error verificando almacenamiento:', e);
                }
            })();
            </script>
            """
            st.markdown(cookie_data_js, unsafe_allow_html=True)
            
            # Procesar credenciales guardadas si existen
            if saved_credentials and 'nip' in saved_credentials and 'password' in saved_credentials:
                # Intentar iniciar sesión con las credenciales guardadas
                nip = saved_credentials['nip']
                password = saved_credentials['password']
                success, result = utils.verify_credentials(nip, password)
                if success:
                    # Autenticación exitosa
                    user = result
                    st.session_state["authenticated"] = True
                    st.session_state["user_nip"] = nip  # Guardamos el NIP como identificador
                    st.session_state["user_data"] = user  # Guardamos todos los datos del usuario
                    
                    # Obtener el nombre del agente para mostrarlo en la interfaz
                    try:
                        agent_name = utils.get_agent_name(nip)
                        if agent_name != "Agente no encontrado" and agent_name != "Error":
                            st.session_state.agent_name = agent_name
                        else:
                            st.session_state.agent_name = f"Agente {nip}"
                    except:
                        st.session_state.agent_name = f"Agente {nip}"
                    
                    # Generate a new session ID when logged in
                    st.session_state.session_id = str(int(time.time()))
                    
                    # Mensaje de éxito y recargar la página
                    st.success("Sesión restaurada automáticamente")
                    # Guardar la sesión en la cookie para persistencia web
                    utils.save_session_to_cookie()
                    st.rerun()
        
    # Intentar cargar sesión desde cookies si existe
    if not st.session_state.get("authenticated", False):
        # Componente para capturar datos desde cookies/localStorage
        utils.load_session_from_cookie()
        
        # Buscar si hay un token de cookie disponible
        if 'token-input' in st.session_state:
            try:
                token_data = st.session_state['token-input']
                if token_data:
                    # Decodificar el token
                    import json
                    import base64
                    
                    # Decodificar token de base64 a JSON
                    token_json = base64.b64decode(token_data).decode('utf-8')
                    token_obj = json.loads(token_json)
                    
                    # Extraer NIP del token
                    if 'user_nip' in token_obj:
                        # Token de sesión de usuario
                        nip = token_obj['user_nip']
                        # Intentar autenticar con el NIP encontrado
                        user = utils.get_user_by_nip(nip)
                        if user:
                            # Autenticación exitosa desde cookie
                            st.session_state["authenticated"] = True
                            st.session_state["user_nip"] = nip
                            st.session_state["user_data"] = user
                            
                            # Obtener nombre del agente
                            try:
                                agent_name = utils.get_agent_name(nip)
                                if agent_name != "Agente no encontrado" and agent_name != "Error":
                                    st.session_state.agent_name = agent_name
                                else:
                                    st.session_state.agent_name = f"Agente {nip}"
                            except:
                                st.session_state.agent_name = f"Agente {nip}"
                            
                            # Generar un nuevo ID de sesión
                            st.session_state.session_id = str(int(time.time()))
                            st.success("Sesión restaurada desde navegador")
                            st.rerun()
                    elif 'nip' in token_obj:
                        # Token de credenciales guardadas
                        nip = token_obj['nip']
                        # Si tiene contraseña codificada, decodificarla
                        if 'pwd' in token_obj:
                            encoded_pwd = token_obj['pwd']
                            pwd = base64.b64decode(encoded_pwd.encode()).decode()
                            
                            # Verificar credenciales
                            success, result = utils.verify_credentials(nip, pwd)
                            if success:
                                # Autenticación exitosa
                                user = result
                                st.session_state["authenticated"] = True
                                st.session_state["user_nip"] = nip
                                st.session_state["user_data"] = user
                                
                                # Obtener nombre del agente
                                try:
                                    agent_name = utils.get_agent_name(nip)
                                    if agent_name != "Agente no encontrado" and agent_name != "Error":
                                        st.session_state.agent_name = agent_name
                                    else:
                                        st.session_state.agent_name = f"Agente {nip}"
                                except:
                                    st.session_state.agent_name = f"Agente {nip}"
                                
                                # Generar un nuevo ID de sesión
                                st.session_state.session_id = str(int(time.time()))
                                st.success("Sesión restaurada desde navegador")
                                st.rerun()
            except Exception as e:
                st.error(f"Error al procesar token de sesión: {str(e)}")
                # Limpiar token para evitar bucles de error
                if 'token-input' in st.session_state:
                    st.session_state['token-input'] = None
        
    # If not authenticated, show login or password recovery
    if not st.session_state.get("authenticated", False):
        if not st.session_state.get("password_recovery", False):
            # Show login form
            st.subheader("Iniciar Sesión")
            
            # Use session state for form inputs to persist values
            if 'form_nip' not in st.session_state:
                st.session_state.form_nip = ""
            if 'form_password' not in st.session_state:
                st.session_state.form_password = ""
            if 'login_error' not in st.session_state:
                st.session_state.login_error = ""
            
            # Define process login function for form submit button
            def process_login():
                nip = st.session_state.nip_input
                password = st.session_state.password_input
                remember = st.session_state.get("remember_me", False)
                
                # Store form values in session state for persistence
                st.session_state.form_nip = nip
                st.session_state.form_password = password
                
                # Validate credentials using the NIP and password
                success, result = utils.verify_credentials(nip, password)
                if success:
                    # Autenticación exitosa
                    user = result
                    st.session_state["authenticated"] = True
                    st.session_state["user_nip"] = nip  # Guardamos el NIP como identificador
                    st.session_state["user_data"] = user  # Guardamos todos los datos del usuario
                    st.session_state.login_error = ""
                    
                    # Obtener el nombre del agente para mostrarlo en la interfaz
                    try:
                        agent_name = utils.get_agent_name(nip)
                        if agent_name != "Agente no encontrado" and agent_name != "Error":
                            st.session_state.agent_name = agent_name
                        else:
                            st.session_state.agent_name = f"Agente {nip}"
                    except:
                        st.session_state.agent_name = f"Agente {nip}"
                    
                    # Generate a new session ID when logged in
                    st.session_state.session_id = str(int(time.time()))
                    
                    # Guardar la sesión en la cookie para persistencia web
                    utils.save_session_to_cookie()
                    
                    # Si se seleccionó "Recordar sesión", guardar las credenciales encriptadas
                    utils.save_credentials(nip, password, remember)
                else:
                    # Error de autenticación
                    st.session_state.login_error = result
                    # Limpiar credenciales guardadas en caso de error
                    utils.clear_saved_credentials()
            
            # Manually build a login form - no on_change callbacks in form
            with st.form("login_form", clear_on_submit=False):
                st.text_input("NIP (Número de Identificación Personal)", key="nip_input", value=st.session_state.form_nip)
                st.text_input("Contraseña", type="password", key="password_input", value=st.session_state.form_password)
                st.checkbox("Recordar sesión", key="remember_me", value=st.session_state.get("remember_me", False),
                            help="Guarda tus credenciales para iniciar sesión automáticamente en este dispositivo")
                submit_button = st.form_submit_button("Acceder", on_click=process_login)
            
            # Display any login errors
            if st.session_state.login_error:
                st.error(st.session_state.login_error)
                
            # If authenticated after form submission, rerun the app
            if st.session_state.authenticated:
                st.rerun()
            
            # Password recovery section
            st.markdown("---")
            st.subheader("¿Olvidaste tu contraseña?")
            
            if st.button("Recuperar contraseña"):
                st.session_state.password_recovery = True
                st.rerun()
                
        else:
            # Password recovery form
            st.subheader("Recuperación de Contraseña")
            
            # Use session state for recovery form inputs
            if 'recovery_username' not in st.session_state:
                st.session_state.recovery_username = ""
            if 'recovery_email' not in st.session_state:
                st.session_state.recovery_email = ""
            if 'recovery_message' not in st.session_state:
                st.session_state.recovery_message = {"type": "", "text": ""}
                
            # Process recovery function - only called by form_submit_button
            def process_recovery():
                username = st.session_state.username_recovery_input
                email = st.session_state.email_recovery_input
                
                # Store form values in session state for persistence
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
            
            # Display the recovery form - no on_change callbacks in form
            with st.form("recovery_form", clear_on_submit=False):
                st.text_input("NIP (Número de Identificación Personal)", 
                             key="username_recovery_input", 
                             value=st.session_state.recovery_username)
                
                st.text_input("Email registrado", 
                             key="email_recovery_input", 
                             value=st.session_state.recovery_email)
                
                recovery_submitted = st.form_submit_button("Enviar solicitud", on_click=process_recovery)
            
            # Display recovery messages
            if st.session_state.recovery_message["type"] == "success":
                st.success(st.session_state.recovery_message["text"])
            elif st.session_state.recovery_message["type"] == "error":
                st.error(st.session_state.recovery_message["text"])
            
            # Return to login button
            if st.button("Volver al inicio de sesión"):
                st.session_state.password_recovery = False
                # Clear recovery form data
                st.session_state.recovery_username = ""
                st.session_state.recovery_email = ""
                st.session_state.recovery_message = {"type": "", "text": ""}
                st.rerun()
    
    else:
        # Sidebar para navegación
        with st.sidebar:
            # Modo claro configurado en .streamlit/config.toml
            st.markdown("### Navegación")
            
            # Botón de cierre de sesión
            if st.button("Cerrar Sesión"):
                utils.clear_session_cookie()
                utils.clear_saved_credentials()  # Limpiar credenciales guardadas
                st.session_state.clear()
                st.rerun()
            
        # Show the main page after authentication
        # Usamos el nombre del agente para la bienvenida si está disponible
        if 'agent_name' in st.session_state:
            st.write(f"## Bienvenido, {st.session_state.agent_name}")
        else:
            st.write(f"## Bienvenido, Agente {st.session_state.username}")
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
