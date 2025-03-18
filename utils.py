import streamlit as st
import pandas as pd
from datetime import datetime
import config
import random
import string
import os
import json
import base64

# Constantes para la gestión de sesión Supabase
SESSION_FILE = '.streamlit/saved_session.json'

# --- Funciones para manejo de sesión con Supabase ---
def init_session_state_supabase():
    """
    Inicializa las variables de estado de sesión para Supabase
    """
    if 'supabase_session' not in st.session_state:
        st.session_state['supabase_session'] = None
    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False
    if 'user_nip' not in st.session_state:
        st.session_state['user_nip'] = None
    if 'user_data' not in st.session_state:
        st.session_state['user_data'] = None
    if 'agent_name' not in st.session_state:
        st.session_state['agent_name'] = None
    if 'session_id' not in st.session_state:
        import time
        st.session_state['session_id'] = str(int(time.time()))

def set_supabase_session_from_state():
    """
    Establece la sesión de Supabase desde session_state
    """
    if st.session_state.get('supabase_session'):
        try:
            # Intentar restablecer la sesión en el cliente de Supabase
            config.supabase.auth.set_session(st.session_state['supabase_session'])
            return True
        except Exception as e:
            # Si hay algún error (token expirado, etc.), limpiar la sesión
            st.warning(f"La sesión ha expirado: {str(e)}")
            clear_supabase_session()
            return False
    return False

def sign_in_with_nip(nip, password):
    """
    Inicia sesión con NIP y contraseña usando la API de Supabase
    
    En lugar de usar email/password estándar, usamos una tabla personalizada
    para la autenticación con NIP (ID del agente)
    """
    try:
        # Verificar credenciales contra tabla users personalizada
        user = get_user_by_nip(nip)
        if not user:
            return False, "Agente no encontrado"
            
        # Verificar la contraseña
        if user.get('password') == password:
            # Crear una sesión de Supabase usando el sistema de autorización personalizado
            # Esta sesión se almacena en session_state
            import time
            session_data = {
                'access_token': f'custom_token_{nip}_{int(time.time())}',
                'token_type': 'bearer',
                'expires_in': 3600,
                'refresh_token': f'refresh_{nip}_{int(time.time())}',
                'user': {
                    'id': nip,
                    'app_metadata': {
                        'provider': 'custom',
                        'providers': ['custom']
                    },
                    'user_metadata': {
                        'nip': nip,
                        'name': get_agent_name(nip)
                    },
                    'aud': 'authenticated',
                    'role': 'authenticated'
                }
            }
            
            # Guardar la sesión en session_state
            st.session_state['supabase_session'] = session_data
            st.session_state['authenticated'] = True
            st.session_state['user_nip'] = nip
            st.session_state['user_data'] = user
            
            # Obtener nombre del agente
            try:
                agent_name = get_agent_name(nip)
                if agent_name != "Agente no encontrado" and agent_name != "Error":
                    st.session_state.agent_name = agent_name
                else:
                    st.session_state.agent_name = f"Agente {nip}"
            except:
                st.session_state.agent_name = f"Agente {nip}"
            
            # Generar un nuevo ID de sesión
            import time
            st.session_state.session_id = str(int(time.time()))
            
            return True, user
        else:
            return False, "Contraseña incorrecta"
    except Exception as e:
        st.error(f"Error al verificar credenciales: {str(e)}")
        return False, "Error de autenticación"

def clear_supabase_session():
    """
    Cierra la sesión de Supabase y limpia session_state
    """
    # Limpiar cliente de Supabase
    try:
        config.supabase.auth.sign_out()
    except:
        pass
    
    # Limpiar variables de sesión
    st.session_state['supabase_session'] = None
    st.session_state['authenticated'] = False
    st.session_state['user_nip'] = None
    st.session_state['user_data'] = None
    st.session_state['agent_name'] = None
    
    # Mensaje informativo
    st.success("Sesión cerrada correctamente")

