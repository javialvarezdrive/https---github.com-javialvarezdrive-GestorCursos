-- Tabla de agentes
CREATE TABLE agents (
    nip VARCHAR(50) PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellido1 VARCHAR(100) NOT NULL,
    apellido2 VARCHAR(100),
    seccion VARCHAR(100),
    grupo VARCHAR(20),
    email VARCHAR(255),
    telefono VARCHAR(20),
    activo BOOLEAN DEFAULT TRUE,
    monitor BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de usuarios para autenticación
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    password VARCHAR(255) NOT NULL,
    agent_nip VARCHAR(50) REFERENCES agents(nip) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de cursos
CREATE TABLE courses (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL UNIQUE,
    descripcion TEXT NOT NULL,
    ocultar BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de actividades
CREATE TABLE activities (
    id SERIAL PRIMARY KEY,
    fecha DATE NOT NULL,
    turno VARCHAR(50) NOT NULL,
    curso_id INTEGER REFERENCES courses(id) ON DELETE SET NULL,
    monitor_nip VARCHAR(50) REFERENCES agents(nip) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(fecha, turno)
);

-- Tabla de participantes en actividades
CREATE TABLE activity_participants (
    id SERIAL PRIMARY KEY,
    activity_id INTEGER REFERENCES activities(id) ON DELETE CASCADE,
    agent_nip VARCHAR(50) REFERENCES agents(nip) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(activity_id, agent_nip)
);


-- FUNCIÓN SQL PARA VERIFICAR SI UN USUARIO AUTENTICADO ES MONITOR
CREATE OR REPLACE FUNCTION is_authenticated_user_monitor(authenticated_user_email VARCHAR)
RETURNS BOOLEAN AS $$
DECLARE
    is_monitor BOOLEAN;
BEGIN
    SELECT monitor INTO is_monitor
    FROM agents
    WHERE email = authenticated_user_email;

    RETURN is_monitor;
END;
$$ LANGUAGE plpgsql
SECURITY DEFINER;

-- Ejemplo de uso:
-- SELECT is_authenticated_user_monitor('email_del_usuario_autenticado@ejemplo.com');
