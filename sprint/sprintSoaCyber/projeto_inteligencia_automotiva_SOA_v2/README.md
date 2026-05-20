# Projeto Base - Inteligencia Competitiva Automotiva (SOA + Cyber)

Aplicacao web e API em Python para:
- cadastro de usuarios por email
- autenticacao com JWT
- upload de arquivos Excel com trilha de auditoria
- consulta/cadastro de veiculos do desafio

## Arquitetura

Estrutura em camadas:
- **Apresentacao**: endpoints FastAPI + site web em `/`
- **Servico**: regras de autenticacao, validacoes e upload em `app/services`
- **Dados**: modelos SQLAlchemy e sessao em `app/models` e `app/db`

## Fluxo de autenticacao

1. Cadastro recebe `email` e `senha`.
2. O hash salvo no banco e gerado com material `email_normalizado + ":" + senha`.
3. Login valida `email + senha` contra o hash.
4. JWT e emitido com:
   - `sub` (email)
   - `role`
   - `cred_fingerprint` (sha256 do hash armazenado)
   - `dados_base64` (payload em Base64)
   - `iat` e `exp`
5. Na validacao do token:
   - assinatura e expiracao (`exp`) sao verificadas
   - `dados_base64` e conferido contra payload JWT
   - fingerprint do token e comparado com o hash atual do usuario no banco

## Upload de Excel

Endpoint: `POST /api/v1/uploads/excel`

Regras:
- exige `Bearer token`
- aceita apenas `.xlsx` e `.xls`
- valida MIME type permitido
- valida tamanho maximo (`MAX_UPLOAD_FILE_SIZE_MB`)
- salva arquivo em `UPLOAD_DIR`
- registra log em `logs_upload`
- registra auditoria em `logs_auditoria`

## Endpoints principais

- `POST /api/v1/auth/register` - cria usuario (role fixa `usuario` no cadastro publico)
- `POST /api/v1/auth/login` - autentica e retorna JWT
- `POST /api/v1/uploads/excel` - upload autenticado
- `POST /api/v1/veiculos/comparar` - consulta tecnica
- `POST /api/v1/veiculos` - cadastro de veiculo (admin)

## Interface web

Acesse:
- `GET /` - pagina unica com cadastro, login e upload

## Configuracao

Use `.env` (ou variaveis de ambiente). Exemplo em `.env.example`.

Principais chaves:
- `DATABASE_URL` (padrao fake/local: `sqlite:///./inteligencia_automotiva.db`)
- `SECRET_KEY`
- `ALGORITHM`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `MAX_CONTENT_LENGTH_KB`
- `UPLOAD_DIR`
- `MAX_UPLOAD_FILE_SIZE_MB`
- `ALLOWED_UPLOAD_EXTENSIONS`
- `ALLOWED_UPLOAD_CONTENT_TYPES`

## Execucao

```bash
pip install -r requirements.txt
python run.py
```

## Seeds iniciais

No startup sao criados:
- `admin_bradesco@sistema.local` / `SenhaForte123`
- `analista_mercado@sistema.local` / `Analise789`

## Observacoes de seguranca

- sanitizacao de entrada para campos textuais
- tratamento global de excecoes sem expor stack trace
- rate limit por IP
- limite de payload
- cabecalhos de seguranca HTTP (CSP, X-Frame-Options, etc.)
- trilha de auditoria para eventos criticos
