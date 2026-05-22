# Projeto Base - Sistema Veiculos (SOA + Cyber)

Aplicacao web e API em Python (FastAPI) com:
- cadastro/login de usuarios
- autenticacao JWT com payload em Base64
- cadastro e consulta de veiculos
- upload simples de Excel
- processamento estruturado de Excel para alimentar catalogo
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

Observacao de contrato:
- `metricas_veiculos.preco_sugerido` permite `NULL` para cenarios de importacao com preco pendente.

## Upload Excel

### Upload simples

Endpoint: `POST /api/v1/uploads/excel`

Regras:
- exige Bearer token
- aceita apenas `.xlsx` e `.xls`
- valida MIME e tamanho
- salva arquivo em `UPLOAD_DIR`
- registra evento em `logs` apenas quando existe `metrica_veiculo` vinculada ao usuario

### Processamento estruturado (catalogo)

Endpoint: `POST /api/v1/uploads/excel/processar`

Regras:
- exige Bearer token com perfil `admin` ou `analista`
- aceita apenas `.xlsx` para parse estruturado
- exige aba `BASE` com primeira coluna `Equipamentos`
- trata cada coluna de versao como uma configuracao de veiculo do mesmo modelo
- executa `upsert` em `marcas -> modelos -> versoes -> veiculos`
- cria sempre nova linha historica em `metricas_veiculos` (sem sobrescrever snapshots anteriores)
- registra log por metrica criada com acao `IMPORTACAO_EXCEL_PROCESSADA`
- fallback de marca: tenta detectar na planilha e, se nao encontrar, usa `FORD`

Resposta de sucesso:
- `status`
- `mensagem`
- `marca`
- `modelo`
- `versoes_processadas`
- `veiculos_criados`
- `metricas_criadas`
- `erros_validacao` (lista vazia no sucesso)

Resposta de erro de validacao (`400`):
- `detail.mensagem`
- `detail.erros_validacao`

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
