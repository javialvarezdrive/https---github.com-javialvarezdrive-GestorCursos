import config
import streamlit as st
import pandas as pd

def initialize_database():
    """
    Inicializa la base de datos con datos de prueba.
    Crea un agente y un usuario asociado para probar el inicio de sesión.
    """
    try:
        print("Inicializando base de datos con datos de prueba...")
        
        # Verificar conexión a Supabase
        print(f"Conectando a Supabase: {config.SUPABASE_URL[:20]}...")
        
        # 1. Crear un agente de prueba si no existe
        test_nip = "12345"
        
        # Verificar si el agente ya existe
        response = config.supabase.table(config.AGENTS_TABLE).select("*").eq("nip", test_nip).execute()
        
        if not response.data:
            print(f"Agente de prueba con NIP {test_nip} no encontrado. Creando...")
            
            # Datos del agente de prueba
            agent_data = {
                "nip": test_nip,
                "nombre": "Agente",
                "apellido1": "De",
                "apellido2": "Prueba",
                "email": "agente@policialocal.test",
                "telefono": "666666666",
                "seccion": "Seguridad",
                "grupo": "G-1",
                "activo": True,
                "monitor": True
            }
            
            # Insertar el agente en la tabla
            config.supabase.table(config.AGENTS_TABLE).insert(agent_data).execute()
            print("Agente de prueba creado con éxito.")
        else:
            print(f"Agente de prueba con NIP {test_nip} ya existe.")
            
        # 2. Crear un usuario asociado al agente si no existe
        response = config.supabase.table(config.USERS_TABLE).select("*").eq("agent_nip", test_nip).execute()
        
        if not response.data:
            print(f"Usuario para agente con NIP {test_nip} no encontrado. Creando...")
            
            # Datos del usuario de prueba
            user_data = {
                "agent_nip": test_nip,
                "password": "12345",  # En un caso real, esta contraseña debería estar hasheada
                "name": "Agente De Prueba"  # Nombre completo del agente
            }
            
            # Insertar el usuario en la tabla
            config.supabase.table(config.USERS_TABLE).insert(user_data).execute()
            print("Usuario de prueba creado con éxito.")
        else:
            print(f"Usuario para agente con NIP {test_nip} ya existe.")
            
        print("Inicialización de base de datos completada.")
        return True, "Base de datos inicializada correctamente."
        
    except Exception as e:
        error_msg = f"Error al inicializar la base de datos: {str(e)}"
        print(error_msg)
        return False, error_msg

if __name__ == "__main__":
    success, message = initialize_database()
    print(message)