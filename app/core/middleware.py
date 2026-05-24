import hashlib
import hmac
import logging
import time

from fastapi import Request, Response, status

from app.core.config import settings

logger = logging.getLogger("SecurityMiddleware")
ip_request_history = {}
RATE_LIMIT_WINDOW = 60
MAX_REQUESTS_PER_WINDOW = 30
MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def _json_response(payload: str, status_code: int) -> Response:
    return Response(content=payload, status_code=status_code, media_type="application/json")


def _request_usa_https(request: Request) -> bool:
    forwarded_proto = request.headers.get("x-forwarded-proto", "").split(",")[0].strip().lower()
    return request.url.scheme == "https" or forwarded_proto == "https"


def _conteudo_json(request: Request) -> bool:
    return request.headers.get("content-type", "").split(";", 1)[0].strip().lower() == "application/json"


def _assinatura_esperada(request: Request, timestamp: str, corpo: bytes) -> str:
    query = request.url.query
    body_hash = hashlib.sha256(corpo).hexdigest()
    canonical = "\n".join([request.method.upper(), request.url.path, query, timestamp, body_hash])
    digest = hmac.new(settings.PAYLOAD_SECRET_HMAC, canonical.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"sha256={digest}"


async def _validar_assinatura_payload(request: Request) -> Response | None:
    if not settings.REQUIRE_PAYLOAD_SIGNATURE:
        return None
    if request.method.upper() not in MUTATING_METHODS:
        return None
    if request.url.path in settings.PAYLOAD_SIGNATURE_EXEMPT_PATHS:
        return None
    if not request.url.path.startswith("/api/v1/") or not _conteudo_json(request):
        return None

    timestamp = request.headers.get("x-payload-timestamp", "")
    assinatura = request.headers.get("x-payload-signature", "")
    if not timestamp or not assinatura:
        return _json_response('{"erro": "Assinatura do payload obrigatoria."}', status.HTTP_401_UNAUTHORIZED)

    try:
        timestamp_int = int(timestamp)
    except ValueError:
        return _json_response('{"erro": "Timestamp de payload invalido."}', status.HTTP_401_UNAUTHORIZED)

    if abs(int(time.time()) - timestamp_int) > settings.PAYLOAD_SIGNATURE_MAX_AGE_SECONDS:
        return _json_response('{"erro": "Assinatura do payload expirada."}', status.HTTP_401_UNAUTHORIZED)

    corpo = await request.body()
    esperada = _assinatura_esperada(request, timestamp, corpo)
    if not hmac.compare_digest(assinatura, esperada):
        return _json_response('{"erro": "Assinatura do payload invalida."}', status.HTTP_401_UNAUTHORIZED)

    async def receber_corpo():
        return {"type": "http.request", "body": corpo, "more_body": False}

    request._receive = receber_corpo
    return None


async def seguranca_middleware_global(request: Request, call_next):
    if settings.FORCE_HTTPS and not _request_usa_https(request):
        return _json_response(
            '{"erro": "HTTPS obrigatorio para acessar este servico."}',
            status.HTTP_426_UPGRADE_REQUIRED,
        )

    # 1. Protecao contra payload flooding.
    content_length = request.headers.get("content-length")
    limite_payload = settings.MAX_CONTENT_LENGTH
    if request.url.path.startswith("/api/v1/uploads/"):
        limite_payload = settings.MAX_UPLOAD_FILE_SIZE + (512 * 1024)

    try:
        tamanho_requisicao = int(content_length) if content_length else 0
    except ValueError:
        return _json_response('{"erro": "Cabecalho Content-Length invalido."}', status.HTTP_400_BAD_REQUEST)

    if tamanho_requisicao > limite_payload:
        return _json_response('{"erro": "Payload recusado."}', status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)

    resposta_assinatura = await _validar_assinatura_payload(request)
    if resposta_assinatura:
        return resposta_assinatura

    # 2. Rate limiting por IP.
    ip = request.client.host if request.client else "127.0.0.1"
    agora = time.time()
    if ip not in ip_request_history:
        ip_request_history[ip] = []

    ip_request_history[ip] = [t for t in ip_request_history[ip] if agora - t < RATE_LIMIT_WINDOW]
    if len(ip_request_history[ip]) >= MAX_REQUESTS_PER_WINDOW:
        return _json_response(
            '{"erro": "Taxa de requisicoes excedida (Rate Limit)."}',
            status.HTTP_429_TOO_MANY_REQUESTS,
        )
    ip_request_history[ip].append(agora)

    # 3. Tratamento global de excecoes e ocultacao de stack trace.
    try:
        response = await call_next(request)
    except Exception as exc:  # noqa: BLE001
        logger.error("[ALERTA CRITICO] Falha interna omitida ao utilizador: %s", str(exc))
        return _json_response(
            '{"erro": "Ocorreu um erro interno no servidor. A infraestrutura de seguranca barrou a exposicao dos dados."}',
            status.HTTP_500_INTERNAL_SERVER_ERROR,
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

    if _request_usa_https(request):
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"

    return response
