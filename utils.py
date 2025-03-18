import streamlit as st
import pandas as pd
from datetime import datetime
import config
import random
import string

def save_session_to_cookie():
    """
    Guarda la información de sesión en una cookie para persistencia
    """
    if st.session_state.get("authenticated", False):
        # Creamos un token persistente (simplificado)
        import json
        import time
        import base64
        
        # Token persistente que contiene NIP y timestamp
        session_data = {
            "user_nip": st.session_state.get("user_nip"),
            "timestamp": int(time.time()),
            "session_id": st.session_state.get("session_id", str(int(time.time())))
        }
        
        # En una implementación real, deberíamos firmar este token
        session_token = base64.b64encode(json.dumps(session_data).encode()).decode()
        
        # Guardar el token en una cookie
        st.session_state["_persistent_token"] = session_token
        
        # Establecer la cookie via JavaScript
        js = f"""
        <script>
        localStorage.setItem('streamlit_auth_token', '{session_token}');
        console.log('Sesión guardada en localStorage');
        </script>
        """
        st.markdown(js, unsafe_allow_html=True)

def load_session_from_cookie():
    """
    Carga la información de sesión desde una cookie si existe
    """
    # Intenta cargar el token desde localStorage mediante JavaScript
    js = """
    <script>
    const token = localStorage.getItem('streamlit_auth_token');
    if (token) {
        window.parent.postMessage({
            type: "streamlit:setComponentValue",
            value: token
        }, "*");
        console.log('Token de sesión recuperado');
    }
    </script>
    """
    st.markdown(js, unsafe_allow_html=True)
    
    # Esperar el token desde el callback de JavaScript
    if "token_received" not in st.session_state:
        token_placeholder = st.empty()
        token = token_placeholder.text_input("", key="token_input", label_visibility="collapsed")
        token_placeholder.empty()
        
        if token:
            try:
                import json
                import base64
                
                # Decodificar el token
                session_data = json.loads(base64.b64decode(token).decode())
                
                # Restaurar la sesión
                st.session_state["user_nip"] = session_data.get("user_nip")
                st.session_state["session_id"] = session_data.get("session_id")
                
                # Verificar que el usuario existe en la base de datos
                user = get_user_by_nip(session_data.get("user_nip"))
                if user:
                    st.session_state["authenticated"] = True
                    st.session_state["user_data"] = user
                    
                    # Obtener el nombre del agente
                    agent_name = get_agent_name(session_data.get("user_nip"))
                    if agent_name != "Agente no encontrado" and agent_name != "Error":
                        st.session_state["agent_name"] = agent_name
                    else:
                        st.session_state["agent_name"] = f"Agente {session_data.get('user_nip')}"
                    
                    st.session_state["token_received"] = True
                    st.rerun()
            except Exception as e:
                # Si hay un error, ignoramos el token
                st.session_state["token_received"] = True
                pass

def clear_session_cookie():
    """
    Elimina la cookie de sesión
    """
    js = """
    <script>
    localStorage.removeItem('streamlit_auth_token');
    console.log('Sesión eliminada de localStorage');
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
    if "_persistent_token" in st.session_state:
        del st.session_state["_persistent_token"]
    if "token_received" in st.session_state:
        del st.session_state["token_received"]

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
