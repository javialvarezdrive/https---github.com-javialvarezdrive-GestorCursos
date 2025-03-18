
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
