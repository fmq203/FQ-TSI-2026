# Informe Ejecutivo — Actividad 10: Laboratorio Paso a Paso (segmentación de red)

**Institución:** Banco Ficticio del Uruguay (ejercicio académico)
**Responsable de Seguridad de la Información (RSI):** [Nombre y cargo]
**Destinatario:** Banco Central del Uruguay — Superintendencia de Instituciones Financieras
**Asunto:** Construcción y verificación de un entorno de red segmentado (LAN/DMZ/firewall)
**Fecha:** 2026-09-02 | **Versión:** 1.0 | **Clasificación:** Confidencial

## 1. Resumen ejecutivo

Se construyó una mini-red de banco de tres zonas — LAN interna, DMZ e
Internet — separadas por un firewall con reglas explícitas, sobre
infraestructura de virtualización (Proxmox VE) en vez del entorno de
escritorio (VirtualBox) que describe el instructivo original. Se
verificaron con evidencia las cuatro condiciones de aprobación del
laboratorio: el servidor web de la DMZ responde desde la red externa, el
servidor interno **no** es alcanzable desde la DMZ, el cliente interno
navega hacia afuera, y todas las pruebas quedaron registradas con fecha.
Durante la Prueba D (Nmap) se detectó y corrigió un hallazgo real: una
regla de firewall demasiado permisiva dejaba el puerto SSH de la DMZ
alcanzable desde la LAN interna — exactamente el tipo de brecha que este
ejercicio existe para enseñar a encontrar.

## 2. Marco normativo y regulatorio aplicable

- MCU 5.0 — funciones de protección (PR) y detección (DE).
- ISO/IEC 27001:2022, Anexo A — A.13 (seguridad de redes), A.12.6 (gestión de vulnerabilidades), A.12.4 (registros de actividad).
- RNRCSF del BCU, art. 492 — evidencia técnica de segmentación y reglas de firewall documentadas.
- URCDP-01 — Documento de Seguridad de Datos Personales: medidas lógicas (segmentación, DMZ, firewall, logs).

## 3. Alcance y metodología

- **Alcance:** red de laboratorio aislada (ningún dato ni IP real del banco), construida sobre el hipervisor Proxmox `proxmox01`.
- **Componentes:** firewall OPNsense (equivalente funcional de pfSense), un servidor de "datos internos" (SSH), un servidor web público (DMZ), un cliente con Nmap y Wireshark.
- **Método:** construcción de la topología, carga de reglas de firewall, y batería de pruebas funcionales (conectividad, bloqueo, escaneo, captura de tráfico) con evidencia fechada.
- **Periodo de ejecución:** 2026-09-02.

## 4. Desviaciones documentadas respecto al instructivo original

El PDF de referencia (`10-Laboratorio-Paso-a-Paso.pdf`) está escrito para
VirtualBox en una máquina de escritorio. Se adaptó a la infraestructura
real disponible (Proxmox), documentando cada desviación en la bitácora
técnica (`bitacora.md`):

| Elemento del PDF | Lo que se hizo | Motivo |
|---|---|---|
| VirtualBox "Red interna" | Bridges Linux aislados en Proxmox (`vmbr10/11/12`) | Equivalente funcional en el hipervisor disponible |
| pfSense nuevo | Se reutilizó una VM OPNsense ya existente | Mismo motor de filtrado, ahorra una instalación completa |
| Servidores Ubuntu Server completos | Contenedores LXC Debian 12 | Mismo resultado funcional, muchísimo más liviano |
| WAN = "Internet simulada" aislada | WAN = red real de la casa (DHCP) | Pedido explícito; no afecta la segmentación LAN↔DMZ, que es el objetivo del ejercicio |
| Cliente Xubuntu/Mint nuevo | Se reutilizó una VM Kali ya existente | Ya tiene Nmap y Wireshark instalados |

## 5. Verificación de las 4 condiciones de aprobación del laboratorio

| # | Condición | Resultado |
|---|---|---|
| 1 | El servidor web de la DMZ responde desde la red externa | ✅ `HTTP 200` (Prueba A) |
| 2 | El servidor interno NO es alcanzable desde la DMZ | ✅ 100% packet loss + SSH timeout (Prueba B) |
| 3 | El cliente interno navega hacia Internet | ✅ TTL confirma tránsito por el firewall (Prueba C) |
| 4 | Todas las pruebas quedaron registradas con fecha | ✅ `evidencias/` (9 archivos, ver README) |

## 6. Hallazgos

| ID | Hallazgo | Severidad | Estado |
|---|---|---|---|
| LAB10-01 | Regla `R5` (LAN→cualquiera, cualquier puerto) evaluada antes que el deny por defecto dejaba el puerto SSH del servidor DMZ alcanzable desde toda la LAN, no solo 80/443 como pretendía `R6` | Media | **Remediado** — regla `R6b` agregada, verificado con Nmap y prueba directa de socket |
| LAB10-02 | Contraseña de `root` del firewall OPNsense sin cambiar del valor por defecto de instalación | Media (mitigado por exposición limitada: solo accesible desde la LAN del laboratorio, no desde WAN) | **Pendiente** — a definir por el responsable antes de reutilizar este firewall fuera del laboratorio |

## 7. Conclusión

El laboratorio demuestra en la práctica el mismo principio que protege los
datos reales del banco: una DMZ comprometida no implica acceso a los
datos internos, siempre que las reglas de firewall sean exhaustivas y se
verifiquen activamente — no alcanza con escribirlas, hay que probarlas con
herramientas como Nmap, como se hizo acá. El hallazgo LAB10-01 es en sí
mismo la evidencia más fuerte del valor de este ejercicio: una regla
"razonable" a primera vista dejó una brecha real, y solo el escaneo activo
la sacó a la luz.

Evidencia completa, bitácora técnica paso a paso y detalle de comandos en
[bitacora.md](bitacora.md) y [evidencias/](evidencias/).
