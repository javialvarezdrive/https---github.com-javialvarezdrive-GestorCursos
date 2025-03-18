import os
from supabase import create_client

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# Initialize Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# App configuration
APP_NAME = "Policía Local de Vigo - Gestión de Agentes"

# Table names
AGENTS_TABLE = "agents"
COURSES_TABLE = "courses"
ACTIVITIES_TABLE = "activities"
PARTICIPANTS_TABLE = "activity_participants"
USERS_TABLE = "users"

# Sections in the police department
SECTIONS = [
    "Atestados",
    "Barrios",
    "Seguridad",
    "Tráfico",
    "Judicial",
    "Administrativa",
    "Playa",
    "Motorizada",
    "Enlace Judicial",
    "Patrulla Verde",
    "Coordinación",
    "Educación Vial",
    "Radar",
    "Depósito",
    "Alcaldía",
    "Grúa",
    "Centralita",
    "Puerto",
    "Control",
    "Oficina"
]

# Groups in the police department
GROUPS = ["G-0", "G-1", "G-2", "G-3", "G-4", "G-5", "G-6", "G-7", "G-8", "G-9"]

# Shifts
SHIFTS = ["Mañana", "Tarde", "Noche"]
