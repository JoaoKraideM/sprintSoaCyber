import os
from pathlib import Path

# Usa SQLite isolado antes de importar a aplicação.
DB_PATH = Path(__file__).with_name("api_test.db")
os.environ["DB_DRIVER"] = "sqlite"
os.environ["SQLITE_DATABASE_URL"] = f"sqlite:///{DB_PATH.as_posix()}"
os.environ["DATABASE_URL"] = f"sqlite:///{DB_PATH.as_posix()}"
os.environ["REQUIRE_PAYLOAD_SIGNATURE"] = "false"

from fastapi.testclient import TestClient

from app.api.deps import obter_db
from app.db.session import Base, SessionLocal, engine
from app.main import app
from app.services.auth_service import AuthService


def _client() -> TestClient:
    # O .env exige HTTPS; simule esse esquema no ASGI TestClient.
    return TestClient(app, base_url="https://testserver")


def override_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[obter_db] = override_db


def _token(email: str, password: str, role: str) -> str:
    with SessionLocal() as db:
        user = AuthService.cadastrar_utilizador(db, email=email, password=password, role=role, nome=role)
        fingerprint = AuthService.fingerprint_atual_do_utilizador(user)
        return AuthService.criar_token_jwt(user.email, user.role, fingerprint)


def setup_module():
    if DB_PATH.exists():
        DB_PATH.unlink()
    Base.metadata.create_all(bind=engine)
    _token("admin@test.local", "Admin1234", "admin")
    _token("user@test.local", "User12345", "user")


def teardown_module():
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if DB_PATH.exists():
        DB_PATH.unlink()


def test_login_sucesso():
    client = _client()
    response = client.post("/api/v1/auth/login", json={
        "email": "admin@test.local",
        "password": "Admin1234",
    })
    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["role"] == "admin"


def test_login_senha_incorreta():
    client = _client()
    response = client.post("/api/v1/auth/login", json={
        "email": "admin@test.local",
        "password": "SenhaErrada123",
    })
    assert response.status_code == 401


def test_endpoint_protegido_sem_token():
    client = _client()
    response = client.get("/api/v1/veiculos")
    assert response.status_code == 401


def test_endpoint_admin_com_role_user():
    client = _client()
    token = AuthService.criar_token_jwt(
        "user@test.local",
        "user",
        _fingerprint("user@test.local"),
    )
    response = client.post(
        "/api/v1/veiculos",
        headers={"Authorization": f"Bearer {token}"},
        json=_veiculo_payload(),
    )
    assert response.status_code == 403


def _fingerprint(email: str) -> str:
    with SessionLocal() as db:
        user = AuthService.obter_utilizador_por_email(db, email)
        return AuthService.fingerprint_atual_do_utilizador(user)


def _veiculo_payload():
    return {
        "marca": "FORD",
        "modelo": "Ranger",
        "versao": "XLT",
        "motorizacao": "2.0 Diesel",
        "potencia_cv": 170,
        "transmissao": "Automatica",
        "tracao": "4x4",
        "preco_sugerido": 250000,
        "pacote_equipamentos": {"Airbag": True},
        "observacao": "Teste de API",
    }


def test_crud_veiculo_com_testclient():
    client = _client()
    token = _token("admin2@test.local", "Admin1234", "admin")
    headers = {"Authorization": f"Bearer {token}"}

    criado = client.post("/api/v1/veiculos", headers=headers, json=_veiculo_payload())
    assert criado.status_code == 201
    veiculo_id = criado.json()["id"]

    listado = client.get("/api/v1/veiculos", headers=headers)
    assert listado.status_code == 200
    assert any(item["id"] == veiculo_id for item in listado.json()["itens"])

    detalhe = client.get(f"/api/v1/veiculos/{veiculo_id}", headers=headers)
    assert detalhe.status_code == 200
    assert detalhe.json()["id"] == veiculo_id

    atualizado = client.patch(
        f"/api/v1/veiculos/{veiculo_id}",
        headers=headers,
        json={"potencia_cv": 200, "preco_sugerido": 260000},
    )
    assert atualizado.status_code == 200

    removido = client.delete(f"/api/v1/veiculos/{veiculo_id}", headers=headers)
    assert removido.status_code == 204

    depois = client.get(f"/api/v1/veiculos/{veiculo_id}", headers=headers)
    assert depois.status_code == 404


def test_painel_admin_e_comparacao_de_veiculos():
    client = _client()
    token = _token("dashboard@test.local", "Admin1234", "admin")
    headers = {"Authorization": f"Bearer {token}"}

    primeiro = client.post("/api/v1/veiculos", headers=headers, json=_veiculo_payload())
    assert primeiro.status_code == 201
    segundo_payload = _veiculo_payload() | {
        "versao": "Limited",
        "potencia_cv": 200,
        "preco_sugerido": 280000,
        "motorizacao": "2.0 Diesel Biturbo",
    }
    segundo = client.post("/api/v1/veiculos", headers=headers, json=segundo_payload)
    assert segundo.status_code == 201

    painel = client.get("/api/v1/admin/dashboard", headers=headers)
    assert painel.status_code == 200
    assert painel.json()["admin"]["email"] == "dashboard@test.local"
    assert "sprint3" in painel.json()
    assert "auditoria" in painel.json()

    comparacao = client.get(
        "/api/v1/admin/comparacoes/veiculos",
        params={"veiculo_id_a": primeiro.json()["id"], "veiculo_id_b": segundo.json()["id"]},
        headers=headers,
    )
    assert comparacao.status_code == 200
    assert comparacao.json()["diferencas_numericas"]["potencia_cv"]["diferenca"] == -30


def test_painel_admin_bloqueia_usuario_comum():
    client = _client()
    token = _token("normal-dashboard@test.local", "User12345", "user")
    response = client.get("/api/v1/admin/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
