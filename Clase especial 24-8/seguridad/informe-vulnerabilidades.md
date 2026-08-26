# Informe de gestión de vulnerabilidades

**Sistemas evaluados:** Sistema de Turnos (Sistema A) y Sistema de Facturación (Sistema B)
**Fecha:** {{completar}}
**Responsable:** {{completar}}

## 1. Alcance
- Código fuente de `sistema-turnos/` y `sistema-facturacion/`.
- Dependencias de terceros (`requirements.txt` de cada sistema).
- Superficie web y REST expuesta en tiempo de ejecución (`:8001` y `:8002`).

## 2. Metodología y herramientas
| Tipo | Herramienta | Qué cubre | Script |
|---|---|---|---|
| SAST (análisis estático) | Bandit | Código Python: uso de `eval`, secretos hardcodeados, SQL/OS injection, etc. | `run_sast.sh` |
| SCA (composición de software) | pip-audit | CVEs conocidas en dependencias de `requirements.txt` | `run_sca.sh` |
| DAST (análisis dinámico) | OWASP ZAP (baseline) | Cabeceras de seguridad, cookies, XSS reflejado, exposición de endpoints | `run_dast.sh` |

Correr en orden: instalar `requirements-dev.txt`, ejecutar `run_sast.sh` y `run_sca.sh` en cualquier momento; para `run_dast.sh` ambos sistemas deben estar corriendo.

## 3. Hallazgos

La matriz formal (CWE/CVE/CVSS + nivel de riesgo, formato RBVM) está consolidada en [../informe.md](../informe.md), sección 3, a partir de la corrida real de `run_sast.sh` y `run_sca.sh`. Resumen:

| ID | Sistema | Herramienta | Severidad (CVSS) | Descripción | Evidencia |
|---|---|---|---|---|---|
| VULN-001 | sistema-facturacion | Bandit | Low (CWE-330) | `random.uniform` para generar el monto de la factura (no criptográfico, pero tampoco es un secreto — dato ficticio de demo) | `sast/sistema-facturacion-bandit.txt` |
| V-03 (=VULN-002) | ambos | pip-audit | 7.5 (Alto), CVE-2024-53981 | `python-multipart` 0.0.9 vulnerable a DoS por payload multipart malformado | `sca/sistema-turnos-pip-audit.txt`, `sca/sistema-facturacion-pip-audit.txt` |
| V-05 (=VULN-003) | ambos | pip-audit | 7.5 (Alto), CVE-2024-47874 | `starlette` 0.38.6 (dependencia de FastAPI) vulnerable a DoS por consumo de memoria en uploads sin límite | idem |

## 4. Plan de remediación
| ID | Acción correctiva | Responsable | Fecha límite | Estado |
|---|---|---|---|---|
| VULN-001 | Aceptado — no es un control de seguridad, es un monto ficticio de demo | RSI | — | Aceptado |
| VULN-002 | Actualizar `python-multipart` a `>=0.0.18` en ambos `requirements.txt` | Equipo de desarrollo | Próximo sprint | Abierto |
| VULN-003 | Actualizar `fastapi`/`starlette` a versión con el parche | Equipo de desarrollo | Próximo sprint | Abierto |

## 5. Retesting
Documentar aquí la corrida posterior a la remediación que confirma el cierre de cada hallazgo.
