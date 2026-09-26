# syntax=docker/dockerfile:1
# ---------------------------------------------------------------------------
# IaC Security (Sprint 3 - Cybersecurity): imagem minima, usuario nao-root,
# dependencias fixadas e sem segredos embutidos (segredos entram via --env-file
# ou orquestrador, nunca via ARG/ENV neste arquivo).
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS base

# Boas praticas de hardening de base image
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Instala apenas dependencias de runtime, sem compiladores desnecessarios
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Copia o codigo da aplicacao
COPY app ./app
COPY run.py .

# Cria usuario e grupo dedicados (principio do menor privilegio: nunca rodar como root)
RUN groupadd -r appgroup && useradd -r -g appgroup -d /app -s /sbin/nologin appuser \
    && mkdir -p /app/data/uploads \
    && chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

# Healthcheck consumido por orquestradores (Docker/Kubernetes) para monitoramento
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://127.0.0.1:8000/health/db || exit 1

# Nao roda com --reload em producao; sem privilegios extras
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
