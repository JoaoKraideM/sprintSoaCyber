import time
import logging
from fastapi import Request, Response, status
from app.core.config import settings

logger = logging.getLogger("SecurityMiddleware")
ip_request_history = {}
RATE_LIMIT_WINDOW = 60
MAX_REQUESTS_PER_WINDOW = 30

async def seguranca_middleware_global(request: Request, call_next):
    # 1. Cybersecurity: Proteção contra Payload Flooding
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > settings.MAX_CONTENT_LENGTH:
        return Response(
            content='{"erro": "Payload demasiado grande. Bloqueado por Cybersecurity."}',
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            media_type="application/json"
        )
    
    # 2. SOA/Infra: Rate Limiting Reutilizável por IP
    ip = request.client.host if request.client else "127.0.0.1"
    agora = time.time()
    if ip not in ip_request_history:
        ip_request_history[ip] = []
    
    ip_request_history[ip] = [t for t in ip_request_history[ip] if agora - t < RATE_LIMIT_WINDOW]
    if len(ip_request_history[ip]) >= MAX_REQUESTS_PER_WINDOW:
        return Response(
            content='{"erro": "Taxa de requisições excedida (Rate Limit)."}',
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            media_type="application/json"
        )
    ip_request_history[ip].append(agora)
    
    # 3. Tratamento de Exceções Global (Ocultação de Stack Traces internos)
    try:
        return await call_next(request)
    except Exception as e:
        logger.error(f"[ALERTA CRÍTICO] Falha interna omitida ao utilizador: {str(e)}")
        return Response(
            content='{"erro": "Ocorreu um erro interno no servidor. A infraestrutura de segurança barrou a exposição dos dados."}',
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            media_type="application/json"
        )