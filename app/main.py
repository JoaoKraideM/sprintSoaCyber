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
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
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


def renderizar_pagina_web(tela_ativa: str) -> HTMLResponse:
    html = (_web_dir / "index.html").read_text(encoding="utf-8")
    telas = {"login", "registro", "upload"}
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


@app.get("/health/db", tags=["Health"])
def verificar_conexao_banco():
    with engine.connect() as conexao:
        conexao.execute(text("SELECT 1"))
    return {"status": "ok", "database": "conectado"}
