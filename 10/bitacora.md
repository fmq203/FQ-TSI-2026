# Bitácora RSI — Actividad 10: Laboratorio Paso a Paso (mini-red de banco)

**Fecha:** 2026-09-02
**Objetivo:** construir la mini-red segmentada del INFRA-10 (LAN interna,
DMZ, "Internet simulada", firewall) y demostrar con evidencia que la
segmentación funciona.
**Diferencia respecto al instructivo:** el PDF está escrito para
VirtualBox en una PC de escritorio. Acá se construyó equivalente sobre un
hipervisor **Proxmox VE** (`proxmox01`, 6 cores / 23 GB RAM), reutilizando
recursos ya existentes en el homelab en vez de crear todo desde cero.

## 1. Adaptación de la topología a Proxmox

La "Red interna" de VirtualBox (aislamiento sin salida) se traduce en
Proxmox a **bridges Linux sin puerto físico**. Se crearon tres, dedicados
solo a este laboratorio, sin tocar el bridge de la red real (`vmbr0`):

| Bridge | Rol PDF | Red |
|---|---|---|
| `vmbr10` | Internet simulada (no usado al final, ver nota) | — |
| `vmbr11` | LAN interna | 10.10.10.0/24 |
| `vmbr12` | DMZ | 10.10.20.0/24 |

```
auto vmbr11
iface vmbr11 inet manual
	bridge-ports none
	bridge-stp off
	bridge-fd 0
```//etc/network/interfaces.d/lab-infra10, aplicado en caliente con `ifreload -a` sin cortar la sesión de administración.

**Nota — desviación deliberada del WAN:** a pedido explícito, la interfaz
WAN del firewall se conectó a la red real de la casa (`vmbr0`, DHCP) en
vez de a `vmbr10` (Internet simulada aislada). Esto no afecta la
segmentación LAN↔DMZ, que es el objetivo central del laboratorio; solo
cambia de dónde sale el firewall a Internet. Queda documentado como
desviación consciente, no como error.

## 2. Firewall: reutilización de `opnrouter` (OPNsense) en vez de pfSense

Ya existía en el homelab una VM `opnrouter` (id 124) con la ISO de
**OPNsense 26.1.2** montada y sin instalar. Se reutilizó en vez de
descargar pfSense: mismo motor de filtrado (`pf` de BSD), misma lógica de
reglas y misma interfaz de conceptos que describe el PDF.

- Instalación interactiva por consola (asistente de OPNsense).
- Interfaces asignadas: `vtnet0`→WAN, `vtnet1`→LAN, `vtnet2`→OPT1 (DMZ).
- IPs: WAN DHCP (`192.168.0.162`), LAN `10.10.10.254/24`, OPT1 `10.10.20.254/24`.
- DHCP habilitado en LAN: `10.10.10.10`–`10.10.10.100`.
- **Nota de seguridad:** la contraseña de `root` quedó en el valor por
  defecto de instalación (no se cambió, a pedido explícito). Queda
  registrado como hallazgo pendiente de remediar antes de considerar este
  firewall apto para nada más allá del laboratorio (ver informe, sección
  de hallazgos).

## 3. Servidores del laboratorio

En vez de instalar sistemas operativos completos por ISO (como indica el
PDF para VirtualBox), se usaron **contenedores LXC** de Proxmox
(Debian 12), mucho más livianos y con aprovisionamiento reproducible:

| Rol | CT | IP | Servicio |
|---|---|---|---|
| Servidor de datos interno | 210 (`lab-srv-datos`) | 10.10.10.20 | `openssh-server`, `/root/datos.txt` con "DATOS DE PRUEBA - NO REALES" |
| Servidor web DMZ | 211 (`lab-web-dmz`) | 10.10.20.10 | `nginx`, página de prueba con fecha |

Detalle técnico: los contenedores nacen sin salida a Internet (están en
bridges aislados a propósito), así que para instalar paquetes se les dio
una NIC temporal a la red real (`vmbr0`, DHCP), se instaló lo necesario, y
se retiró esa NIC antes de correr cualquier prueba — las pruebas de
segmentación se hicieron siempre con la topología final, sin atajos.

## 4. Reglas de firewall — API REST de OPNsense en vez de clics uno por uno

