# Evidencias

Estándar de nombre: `EVI-YYYY-MM-DD-NN-descripcion.ext`.

No tengo forma de tomar capturas de pantalla de tu navegador, tu celular o una app como Postman desde este entorno (no hay herramienta de browser/screenshot disponible acá) — así que generé lo que sí puedo obtener de forma reproducible (transcripciones reales de `curl` contra los sistemas corriendo, y el fragmento real del SBOM) como sustituto/complemento en `.txt`/`.json`. Los que requieren una captura visual real quedan pendientes de que las tomes vos.

| Archivo pedido | Estado | Notas |
|---|---|---|
| `EVI-2026-01-mfa-enroll.png` | **Pendiente — captura manual** | Screenshot de la pantalla `/mfa/setup` (QR + secreto) y de tu app autenticadora (Google Authenticator/Authy) mostrando el código sincronizado. |
| `EVI-2026-02-stepup-block-ok.png` | Complementado con `EVI-2026-08-24-02-stepup-transcript.txt` | Transcripción real de la llamada rechazada (401) y aceptada (200). Si querés el `.png`, repetí la secuencia en Postman/Insomnia y capturá pantalla. |
| `EVI-2026-03-hashchain-audit.png` | Complementado con `EVI-2026-08-24-03-hashchain-audit.txt` | Para el `.png`, andá a `/admin/audit` en el navegador (ambos sistemas) y capturá la tabla con el mensaje "Integridad de la cadena de hashes: OK". |
| `EVI-2026-04-dlp-blocked.png` | Complementado con `EVI-2026-08-24-04-dlp-blocked-transcript.txt` | Para el `.png`, repetí `GET /api/v1/pacientes?raw=true` en Postman y capturá el 403. |
| `EVI-2026-05-sbom-cyclonedx.png` | Complementado con `EVI-2026-08-24-05-sbom-cyclonedx-fragmento.json` | Para el `.png`, abrí `sbom/sbom-sistema-turnos.json` en el editor y capturá un fragmento con componentes y versiones visibles. |
| `EVI-2026-06-caso-directivo-arquitectura.png` | **Pendiente — captura manual** | El diagrama ya está en `caso-directivo-pam.md` (ASCII). Capturalo desde el editor/preview de Markdown, o pasalo por una herramienta de diagramas si preferís una versión gráfica. |

Si preferís que genere el diagrama del caso directivo como imagen (por ejemplo con draw.io) en vez de ASCII, decímelo y lo armo.