def check_supabase_auth():
    """
    Verifica si hay una sesión activa y válida
    Devuelve True si está autenticado, False si no
    """
    # Inicializar variables de session_state si no existen
    init_session_state_supabase()
    
    # Si ya está autenticado, verificar que la sesión siga siendo válida
    if st.session_state.get('authenticated') and st.session_state.get('user_nip'):
        # Verificar que el cliente de Supabase tenga la sesión establecida
        if not set_supabase_session_from_state():
            # Si no se pudo establecer la sesión, verificar con la tabla users
            try:
                user = get_user_by_nip(st.session_state.get('user_nip'))
                if user:
                    # La sesión sigue siendo válida
                    return True
                else:
                    # La sesión ya no es válida
                    clear_supabase_session()
                    return False
            except:
                # Error al verificar, limpiar sesión
                clear_supabase_session()
                return False
        return True
    
    # No hay sesión activa
    return False

def save_credentials(nip, password, remember=False):
    """Guarda las credenciales en un archivo JSON y cookies si remember=True"""
    if not remember:
        # Si no se quiere recordar, borrar cualquier sesión guardada
        clear_saved_credentials()
        return False
    
    try:
        # Datos a guardar
        import time
        import json
        import base64
        
        # Simple "encriptación" básica (base64)
        # En un entorno real deberíamos usar encriptación más fuerte
        encoded_password = base64.b64encode(password.encode()).decode()
        
        # Crear directorio .streamlit si no existe
        os.makedirs(".streamlit", exist_ok=True)
        
        data = {
            'nip': nip,
            'password': encoded_password,
            'timestamp': int(time.time())
        }
        
        # Guardar en archivo JSON
        with open(SESSION_FILE, 'w') as f:
            json.dump(data, f)
            
        # Guardar en cookies del navegador
        # Crear un token para el navegador
        cookie_data = {
            'nip': nip,
            'pwd': encoded_password, 
            'ts': int(time.time())
        }
        
        # Convertir a JSON y codificar en base64
        cookie_token = base64.b64encode(json.dumps(cookie_data).encode()).decode()
        
        # Generar script JavaScript para establecer la cookie
        js = f"""
        <script>
        try {{
            // Establecer cookie con 30 días de duración
            const days = 30;
            const date = new Date();
            date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
            const expires = "; expires=" + date.toUTCString();
            
            document.cookie = "{COOKIE_NAME}=" + '{cookie_token}' + expires + "; path=/; SameSite=Strict";
            console.log('Cookie de sesión guardada');
            
            // También guardar en localStorage como respaldo
            localStorage.setItem('{COOKIE_NAME}', '{cookie_token}');
            localStorage.setItem('auth_token', '{cookie_token}');
            console.log('Datos guardados en localStorage');
        }} catch (e) {{
            console.error('Error guardando en navegador:', e);
        }}
        </script>
        """
        st.markdown(js, unsafe_allow_html=True)
            
        st.success("Sesión guardada. La próxima vez iniciarás sesión automáticamente.")
        return True
    except Exception as e:
        st.error(f"Error guardando credenciales: {str(e)}")
        return False

def load_credentials():
    """Carga credenciales desde archivo JSON o cookies si existen"""
    # Variable para almacenar los datos de credenciales
    creds_data = None
    
    # Primero intentar cargar desde el archivo
    if os.path.exists(SESSION_FILE):
        try:
            # Leer datos del archivo JSON
            import json
            import base64
            
            with open(SESSION_FILE, 'r') as f:
                data = json.load(f)
            
            # Decodificar la contraseña
            if 'password' in data:
                data['password'] = base64.b64decode(data['password'].encode()).decode()
            
            creds_data = data
        except Exception as e:
            st.error(f"Error cargando credenciales desde archivo: {str(e)}")
            if os.path.exists(SESSION_FILE):
                os.remove(SESSION_FILE)  # Borrar archivo corrupto
    
    # Si no se pudo cargar desde archivo o no existe, intentar desde cookies/localStorage
    if not creds_data:
        # Generar un código HTML oculto para recuperar la cookie y luego procesarla
        # Esto será procesado en la función que llame a load_session_from_cookie
        load_session_from_cookie()
    
    return creds_data

