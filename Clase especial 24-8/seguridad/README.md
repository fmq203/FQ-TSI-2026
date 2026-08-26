# Gestión de vulnerabilidades (externa a ambos sistemas)

Esta carpeta no es parte del código de ninguno de los dos sistemas: es el proceso de seguridad que se aplica *sobre* ambos, tal como pide la consigna ("gestión de vulnerabilidades externa para ambos").

## Cómo usar
```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements-dev.txt

./run_sast.sh   # Bandit sobre el código de los dos sistemas
./run_sca.sh    # pip-audit sobre las dependencias de los dos sistemas
./run_dast.sh   # OWASP ZAP contra las apps corriendo (requiere Docker + apps levantadas)
```

Los reportes quedan en `sast/`, `sca/` y `dast/`. Volcar los hallazgos relevantes (con severidad CVSS y plan de remediación) en [informe-vulnerabilidades.md](informe-vulnerabilidades.md); la versión ejecutiva consolidada (matriz RBVM con CWE/CVE reales encontrados por `run_sca.sh`) está en [../informe.md](../informe.md).

También en esta carpeta: [db_roles.sql](db_roles.sql) — diseño de roles de base de datos (`rol_aplicativo` / `rol_auditor`) para producción sobre Postgres, referenciado desde [../caso-directivo-pam.md](../caso-directivo-pam.md).
