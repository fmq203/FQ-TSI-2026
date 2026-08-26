# Caso de uso: acceso directo de un alto directivo a la base de datos

## Escenario

El Directorio o un Gerente General solicita acceso directo e irrestricto a la base de datos de producción (Sistema de Turnos y/o Facturación) mediante un cliente SQL (DBeaver, pgAdmin) para ejecutar consultas analíticas inmediatas, sin pasar por la aplicación web.

## Riesgos identificados (RSI)

| Riesgo | Detalle |
|---|---|
| Violación de mínimo privilegio y segregación de funciones | El rol directivo no debe tener permisos de `UPDATE`/`DELETE`/`DROP` — solo necesita consultar, no modificar. |
| Fuga masiva de PII | Sin paginación ni DLP aplicativo, una consulta directa puede volcar toda la tabla `turnos` (nombres, documentos de pacientes) en un export. |
| Falta de trazabilidad y no repudio | Una conexión directa con credenciales compartidas no permite saber quién ejecutó qué consulta ni cuándo. |
| Incumplimiento normativo | Viola la Ley 18.331 (LPDP) y el marco SF.SEG.08 de BCU/AGESIC sobre control y registro de accesos a datos sensibles. |

## Dictamen del RSI

**No se autoriza** el acceso directo con credenciales de aplicación a la base de producción. Todo acceso de un directivo debe transitar por un **Bastion Host / PAM Gateway** con MFA obligatorio, usando un **rol de solo lectura sobre vistas con enmascaramiento de datos**, con **auditoría inmutable de cada sentencia ejecutada**. La justificación de negocio y la ventana temporal (Just-in-Time) quedan registradas antes de habilitar el acceso.

## Arquitectura exigida

```
[ Directivo / Cliente SQL ]
        │
        ▼  Requiere VPN / Zero Trust Network Access
┌───────────────────────────────────────────────────────────┐
│ Bastion Host / PAM Gateway (Privileged Access Management)  │
│  - Autenticación con MFA obligatorio (TOTP / Hardware key) │
│  - Grabación de sesión y registro de cada comando SQL      │
│  - Aprobación Just-in-Time (JIT) por ventana de tiempo      │
└───────────────────────────────────────────────────────────┘
        │  Conexión cifrada TLS, usuario restringido
        ▼
┌───────────────────────────────────────────────────────────┐
│ Base de Datos de Producción                                │
│  - Usuario: directorio_ro (SELECT únicamente, sobre vistas) │
│  - Data Masking: documento y otros PII parcialmente ocultos │
│  - Tabla de auditoría inmutable (hash-chaining, ver audit.py│
│    de sistema-turnos / sistema-facturacion)                │
└───────────────────────────────────────────────────────────┘
```

## Controles concretos

### 1. Bastion / PAM en el camino de red

No se abren puertos de base de datos (5432/3306) a redes abiertas ni a la red corporativa general. Toda conexión de un cliente SQL pasa por un proxy de base de datos con MFA (ej. Teleport, StrongDM, o como mínimo un túnel SSH con `ForceCommand` + TOTP). El bastion es quien autentica al directivo con credenciales nominativas (no compartidas) + segundo factor.

### 2. Acceso Just-in-Time (JIT)

El acceso no es una cuenta permanente: se solicita, se justifica ("necesito analizar ocupación de turnos del trimestre") y se habilita por una ventana acotada (ej. 2 horas), después de la cual el bastion revoca la sesión automáticamente. Esto evita el patrón de "cuenta de directivo con acceso eterno" que es el hallazgo más común en auditorías BCU.

### 3. Rol restringido + vistas con Data Masking (ver `db_roles.sql` y el ejemplo de vista abajo)

El directivo nunca se conecta con el usuario de la aplicación (`rol_aplicativo`). Se le crea un usuario `directorio_ro`, con `SELECT` únicamente sobre **vistas** (no tablas base) donde el documento de identidad y otros campos sensibles están parcialmente enmascarados:

```sql
CREATE ROLE directorio_ro LOGIN PASSWORD 'gestionada-por-bastion';

CREATE VIEW vw_turnos_directorio AS
SELECT
    id,
    paciente,
    -- Data masking: solo se ven los dos primeros y dos últimos dígitos
    left(documento_paciente, 2) || repeat('*', greatest(length(documento_paciente) - 4, 0))
        || right(documento_paciente, 2) AS documento_paciente,
    medico,
    fecha,
    estado
FROM turnos;

GRANT SELECT ON vw_turnos_directorio TO directorio_ro;
REVOKE ALL ON turnos, users, api_clients, audit_log FROM directorio_ro;
```

Esto es el mismo enmascaramiento que ya aplica el endpoint `GET /api/v1/pacientes` de Sistema de Turnos (`_mask_documento` en `app/routers/api_v1.py`) — la vista de BD replica esa misma política de protección de PII, pero a nivel de motor de datos, como defensa en profundidad para el caso en que alguien se salte la API.

### 4. Auditoría de queries con hash-chaining

Cada sentencia SQL ejecutada por el bastion se registra asociada a la identidad real del directivo (no a un usuario técnico genérico), y se persiste en una tabla de auditoría con el mismo mecanismo de encadenamiento criptográfico (`prev_hash` → `entry_hash` con SHA-256) implementado en `app/audit.py` de ambos sistemas — de modo que ni siquiera un DBA con acceso a la base puede alterar retroactivamente el historial de accesos sin que la verificación de cadena lo detecte (ver `/admin/audit`).

## Qué queda simulado vs. implementado en este entregable

- **Implementado y funcional**: el enmascaramiento de PII (`_mask_documento`) y el bloqueo DLP ante extracción masiva, sobre el endpoint `GET /api/v1/pacientes` de Sistema de Turnos; el log de auditoría con hash-chaining verificable en ambos sistemas.
- **Documentado, no desplegado**: el Bastion Host / PAM (Teleport/StrongDM) y el motor Postgres con roles reales (`db_roles.sql`), porque requieren infraestructura fuera del alcance de un laptop de clase — se entregan como diseño listo para producción, con el SQL exacto a ejecutar.
