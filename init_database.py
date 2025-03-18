import config
import streamlit as st
import pandas as pd

def initialize_database():
    """
    Inicializa la base de datos con datos de prueba.
    Crea las tablas necesarias y un usuario asociado para probar el inicio de sesión.
    """
    # Crear tablas
    try:
        print("Creando tablas...")
        
        # Leer el archivo SQL
        with open('sql/functions.sql', 'r') as file:
            sql_commands = file.read()
        
        # Ejecutar los comandos SQL
        config.supabase.query(sql_commands).execute()
        print("Tablas creadas correctamente.")
    try:
        print("Inicializando base de datos con datos de prueba...")
        
        # Verificar conexión a Supabase
        print(f"Conectando a Supabase: {config.SUPABASE_URL[:20]}...")
        
        # 1. Crear un agente de prueba si no existe
        test_nip = "12345"
        test_email = "agente@policialocal.test"
        test_password = "12345"
        
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
                "email": test_email,
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
        
        # 2. Crear un usuario en auth.users si no existe
        # Primero verificamos si ya existe un usuario con el mismo email
        try:
            # Intetamos iniciar sesión para ver si existe
            login_response = config.supabase.auth.sign_in_with_password({
                "email": test_email,
                "password": test_password
            })
            print(f"Usuario para agente con NIP {test_nip} ya existe en auth.users")
        except Exception as e:
            if "Invalid login credentials" in str(e):
                # El usuario existe pero la contraseña es incorrecta
                print(f"Usuario para agente con NIP {test_nip} ya existe pero con otra contraseña.")
            else:
                # El usuario no existe, crearlo
                try:
                    print(f"Creando usuario en auth.users para agente con NIP {test_nip}...")
                    # Crear usuario en auth.users
                    signup_response = config.supabase.auth.sign_up({
                        "email": test_email,
                        "password": test_password,
                        "options": {
                            "data": {
                                "nip": test_nip,
                                "name": "Agente De Prueba"
                            }
                        }
                    })
                    print("Usuario creado con éxito en auth.users.")
                except Exception as signup_error:
                    print(f"Error al crear usuario: {str(signup_error)}")
        
        print("Inicialización de base de datos completada.")
        return True, "Base de datos inicializada correctamente."
        
    except Exception as e:
        error_msg = f"Error al inicializar la base de datos: {str(e)}"
        print(error_msg)
        return False, error_msg

if __name__ == "__main__":
    success, message = initialize_database()
    print(message)