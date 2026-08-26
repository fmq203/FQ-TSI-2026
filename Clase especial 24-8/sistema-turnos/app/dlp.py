import json

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

from app.audit import log_event
from app.database import SessionLocal

PII_PATH = "/api/v1/pacientes"
MAX_REGISTROS_SIN_CONTROL = 5


def _tiene_documento_en_claro(registros: list[dict]) -> bool:
    return any(r.get("documento") and "*" not in r["documento"] for r in registros)


def register_dlp_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def dlp_pacientes(request: Request, call_next):
        response = await call_next(request)
        if request.url.path != PII_PATH or response.status_code != 200:
            return response

        body = b""
        async for chunk in response.body_iterator:
            body += chunk
        try:
            data = json.loads(body)
        except ValueError:
            return Response(content=body, status_code=response.status_code, media_type=response.media_type)

        registros = data.get("registros", [])
        violacion = None
        if len(registros) > MAX_REGISTROS_SIN_CONTROL:
            violacion = "mas_de_5_registros_sin_paginacion"
        elif _tiene_documento_en_claro(registros):
            violacion = "documento_identidad_en_texto_claro"

        if violacion:
            db = SessionLocal()
            try:
                log_event(
                    db,
                    actor="dlp-middleware",
                    action="dlp_blocked",
                    entity="paciente",
                    entity_id=None,
                    detail={"violacion": violacion, "path": str(request.url), "registros_intentados": len(registros)},
                )
            finally:
                db.close()
            return JSONResponse(
                status_code=403,
                content={"detail": "Bloqueado por politica DLP", "violacion": violacion},
            )

        return JSONResponse(status_code=response.status_code, content=data)
