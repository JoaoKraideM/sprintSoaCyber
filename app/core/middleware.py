import logging
import time

from fastapi import Request, Response, status

from app.core.config import settings

logger = logging.getLogger("SecurityMiddleware")
ip_request_history = {}
RATE_LIMIT_WINDOW = 60
MAX_REQUESTS_PER_WINDOW = 30


async def seguranca_middleware_global(request: Request, call_next):
    # 1. Protecao contra payload flooding.
    content_length = request.headers.get("content-length")
    limite_payload = settings.MAX_CONTENT_LENGTH
    if request.url.path.startswith("/api/v1/uploads/"):
        limite_payload = settings.MAX_UPLOAD_FILE_SIZE + (512 * 1024)

    if content_length and int(content_length) > limite_payload:
        return Response(
            content='{"erro": "Payload recusado."}',
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            media_type="application/json",
        )

    # 2. Rate limiting por IP.
    ip = request.client.host if request.client else "127.0.0.1"
    agora = time.time()
    if ip not in ip_request_history:
        ip_request_history[ip] = []

    ip_request_history[ip] = [t for t in ip_request_history[ip] if agora - t < RATE_LIMIT_WINDOW]
    if len(ip_request_history[ip]) >= MAX_REQUESTS_PER_WINDOW:
        return Response(
            content='{"erro": "Taxa de requisicoes excedida (Rate Limit)."}',
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            media_type="application/json",
        )
    ip_request_history[ip].append(agora)

    # 3. Tratamento global de excecoes e ocultacao de stack trace.
    try:
        response = await call_next(request)
    except Exception as exc:  # noqa: BLE001
        logger.error("[ALERTA CRITICO] Falha interna omitida ao utilizador: %s", str(exc))
        return Response(
            content='{"erro": "Ocorreu um erro interno no servidor. A infraestrutura de seguranca barrou a exposicao dos dados."}',
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            media_type="application/json",
        )

    # 4. Cabecalhos de seguranca para respostas HTTP.
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    response.headers["Content-Security-Policy"] = "default-src 'self'; style-src 'self' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; script-src 'self'; img-src 'self' data:; connect-src 'self';"

    if request.url.path.startswith("/static/") or response.headers.get("content-type", "").startswith("text/html"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"

    if request.url.scheme == "https":
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"

    return response
