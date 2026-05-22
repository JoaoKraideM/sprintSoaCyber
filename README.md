# Projeto Base - Sistema Veiculos (SOA + Cyber)

Aplicacao web e API em Python (FastAPI) com:
- cadastro/login de usuarios
- autenticacao JWT com payload em Base64
- cadastro e consulta de veiculos
- upload de Excel
- logs/auditoria conforme schema relacional solicitado

## Schema de banco (atual)

Tabelas implementadas no codigo:
- `users`
- `marcas`
- `modelos`
- `versoes`
- `veiculos`
- `metricas_veiculos`
- `logs`
- `logs_auth`
- `password_reset_tokens`

Importante:
- A aplicacao **nao recria tabelas automaticamente** no startup.
- O script SQL do schema fica em `app/db/schema.sql`.
- Para criar/recriar o banco MySQL `veiculos_db`, execute `py -3 -m app.db.init_db`.

## Autenticacao

Fluxo:
1. Cadastro cria usuario em `users`.
2. Senha e armazenada com hash de `email_normalizado + ":" + senha`.
3. Login valida esse hash.
4. JWT inclui `sub`, `role`, `cred_fingerprint`, `dados_base64`, `iat`, `exp`.
5. RBAC valida assinatura, expiracao, integridade do Base64 e fingerprint atual da credencial.
6. Tentativas de autenticacao sao registradas em `logs_auth` (sucesso/falha).

## Veiculos e metricas

Cadastro (`POST /api/v1/veiculos`) grava:
- `marcas` (se nao existir)
- `modelos` (se nao existir para a marca)
- `versoes` (se nao existir)
- `veiculos`
- `metricas_veiculos`

Consulta (`POST /api/v1/veiculos/comparar`) busca por `marca/modelo/versao` e retorna dados tecnicos + metrica mais recente.

## Upload Excel

Endpoint: `POST /api/v1/uploads/excel`

Regras:
- exige Bearer token
- aceita apenas `.xlsx` e `.xls`
- valida MIME e tamanho
- salva arquivo em `UPLOAD_DIR`
- registra evento em `logs` apenas quando existe `metrica_veiculo` vinculada ao usuario

## Configuracao

Use `.env` (ou variaveis de ambiente), com base em `.env.example`.

Principal:
- `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`
- `DATABASE_URL` (opcional; sobrescreve os campos `DB_*`)
- `SECRET_KEY`
- `ALGORITHM`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `UPLOAD_DIR`
- `MAX_UPLOAD_FILE_SIZE_MB`

## Execucao

```bash
py -3 -m pip install -r requirements.txt
py -3 -m app.db.init_db
py -3 run.py
```

Teste de conexao:

```bash
curl http://127.0.0.1:8000/health/db
```