def clear_saved_credentials():
    """Elimina las credenciales guardadas"""
    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)
        return True
    return False

# Clave para las cookies del navegador (para acceder desde JavaScript)
COOKIE_NAME = 'vigo_police_session'

def save_session_to_cookie():
    """
    Guarda la información de sesión en cookies y localStorage para persistencia
    """
    if st.session_state.get("authenticated", False):
        import json
        import time
        import base64
        
        # Token persistente que contiene NIP y timestamp
        session_data = {
            "user_nip": st.session_state.get("user_nip"),
            "timestamp": int(time.time()),
            "session_id": st.session_state.get("session_id", str(int(time.time())))
        }
        
        # Convertir los datos a una cadena JSON y luego codificar en base64
        session_token = base64.b64encode(json.dumps(session_data).encode()).decode()
        
        # Usar cookies y localStorage con JavaScript para asegurar persistencia
        js = f"""
        <script>
        try {{
            // Guardar en localStorage - manera más directa
            localStorage.setItem('vigo_police_session', '{session_token}');
            
            // Guardar en localStorage (respaldo)
            localStorage.setItem('auth_token', '{session_token}');
            
            // Establecer cookie con 30 días de duración
            const date = new Date();
            date.setTime(date.getTime() + (30 * 24 * 60 * 60 * 1000));
            const expires = "; expires=" + date.toUTCString();
            document.cookie = "vigo_police_session={session_token}" + expires + "; path=/; SameSite=Strict";
            
            // Más simple: guardar el NIP directamente para persistencia
            localStorage.setItem('user_nip', '{st.session_state.get("user_nip")}');
            sessionStorage.setItem('user_nip', '{st.session_state.get("user_nip")}');
            
            console.log('Sesión guardada en localStorage, sessionStorage y cookies');
            alert("Sesión guardada correctamente. Se mantendrá activa cuando vuelvas.");
        }} catch (e) {{
            console.error('Error guardando sesión:', e);
            alert("Error al guardar la sesión: " + e.message);
        }}
        </script>
        """
        st.markdown(js, unsafe_allow_html=True)

