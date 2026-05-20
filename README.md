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
- `modelos`
- `versoes`
- `veiculos`
- `metricas_veiculos`
- `logs`
- `password_reset_tokens`

O SQL de criacao esta em [tabelas.sql](C:/Users/e44402854814/Desktop/sprint/sprintSoaCyber/projeto_inteligencia_automotiva_SOA_v2/tabelas.sql).

## Autenticacao

Fluxo:
1. Cadastro cria usuario em `users`.
2. Senha e armazenada com hash de `email_normalizado + ":" + senha`.
3. Login valida esse hash.
4. JWT inclui `sub`, `role`, `cred_fingerprint`, `dados_base64`, `iat`, `exp`.
5. RBAC valida assinatura, expiracao, integridade do Base64 e fingerprint atual da credencial.

## Veiculos e metricas

Cadastro (`POST /api/v1/veiculos`) grava:
- `modelos` (se nao existir)
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
- registra evento em `logs` (vinculado a `metricas_veiculos` e `users`)

## Configuracao

Use `.env` (ou variaveis de ambiente), com base em `.env.example`.

Principal:
- `DATABASE_URL` (padrao local: `sqlite:///./sistema_veiculos.db`)
- `SECRET_KEY`
- `ALGORITHM`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `UPLOAD_DIR`
- `MAX_UPLOAD_FILE_SIZE_MB`

## Execucao

```bash
py -3 -m pip install -r requirements.txt
py -3 run.py
```

## Seeds no startup

- `admin_bradesco@sistema.local` / `SenhaForte123`
- `analista_mercado@sistema.local` / `Analise789`
- Base Ford Ranger Raptor em `modelos/versoes/veiculos/metricas_veiculos`
