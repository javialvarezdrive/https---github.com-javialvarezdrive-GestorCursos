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

# Custom CSS to fix container width issues and hide navigation when not authenticated
st.markdown("""
<style>
    .block-container {
        max-width: 95%;
        padding-top: 1rem;
        padding-right: 1rem;
        padding-left: 1rem;
        padding-bottom: 1rem;
    }
    .stApp > header {
        background-color: transparent;
    }
    .main .block-container {
        width: 95%;
    }
    [data-testid="stSidebarNav"] {display: none !important;}
</style>
""", unsafe_allow_html=True)

# Initialize session state variables
utils.init_session_state_supabase()

# Additional app state variables
if 'need_rerun' not in st.session_state:
    st.session_state.need_rerun = False
    
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

# Check authentication status
is_authenticated = utils.check_supabase_auth()

# Hide all pages in sidebar if not authenticated
if not is_authenticated:
    st.title("")
    st.subheader("Iniciar Sesión")

    # Login form
    with st.form("login_form", clear_on_submit=False):
        st.text_input("Email",
                     key="email_input",
                     value=st.session_state.form_email
                     if 'form_email' in st.session_state else "")

        st.text_input("Contraseña",
                     type="password",
                     key="password_input",
                     value=st.session_state.form_password)

        submit_button = st.form_submit_button("Acceder")

        if submit_button:
            email = st.session_state.email_input
            password = st.session_state.password_input

            # Store values in session_state
            st.session_state.form_email = email
            st.session_state.form_password = password

            try:
                response = config.supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": password
                })

                st.session_state['supabase_session'] = response.session
                st.session_state['authenticated'] = True
                st.rerun()

            except Exception as e:
                st.error("Credenciales incorrectas")

    # Password recovery section
    st.markdown("---")
    st.subheader("¿Olvidaste tu contraseña?")
    if st.button("Recuperar contraseña"):
        st.session_state.password_recovery = True
        st.rerun()

else:
    # If authenticated, redirect to activities page
    st.switch_page("pages/3_Actividades.py")