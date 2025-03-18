import streamlit as st

# Configuración básica de página
st.set_page_config(
    page_title="App Mínima",
    page_icon="👮‍♂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Contenido simple
st.title("Aplicación Mínima")
st.write("Esta es una versión mínima para diagnóstico")

st.success("Si puedes ver este mensaje, la aplicación está funcionando correctamente.")

# Mostrar algunos elementos básicos
option = st.selectbox(
    'Selecciona una opción',
    ('Opción 1', 'Opción 2', 'Opción 3')
)

st.write('Seleccionaste:', option)