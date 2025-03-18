# Aplicación de Gestión para la Policía Local de Vigo

Esta aplicación web, desarrollada con Streamlit, está diseñada para la Policía Local de Vigo para gestionar agentes, cursos, actividades y generar estadísticas e informes.

## Características principales

- **Gestión de Agentes**: Alta, baja y modificación de agentes policiales
- **Gestión de Cursos**: Administración de cursos de formación
- **Gestión de Actividades**: Programación y asignación de agentes a actividades
- **Estadísticas**: Visualización de datos estadísticos de participación
- **Generación de Informes PDF**: Reportes detallados para cada actividad

## Requisitos Técnicos

- Python 3.8 o superior
- Streamlit 1.30.0 o superior
- Supabase para la autenticación y base de datos
- Librerías adicionales especificadas en `render_requirements.txt`

## Variables de Entorno

La aplicación requiere las siguientes variables de entorno:

- `SUPABASE_URL`: URL de la instancia de Supabase
- `SUPABASE_KEY`: Clave de API de Supabase

## Instalación Local

1. Clona el repositorio
2. Instala las dependencias: `pip install -r render_requirements.txt`
3. Configura las variables de entorno SUPABASE_URL y SUPABASE_KEY
4. Ejecuta la aplicación: `streamlit run app.py`

## Despliegue en Render

1. Configura un nuevo servicio web en Render
2. Conecta este repositorio
3. Usa las siguientes configuraciones:
   - **Build Command**: `pip install -r render_requirements.txt`
   - **Start Command**: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
4. Agrega las variables de entorno necesarias (SUPABASE_URL y SUPABASE_KEY)
5. Despliega la aplicación

Alternativamente, puedes usar el archivo `render.yaml` incluido para configurar automáticamente el despliegue a través de Render Blueprints.

## Estructura de la Aplicación

- `app.py`: Punto de entrada de la aplicación
- `config.py`: Configuración general y conexión a Supabase
- `utils.py`: Funciones de utilidad y acceso a datos
- `pdf_generator.py`: Generación de informes PDF
- `pages/`: Páginas de la aplicación (Actividades, Estadísticas, Cursos, Agentes)

## Contacto

Para cualquier consulta o soporte, contacta al desarrollador.