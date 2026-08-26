-- Diseño de RBAC a nivel de base de datos para Sistema de Turnos / Sistema de
-- Facturación en producción (motor Postgres).
--
-- Por qué este archivo no se ejecuta contra la demo: la actividad (sección
-- "Herramientas del Día") indica sqlite3 como motor de referencia, y SQLite no
-- implementa roles ni GRANT/REVOKE (no hay control de acceso a nivel de motor,
-- solo a nivel de sistema de archivos). Este script documenta cómo se aplicaría
-- la segregación de privilegios (rol aplicativo vs. rol auditor) si el proyecto
-- se despliega sobre Postgres, que es el motor real que usaría un banco/clínica.
--
-- rol_aplicativo: el usuario con el que se conecta la API (FastAPI/SQLAlchemy).
-- Solo puede leer y escribir tablas de negocio; nunca puede tocar la tabla de
-- auditoría (ni siquiera para insertar directamente — eso lo hace vía función).
-- rol_auditor: usuario de solo lectura para el equipo de seguridad/compliance,
-- exclusivamente sobre la pista de auditoría inmutable.

CREATE ROLE rol_aplicativo LOGIN PASSWORD 'cambiar-en-deploy';
CREATE ROLE rol_auditor LOGIN PASSWORD 'cambiar-en-deploy';

-- Tablas de negocio: la app puede leer/escribir, nunca DROP ni DDL.
GRANT SELECT, INSERT, UPDATE ON turnos, users, api_clients TO rol_aplicativo;
REVOKE DELETE, TRUNCATE, REFERENCES, TRIGGER ON turnos, users, api_clients FROM rol_aplicativo;

-- Tabla de auditoría: la app solo puede insertar (nunca leer en bloque, nunca
-- modificar/borrar). La inmutabilidad se refuerza doblemente: a nivel de
-- aplicación (sin endpoints de UPDATE/DELETE, ver app/audit.py) y ahora también
-- a nivel de motor de base de datos.
GRANT INSERT ON audit_log TO rol_aplicativo;
REVOKE SELECT, UPDATE, DELETE, TRUNCATE ON audit_log FROM rol_aplicativo;

-- rol_auditor: exactamente lo opuesto. Solo lectura de la pista de auditoría,
-- sin acceso a datos de negocio (evita que auditoría vea PII de pacientes que
-- no necesita para verificar integridad del log).
GRANT SELECT ON audit_log TO rol_auditor;
REVOKE ALL ON turnos, users, api_clients FROM rol_auditor;

-- Defensa en profundidad adicional: nadie puede hacer DROP/ALTER sobre
-- audit_log salvo el owner (rol de migraciones, no usado en runtime).
REVOKE ALL ON audit_log FROM PUBLIC;
GRANT INSERT ON audit_log TO rol_aplicativo;
GRANT SELECT ON audit_log TO rol_auditor;