def load_session_from_cookie():
    """
    Enfoque mejorado: buscar el token en cookies y localStorage 
    y usarlo en la aplicación
    """
    # Crear y ejecutar JavaScript para extraer el token
    js_code = """
    <script>
    // Función para obtener una cookie por nombre
    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    }
    
    // Función que se ejecuta al inicio
    (function() {
        try {
            // Buscar primero en cookies
            let authToken = getCookie('vigo_police_session');
            
            // Si no está en cookies, buscar en localStorage
            if (!authToken) {
                authToken = localStorage.getItem('vigo_police_session');
                console.log('Token no encontrado en cookies, usando localStorage (vigo_police_session)');
            }
            
            // Si aún no lo encontramos, buscar en el otro nombre de localStorage
            if (!authToken) {
                authToken = localStorage.getItem('auth_token');
                console.log('Token no encontrado, usando localStorage (auth_token)');
            }
            
            // Si existe un token en cualquiera de los lugares
            if (authToken) {
                console.log('Token de sesión encontrado: ' + authToken.substring(0, 10) + '...');
                
                // Obtener/crear el campo oculto para el token
                let inputField = document.getElementById('token-input');
                
                // Si no existe, crearlo
                if (!inputField) {
                    inputField = document.createElement('input');
                    inputField.type = 'hidden';
                    inputField.id = 'token-input';
                    document.body.appendChild(inputField);
                    console.log('Creado nuevo campo para el token');
                }
                
                // Establecer el valor
                inputField.value = authToken;
                
                // Crear un elemento para activar Streamlit
                const eventTrigger = document.createElement('button');
                eventTrigger.id = 'auth-token-submit';
                eventTrigger.innerText = 'Submit Token';
                eventTrigger.style.display = 'none';
                document.body.appendChild(eventTrigger);
                
                // Configurar un listener para cuando el DOM esté completamente cargado
                document.addEventListener('DOMContentLoaded', function() {
                    console.log('DOM cargado, activando token');
                    // Asegurarnos que Streamlit está listo antes de disparar
                    setTimeout(() => {
                        // Simular un evento de cambio en el campo
                        const event = new Event('change', { bubbles: true });
                        inputField.dispatchEvent(event);
                        
                        // Hacer clic en el botón para activar
                        eventTrigger.click();
                        console.log('Eventos disparados para token');
                    }, 1000);
                });
                
                // Si el DOM ya está cargado, activar ahora
                if (document.readyState === 'complete' || document.readyState === 'interactive') {
                    console.log('DOM ya cargado, activando token inmediatamente');
                    setTimeout(() => {
                        // Simular un evento de cambio en el campo
                        const event = new Event('change', { bubbles: true });
                        inputField.dispatchEvent(event);
                        
                        // Hacer clic en el botón para activar
                        eventTrigger.click();
                        console.log('Eventos disparados para token inmediatamente');
                    }, 500);
                }
            } else {
                console.log('No hay token de sesión guardado');
            }
        } catch (e) {
            console.error('Error accediendo a datos de sesión:', e);
        }
    })();
    </script>
    <div id="token-container"></div>
    <input type="hidden" id="token-input" name="token-input" />
    """
    st.markdown(js_code, unsafe_allow_html=True)
    
    # Agregar componente para capturar el valor del token
    components = """
    <script>
    // Función para enviar token a Streamlit
    const sendTokenToStreamlit = () => {
        const tokenInput = document.getElementById('token-input');
        if (tokenInput && tokenInput.value) {
            // Esto permitirá a Streamlit obtener el valor
            window.parent.postMessage({
                type: "streamlit:setComponentValue",
                value: tokenInput.value
            }, "*");
            console.log('Token enviado a Streamlit');
        }
    };
    
    // Ejecutar cuando el DOM esté listo
    if (document.readyState === 'complete' || document.readyState === 'interactive') {
        setTimeout(sendTokenToStreamlit, 1000);
    } else {
        document.addEventListener('DOMContentLoaded', function() {
            setTimeout(sendTokenToStreamlit, 1000);
        });
    }
    </script>
    """
    st.components.v1.html(components, height=0)
    
    # Este método se mejorará en otras partes del código
    # para detectar el token y autenticar automáticamente
    return False

def clear_session_cookie():
    """
    Elimina la sesión de localStorage y cookies
    """
    # Usar JavaScript para eliminar todas las formas de almacenamiento
    js = """
    <script>
    try {
        // Eliminar todas las formas de almacenamiento
        localStorage.removeItem('auth_token');
        localStorage.removeItem('vigo_police_session');
        localStorage.removeItem('user_nip');
        sessionStorage.removeItem('user_nip');
        
        // Eliminar cookie estableciendo una fecha pasada
        document.cookie = "vigo_police_session=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; SameSite=Strict";
        
        console.log('Sesión eliminada de localStorage, sessionStorage y cookies');
        alert('Sesión cerrada correctamente');
    } catch (e) {
        console.error('Error al eliminar datos de sesión:', e);
    }
    </script>
    """
    st.markdown(js, unsafe_allow_html=True)
    
    # Limpiar variables de sesión
    if "authenticated" in st.session_state:
        st.session_state["authenticated"] = False
    if "user_nip" in st.session_state:
        st.session_state["user_nip"] = None
    if "user_data" in st.session_state:
        st.session_state["user_data"] = None
    if "agent_name" in st.session_state:
        st.session_state["agent_name"] = None
    
    # Limpiar cualquier campo de entrada relacionado con la autenticación
    if "auth_token_input" in st.session_state:
        st.session_state["auth_token_input"] = ""
        
    # También eliminar el archivo de sesión guardado
    clear_saved_credentials()

