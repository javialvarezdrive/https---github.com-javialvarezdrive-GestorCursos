import streamlit as st
import pandas as pd
import yaml
from yaml.loader import SafeLoader
import config
import utils
import time

# Configure the page
st.set_page_config(page_title=config.APP_NAME,
                   page_icon="👮‍♂️",
                   layout="wide",
                   initial_sidebar_state="expanded")


# Initialize all session state variables
def init_session_state():
    # Initialize Supabase session variables
    utils.init_session_state_supabase()

    # Variable para recargar la página después de callbacks
    if 'need_rerun' not in st.session_state:
        st.session_state.need_rerun = False

    # Additional app state variables
    if 'username' not in st.session_state:
        st.session_state.username = None

    if 'password_recovery' not in st.session_state:
        st.session_state.password_recovery = False

    # Login form fields
    if 'form_email' not in st.session_state:
        st.session_state.form_email = ""
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
    # Verificar si necesitamos recargar la página (puede ocurrir desde cualquier parte de la aplicación)
    if st.session_state.get('need_rerun', False):
        st.session_state.need_rerun = False
        st.rerun()

    # Add a title
    st.title("👮‍♂️ Gestión de Cursos y Actividades")

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
                email = st.session_state.email_input
                password = st.session_state.password_input
                remember = st.session_state.get("remember_me", False)

                # Almacenar valores en session_state para persistencia
                st.session_state.form_email = email
                st.session_state.form_password = password

                # Iniciar sesión usando directamente la API nativa de Supabase
                try:
                    response = config.supabase.auth.sign_in_with_password({
                        "email":
                        email,
                        "password":
                        password
                    })

                    # Autenticación exitosa
                    # Guardar la sesión en session_state
                    st.session_state['supabase_session'] = response.session
                    st.session_state['authenticated'] = True

                    # Obtener el NIP desde los metadatos del usuario o buscarlo en la tabla de agentes
                    user_metadata = response.user.user_metadata if hasattr(
                        response.user, 'user_metadata') else {}
                    nip = user_metadata.get('nip')

                    # Si no hay NIP en los metadatos, intentar buscarlo por email
                    if not nip:
                        try:
                            # Buscar el agente por email
                            agent_response = config.supabase.table(
                                config.AGENTS_TABLE).select("*").eq(
                                    "email", email).execute()
                            if agent_response.data:
                                nip = agent_response.data[0].get('nip')
                        except Exception as e:
                            st.error(
                                f"Error al buscar el NIP del agente: {str(e)}")

                    # Guardar NIP y datos del usuario
                    st.session_state['user_nip'] = nip
                    st.session_state['user_data'] = {
                        'id': response.user.id,
                        'email': response.user.email,
                        'nip': nip,
                        'metadata': user_metadata
                    }

                    # Nota: Ya no agregamos el componente JavaScript personalizado aquí
                    # Supabase guarda automáticamente la sesión en localStorage

                    # Obtener nombre del agente si se encontró el NIP
                    if nip:
                        try:
                            agent_name = utils.get_agent_name(nip)
                            if agent_name and agent_name != "Agente no encontrado" and agent_name != "Error":
                                st.session_state.agent_name = agent_name
                            else:
                                st.session_state.agent_name = "Usuario Autenticado"
                        except Exception as e:
                            st.session_state.agent_name = "Usuario Autenticado"
                            st.error(
                                f"Error al obtener el nombre del agente: {str(e)}"
                            )
                    else:
                        st.session_state.agent_name = "Usuario Autenticado"

                    # Generar un nuevo ID de sesión
                    import time
                    st.session_state.session_id = str(int(time.time()))

                    # Limpiar error de login
                    st.session_state.login_error = ""

                    # Si se seleccionó "Recordar sesión", guardar las credenciales
                    if remember:
                        utils.save_credentials(email, password, remember)

                    # Configuramos una bandera para recargar después del callback
                    st.session_state.need_rerun = True

                except Exception as e:
                    # Error de autenticación
                    error_message = str(e)
                    if "Invalid login credentials" in error_message:
                        st.session_state.login_error = "Credenciales incorrectas"
                    else:
                        st.session_state.login_error = f"Error de autenticación: {error_message}"

                    # Limpiar credenciales guardadas en caso de error
                    utils.clear_saved_credentials()

            # Formulario de login
            with st.form("login_form", clear_on_submit=False):
                st.text_input("Email",
                              key="email_input",
                              value=st.session_state.form_email
                              if 'form_email' in st.session_state else "")

                st.text_input("Contraseña",
                              type="password",
                              key="password_input",
                              value=st.session_state.form_password)

                st.checkbox(
                    "Recordar sesión",
                    key="remember_me",
                    value=st.session_state.get("remember_me", False),
                    help=
                    "Guarda tus credenciales para iniciar sesión automáticamente en este dispositivo"
                )

                submit_button = st.form_submit_button("Acceder",
                                                      on_click=process_login)

            # Mostrar errores de login
            if st.session_state.login_error:
                st.error(st.session_state.login_error)

            # Verificar si necesitamos recargar la página después del login exitoso
            if st.session_state.get('need_rerun', False):
                st.session_state.need_rerun = False
                st.rerun()

            # Sección de recuperación de contraseña
            st.markdown("---")
            st.subheader("¿Olvidaste tu contraseña?")

            def change_to_recovery():
                st.session_state.password_recovery = True

            if st.button("Recuperar contraseña", on_click=change_to_recovery):
                st.session_state.need_rerun = True

        else:
            # Formulario de recuperación de contraseña
            st.subheader("Recuperación de Contraseña")

            # Función para procesar la recuperación
            def process_recovery():
                email = st.session_state.email_recovery_input

                # Almacenar valores en session_state para persistencia
                st.session_state.recovery_email = email

                if email:
                    try:
                        # Usar directamente la API de Supabase para recuperación de contraseña
                        config.supabase.auth.reset_password_for_email(email)

                        # Mensaje de éxito
                        success_message = (
                            "Se ha enviado un correo con instrucciones para restablecer tu contraseña. "
                            "Por favor, revisa tu bandeja de entrada.")
                        st.session_state.recovery_message = {
                            "type": "success",
                            "text": success_message
                        }
                    except Exception as e:
                        error_message = str(e)
                        st.session_state.recovery_message = {
                            "type": "error",
                            "text": f"Error: {error_message}"
                        }
                else:
                    st.session_state.recovery_message = {
                        "type": "error",
                        "text": "Por favor, introduce tu email"
                    }

            # Formulario de recuperación
            with st.form("recovery_form", clear_on_submit=False):
                st.text_input("Email registrado",
                              key="email_recovery_input",
                              value=st.session_state.recovery_email)

                recovery_submitted = st.form_submit_button(
                    "Enviar solicitud", on_click=process_recovery)

            # Mostrar mensajes de recuperación
            if st.session_state.recovery_message["type"] == "success":
                st.success(st.session_state.recovery_message["text"])
            elif st.session_state.recovery_message["type"] == "error":
                st.error(st.session_state.recovery_message["text"])

            # Botón para volver al login
            def back_to_login():
                st.session_state.password_recovery = False
                # Limpiar datos del formulario de recuperación
                st.session_state.recovery_email = ""
                st.session_state.recovery_message = {"type": "", "text": ""}
                st.session_state.need_rerun = True

            if st.button("Volver al inicio de sesión", on_click=back_to_login):
                pass

    else:
        # Usuario autenticado - Mostrar interfaz principal
        # Sidebar para navegación
        with st.sidebar:
            # Modo claro configurado en .streamlit/config.toml
            st.markdown("### Navegación")

            # Botón de cierre de sesión
            def logout():
                # Usar el método nativo de Supabase para cerrar sesión
                utils.clear_supabase_session()
                utils.clear_saved_credentials(
                )  # Limpiar credenciales guardadas locales
                st.session_state.need_rerun = True

            if st.button("Cerrar Sesión", on_click=logout):
                pass

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
            active_agents = len(agents_df[agents_df['activo'] ==
                                          True]) if not agents_df.empty else 0
            total_agents = len(agents_df) if not agents_df.empty else 0

            with col1:
                st.metric("Agentes Activos", active_agents,
                          f"{active_agents}/{total_agents}")
        except:
            with col1:
                st.metric("Agentes Activos", "Error", "")

        # Courses count
        try:
            courses_df = utils.get_all_courses(include_hidden=True)
            visible_courses = len(courses_df[
                courses_df['ocultar'] == False]) if not courses_df.empty else 0
            total_courses = len(courses_df) if not courses_df.empty else 0

            with col2:
                st.metric("Cursos Visibles", visible_courses,
                          f"{visible_courses}/{total_courses}")
        except:
            with col2:
                st.metric("Cursos Visibles", "Error", "")

        # Activities count
        try:
            activities_df = utils.get_all_activities()
            activities_count = len(
                activities_df) if not activities_df.empty else 0

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