Las 7 reglas de la tabla del PDF (Paso 6) se cargaron con la **API REST
de OPNsense** (`/api/firewall/filter/addRule`), autenticada con una API
key generada desde el usuario `root` (credencial de API separada de la
contraseña de la cuenta, revocable de forma independiente). Se agregaron
además 2 reglas de DNS (R8) que el PDF no contemplaba explícitamente pero
son indispensables: sin ellas, ni LAN ni DMZ pueden resolver nombres
porque R4/R6 solo abren 80/443 y el resto queda bloqueado por R7 — el
mismo tipo de "regla de salida olvidada" que el propio PDF advierte en su
tabla de errores comunes.

Orden final aplicado (las reglas específicas antes que las generales, por
interfaz, evaluación primer-match-gana):

```
LAN:   R8(DNS) → R6(HTTP) → R6(HTTPS) → R6b(bloqueo resto a DMZ) → R5(resto a Internet) → R7(deny)
OPT1:  R3(bloqueo a LAN) → R4(HTTP saliente) → R4(HTTPS saliente) → R7(deny)
WAN:   R1(HTTP a DMZ) → R1(HTTPS a DMZ) → R2(deny resto) → R7(deny)
```

## 5. Hallazgo real durante la Prueba D (Nmap) — y su corrección

Al escanear la DMZ desde el cliente (`nmap -sS 10.10.20.10`), apareció el
puerto **22/tcp abierto además del 80/tcp**. Causa raíz: la regla `R5`
(LAN → cualquiera, cualquier puerto, permitir) tenía secuencia 20, después
de `R6` (que solo cubre 80/443) pero **antes** de `R7` (deny por
defecto, secuencia 900). Cualquier puerto hacia la DMZ que no fuera
80/443 caía en `R5` y pasaba igual, dejando SSH del servidor DMZ
alcanzable desde toda la LAN — algo que el diseño original del
laboratorio no contemplaba y que un Nmap real detectó, tal como se supone
que debe pasar.

**Corrección:** se agregó `R6b` (LAN → DMZ, bloquear todo lo que no sea
80/443) con secuencia 15, entre `R6` y `R5`. Verificado después del
cambio: puerto 22 pasa a estar filtrado/cerrado desde LAN, HTTP sigue
respondiendo `200 OK`. Evidencia en
`evidencias/EVI-2026-09-02-02-reglas-firewall-opnsense-final.txt`.

## 6. Pruebas del Paso 7 — resultados

| Prueba | Comando | Resultado | Evidencia |
|---|---|---|---|
| A — web DMZ responde | `curl -I http://10.10.20.10` desde LAN | `HTTP 200` | Ejecutado por SSH + captura de navegador desde Kali |
| B — DMZ no alcanza LAN | `ping`/`ssh` desde 211 a 10.10.10.20 | 100% packet loss, SSH timeout | Ejecutado por SSH |
| C — LAN navega a Internet | `ping 192.168.0.1` desde 210, TTL 63 (un salto = pasó por el firewall) | OK | Ejecutado por SSH |
| D — Nmap | `nmap -sP 10.10.20.0/24`, `nmap -sS 10.10.20.10` desde Kali | 2 hosts vivos; 22 y 80 abiertos → corregido a solo 80 | `EVI-2026-09-02-03-nmap-dmz.png` |

## 7. Wireshark (Paso 8)

Captura en Kali, interfaz LAN (`eth0`), dos filtros:

- `icmp`: ping 10.10.10.16 (Kali) → 10.10.20.10 (web DMZ), TTL 64 salida /
  63 en la respuesta (confirma que atravesó el firewall).
  `EVI-2026-09-02-05-wireshark-icmp.png`
- `http`: `GET / HTTP/1.1` → `200 OK`, seguido de `GET /favicon.ico` →
  `404 Not Found`. Three-way handshake implícito en el stream TCP.
  `EVI-2026-09-02-04-wireshark-http.png`

## 8. Cliente del laboratorio

En vez de instalar una VM de escritorio nueva (Xubuntu/Mint) como sugiere
el PDF, se reutilizó la VM `kali` ya existente en el homelab (id 120, ya
instalada), moviéndole la NIC a la LAN del laboratorio (`vmbr11`). Trae
Nmap y Wireshark preinstalados, cumple el mismo rol que el "Cliente" del
PDF.

## 9. Acceso administrativo usado durante la construcción

Para las tareas que el MCP de Proxmox no cubre (red del host, hardware de
VM, configuración de OPNsense) se generó un par de claves SSH dedicado
(`labops`, usuario propio con sudo en el host, no root) — revocable
borrando el usuario o su clave sin afectar nada más del homelab.