def check_authentication():
    """
    Check if user is authenticated and ensure session state is properly initialized
    This function ensures a consistent state across all pages
    """
    # Initialize all session state variables with persistence
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    
    if "user_nip" not in st.session_state:
        st.session_state["user_nip"] = None
        
    if "user_data" not in st.session_state:
        st.session_state["user_data"] = None

    if "agent_name" not in st.session_state:
        st.session_state["agent_name"] = None
    
    # Si no está autenticado, intentamos cargar la sesión desde la cookie
    if not st.session_state.get("authenticated", False):
        load_session_from_cookie()
    
    # Check if user is authenticated and verify with Supabase
    if not st.session_state.get("authenticated", False) or not st.session_state.get("user_nip"):
        st.warning("Por favor, inicia sesión para acceder a esta página.")
        st.stop()
    else:
        # Verify session is still valid with Supabase
        try:
            user = get_user_by_nip(st.session_state["user_nip"])
            if not user:
                clear_session_cookie()
                st.warning("Sesión expirada. Por favor, inicia sesión nuevamente.")
                st.stop()
            
            # Si la sesión es válida, guardamos la cookie para futuras visitas
            save_session_to_cookie()
            
        except Exception as e:
            st.error(f"Error de autenticación: {str(e)}")
            clear_session_cookie()
            st.stop()
        
    # Make the session persistent with unique session ID
    # This method uses session state's persistence to maintain login state
    if "session_id" not in st.session_state:
        import time
        st.session_state.session_id = str(int(time.time()))

def format_date(date_str):
    """Format date to DD/MM/YYYY"""
    if isinstance(date_str, str):
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            return date_obj.strftime("%d/%m/%Y")
        except ValueError:
            return date_str
    return date_str

def format_bool(value):
    """Format boolean values to Spanish"""
    if value is True:
        return "Sí"
    elif value is False:
        return "No"
    return value

def get_all_agents(active_only=False):
    """Get all agents from database"""
    try:
        query = config.supabase.table(config.AGENTS_TABLE).select("*")
        if active_only:
            query = query.eq("activo", True)
        
        response = query.execute()
        
        if response.data:
            return pd.DataFrame(response.data)
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error al obtener los agentes: {str(e)}")
        return pd.DataFrame()

def get_all_monitors():
    """Get all monitors from database"""
    try:
        response = config.supabase.table(config.AGENTS_TABLE).select("*").eq("monitor", True).eq("activo", True).execute()
        
        if response.data:
            return pd.DataFrame(response.data)
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error al obtener los monitores: {str(e)}")
        return pd.DataFrame()

def get_all_courses(include_hidden=False):
    """Get all courses from database"""
    try:
        query = config.supabase.table(config.COURSES_TABLE).select("*")
        if not include_hidden:
            query = query.eq("ocultar", False)
        
        response = query.execute()
        
        if response.data:
            return pd.DataFrame(response.data)
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error al obtener los cursos: {str(e)}")
        return pd.DataFrame()

def get_all_activities():
    """Get all activities from database"""
    try:
        response = config.supabase.table(config.ACTIVITIES_TABLE).select("*").execute()
        
        if response.data:
            return pd.DataFrame(response.data)
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error al obtener las actividades: {str(e)}")
        return pd.DataFrame()

def get_activity_participants(activity_id):
    """Get participants for a specific activity"""
    try:
        response = config.supabase.table(config.PARTICIPANTS_TABLE).select("*").eq("activity_id", activity_id).execute()
        
        if response.data:
            return pd.DataFrame(response.data)
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error al obtener los participantes: {str(e)}")
        return pd.DataFrame()

