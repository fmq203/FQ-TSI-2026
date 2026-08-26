"""
API REST de ejemplo para una institucion financiera.
Endpoints:
  GET /health   -> estado del servicio, publico
  GET /usuarios -> lista de usuarios, protegido con token en Authorization
"""
import os
import re
import secrets

from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Configuracion
# ---------------------------------------------------------------------------

# El token se lee de una variable de entorno; nunca se hardcodea en el
# repositorio. En produccion cada cliente/servicio deberia tener su propio
# token, gestionado en un almacen de secretos (Vault, AWS Secrets Manager...).
API_TOKEN = os.environ.get("API_TOKEN")
if not API_TOKEN:
    raise RuntimeError(
        "La variable de entorno API_TOKEN es obligatoria. "
        "Ejemplo: export API_TOKEN=$(python -c 'import secrets;print(secrets.token_urlsafe(32))')"
    )

# Origen unico permitido para CORS (front-end de la institucion).
ALLOWED_ORIGIN = os.environ.get("ALLOWED_ORIGIN", "https://app.mibanco.com")

CORS(
    app,
    resources={r"/usuarios": {"origins": ALLOWED_ORIGIN}},
    methods=["GET"],
    allow_headers=["Authorization", "Content-Type"],
    supports_credentials=False,
    max_age=600,
)

# Datos de ejemplo. En un sistema real vendrian de una base de datos,
# nunca incluyendo campos sensibles (contrasenas, PAN, etc.) en la
# respuesta de la API.
USUARIOS = [
    {"id": 1, "nombre": "Ana Perez", "email": "ana.perez@mibanco.com"},
    {"id": 2, "nombre": "Luis Gomez", "email": "luis.gomez@mibanco.com"},
    {"id": 3, "nombre": "Marta Diaz", "email": "marta.diaz@mibanco.com"},
]

ID_PATTERN = re.compile(r"^\d{1,10}$")


# ---------------------------------------------------------------------------
# Cabeceras de seguridad (aplicadas a toda respuesta)
# ---------------------------------------------------------------------------
@app.after_request
def set_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    # Evita que el servidor filtre su version/tecnologia (defensa en profundidad).
    response.headers.pop("Server", None)
    return response


# ---------------------------------------------------------------------------
# Autenticacion
# ---------------------------------------------------------------------------
def _extraer_token(auth_header: str) -> str | None:
    """Extrae el token de un header 'Authorization: Bearer <token>'."""
    if not auth_header:
        return None
    partes = auth_header.split(" ", 1)
    if len(partes) != 2 or partes[0] != "Bearer":
        return None
    return partes[1].strip()


def requiere_token(f):
    from functools import wraps

    @wraps(f)
    def wrapper(*args, **kwargs):
        token = _extraer_token(request.headers.get("Authorization", ""))
        if not token or not secrets.compare_digest(token, API_TOKEN):
            return jsonify({"error": "No autorizado"}), 401
        return f(*args, **kwargs)

    return wrapper


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.get("/health")
def health():
    return jsonify({"status": "ok"}), 200


@app.get("/usuarios")
@requiere_token
def usuarios():
    # Validacion de parametros: 'id' es opcional, pero si viene debe ser
    # un entero corto. Cualquier otro valor se rechaza con 400 en vez de
    # dejarlo pasar a una consulta o filtro sin validar.
    id_param = request.args.get("id")
    if id_param is not None:
        if not ID_PATTERN.match(id_param):
            return jsonify({"error": "Parametro 'id' invalido"}), 400
        usuario = next((u for u in USUARIOS if u["id"] == int(id_param)), None)
        if usuario is None:
            return jsonify({"error": "Usuario no encontrado"}), 404
        return jsonify(usuario), 200

    return jsonify(USUARIOS), 200


@app.errorhandler(404)
def not_found(_err):
    return jsonify({"error": "Recurso no encontrado"}), 404


@app.errorhandler(405)
def method_not_allowed(_err):
    return jsonify({"error": "Metodo no permitido"}), 405


if __name__ == "__main__":
    # debug=False siempre en produccion: el modo debug expone un evaluador
    # de expresiones interactivo (Werkzeug debugger) si ocurre una excepcion.
    app.run(host="127.0.0.1", port=5000, debug=False)
