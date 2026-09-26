from pathlib import Path

from fastapi import Cookie, Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.admin import router as admin_router
from app.api.auth import router as auth_router
from app.api.deps import obter_db
from app.api.uploads import router as uploads_router
from app.api.veiculos import router as veiculos_router
from app.core.config import settings
from app.core.middleware import seguranca_middleware_global
from app.db.session import engine
from app.services.auth_service import AuthService

app = FastAPI(
    title="Plataforma de Inteligencia Competitiva Automotiva (SOA + Cyber Secure)",
    description="Base de cadastro, autenticacao JWT e upload Excel com arquitetura em camadas.",
    version="3.1.0",
    docs_url=None,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Payload-Signature", "X-Payload-Timestamp"],
)

app.middleware("http")(seguranca_middleware_global)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(veiculos_router, prefix="/api/v1")
app.include_router(uploads_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")

_web_dir = Path(__file__).resolve().parent / "web"
_session_cookie_name = "ica_access_token"
app.mount("/static", StaticFiles(directory=str(_web_dir)), name="static")


@app.get("/docs", include_in_schema=False)
def servir_documentacao_local():
    """Interface local de documentação OpenAPI sem dependências externas de CDN."""
    html = f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Documentação da API</title>
  <link rel="stylesheet" href="/static/openapi-local/docs.css">
</head>
<body>
  <header>
    <h1 id="api-title">Documentação da API</h1>
    <p id="api-description">Carregando especificação OpenAPI...</p>
  </header>
  <main>
    <div class="toolbar">
      <input id="search" type="search" placeholder="Buscar por endpoint, método ou descrição...">
      <select id="method-filter" aria-label="Filtrar por método HTTP">
        <option value="ALL">Todos os métodos</option>
        <option>GET</option><option>POST</option><option>PUT</option>
        <option>PATCH</option><option>DELETE</option>
      </select>
    </div>
    <section id="api-docs" aria-live="polite"><p class="muted">Carregando endpoints...</p></section>
  </main>
  <script src="/static/openapi-local/docs.js" defer></script>
</body>
</html>"""
    return HTMLResponse(html, headers={"Cache-Control": "no-store"})


def renderizar_pagina_web(tela_ativa: str) -> HTMLResponse:
    html = (_web_dir / "index.html").read_text(encoding="utf-8")
    telas = {"login", "registro", "upload", "admin", "reset"}
    tela = tela_ativa if tela_ativa in telas else "login"

    for nome_tela in telas:
        ativa = nome_tela == tela
        html = html.replace(f"{{{{{nome_tela}_nav_active}}}}", "active" if ativa else "")
        html = html.replace(f"{{{{{nome_tela}_screen_active}}}}", "active" if ativa else "")
        html = html.replace(f"{{{{{nome_tela}_screen_hidden}}}}", "" if ativa else "hidden")

    html = html.replace('class="nav-btn "', 'class="nav-btn"')
    html = html.replace('class="screen "', 'class="screen"')

    return HTMLResponse(
        html,
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


def token_cookie_valido(
    access_token: str | None = Cookie(default=None, alias=_session_cookie_name),
    db: Session = Depends(obter_db),
) -> bool:
    if not access_token:
        return False

    try:
        payload = AuthService.validar_token_jwt(access_token)
        user = AuthService.obter_utilizador_por_email(db, payload["sub"])
    except ValueError:
        return False

    if not user or not user.status:
        return False

    fingerprint_atual = AuthService.fingerprint_atual_do_utilizador(user)
    return payload["cred_fingerprint"] == fingerprint_atual and payload.get("role") in {"admin", "analista", "user"}


def token_cookie_admin(
    access_token: str | None = Cookie(default=None, alias=_session_cookie_name),
    db: Session = Depends(obter_db),
) -> bool:
    if not access_token:
        return False
    try:
        payload = AuthService.validar_token_jwt(access_token)
        user = AuthService.obter_utilizador_por_email(db, payload["sub"])
    except ValueError:
        return False
    if not user or not user.status or user.role != "admin":
        return False
    return payload["cred_fingerprint"] == AuthService.fingerprint_atual_do_utilizador(user)


@app.get("/", include_in_schema=False)
def servir_site():
    return renderizar_pagina_web("login")


@app.get("/login", include_in_schema=False)
def servir_login():
    return renderizar_pagina_web("login")


@app.get("/registro", include_in_schema=False)
def servir_registro():
    return renderizar_pagina_web("registro")


@app.get("/enviar-arquivo", include_in_schema=False)
def servir_envio_arquivo(autenticado: bool = Depends(token_cookie_valido)):
    if not autenticado:
        return RedirectResponse("/login", status_code=303)
    return renderizar_pagina_web("upload")


@app.get("/upload", include_in_schema=False)
def servir_upload(autenticado: bool = Depends(token_cookie_valido)):
    if not autenticado:
        return RedirectResponse("/login", status_code=303)
    return renderizar_pagina_web("upload")


@app.get("/redefinir-senha", include_in_schema=False)
def servir_redefinicao_senha():
    return renderizar_pagina_web("reset")


@app.get("/admin", include_in_schema=False)
def servir_painel_admin(autenticado: bool = Depends(token_cookie_admin)):
    if not autenticado:
        return RedirectResponse("/login", status_code=303)
    return renderizar_pagina_web("admin")


@app.get("/painel-admin", include_in_schema=False)
def servir_painel_admin_alias(autenticado: bool = Depends(token_cookie_admin)):
    if not autenticado:
        return RedirectResponse("/login", status_code=303)
    return renderizar_pagina_web("admin")


@app.get("/health/db", tags=["Health"])
def verificar_conexao_banco():
    with engine.connect() as conexao:
        conexao.execute(text("SELECT 1"))
    return {"status": "ok", "database": "conectado"}