def get_agent_name(nip):
    """Get agent's full name by NIP"""
    try:
        response = config.supabase.table(config.AGENTS_TABLE).select("nombre", "apellido1", "apellido2").eq("nip", nip).execute()
        
        if response.data:
            agent = response.data[0]
            return f"{agent['nombre']} {agent['apellido1']} {agent['apellido2']}".strip()
        return "Agente no encontrado"
    except Exception as e:
        st.error(f"Error al obtener el nombre del agente: {str(e)}")
        return "Error"

def validate_agent(nip, nombre, apellido1, email, telefono):
    """Validate agent data"""
    errors = []
    
    # NIP validation
    if not nip:
        errors.append("El NIP es obligatorio")
    elif not str(nip).isdigit():
        errors.append("El NIP debe ser un número")
    
    # Name validation
    if not nombre:
        errors.append("El nombre es obligatorio")
    
    # Last name validation
    if not apellido1:
        errors.append("El primer apellido es obligatorio")
    
    # Email validation (basic)
    if email and '@' not in email:
        errors.append("El email no es válido")
    
    # Phone validation
    if telefono and not str(telefono).isdigit():
        errors.append("El teléfono debe contener solo números")
    
    return errors

def validate_course(nombre, descripcion):
    """Validate course data"""
    errors = []
    
    # Name validation
    if not nombre:
        errors.append("El nombre del curso es obligatorio")
    
    # Description validation
    if not descripcion:
        errors.append("La descripción es obligatoria")
    
    return errors

def validate_activity(fecha, turno):
    """Validate activity data"""
    errors = []
    
    # Date validation
    if not fecha:
        errors.append("La fecha es obligatoria")
    
    # Shift validation
    if not turno:
        errors.append("El turno es obligatorio")
    
    return errors

def get_user_by_nip(nip):
    """Get user data by NIP (agent ID)"""
    try:
        response = config.supabase.table(config.USERS_TABLE).select("*").eq("agent_nip", nip).execute()
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        st.error(f"Error al obtener el usuario: {str(e)}")
        return None
        
def verify_credentials(nip, password):
    """Verify user credentials (NIP and password)"""
    try:
        user = get_user_by_nip(nip)
        if not user:
            return False, "Agente no encontrado"
            
        # Verificar la contraseña
        # En un caso real, deberíamos hashear la contraseña y compararla
        # Por simplicidad, comparamos directamente
        if user.get('password') == password:
            return True, user
        else:
            return False, "Contraseña incorrecta"
    except Exception as e:
        st.error(f"Error al verificar credenciales: {str(e)}")
        return False, "Error de autenticación"

def generate_temp_password(length=8):
    """Generate a temporary password"""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def reset_password(nip, email):
    """Reset user password and send email with new password"""
    try:
        # Verificar que existe un agente con ese NIP
        response = config.supabase.table(config.AGENTS_TABLE).select("*").eq("nip", nip).execute()
        if not response.data:
            return False, "No se encontró un agente con este NIP"
        
        # Verificar que el email coincida con el del agente
        agent = response.data[0]
        if agent.get('email') != email:
            return False, "El email no coincide con el registrado para este agente"
        
        # Verificar que el agente tiene un usuario en la tabla users
        user = get_user_by_nip(nip)
        if not user:
            return False, "No existe un usuario asociado a este agente"
            
        # Generate new password
        new_password = generate_temp_password()
        
        # Hash new password - en un caso real debería hashear la contraseña
        # Para simplificar, usamos la contraseña en texto plano por ahora
        
        # Update user password in database
        config.supabase.table(config.USERS_TABLE).update({"password": new_password}).eq("agent_nip", nip).execute()
        
        # In a real application, send an email with the new password
        # For now, just return the new password
        return True, f"Tu nueva contraseña temporal es: {new_password}"
    except Exception as e:
        return False, f"Error al restablecer la contraseña: {str(e)}"
