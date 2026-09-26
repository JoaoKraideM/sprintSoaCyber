# Compliance, Riscos e Segurança Contínua — Sprint 3

Entrega separada exigida pelo Passo 2.5 do Sprint 3 (Cybersecurity).

## 1. Revisão de riscos (STRIDE + DevSecOps)

| Categoria STRIDE | Ameaça considerada | Controle implementado no código |
|---|---|---|
| **S**poofing | Falsificação de identidade / uso de credencial de terceiro | Hash bcrypt do material `email+senha`, JWT assinado (`HS256`), `cred_fingerprint` amarra o token ao hash atual da senha (invalida sessões antigas após troca de senha) |
| **T**ampering | Alteração de payload em trânsito | Assinatura HMAC opcional de payload (`X-Payload-Signature`/`X-Payload-Timestamp`), CSP e cabeçalhos de segurança no middleware |
| **R**epudiation | Usuário nega ter realizado uma ação | Eventos de domínio auditados em `logs`/`logs_auth` com usuário, IP e user-agent (pseudonimizados) |
| **I**nformation Disclosure | Vazamento de dados sensíveis (senha, PII, stack trace) | Senhas nunca retornadas pela API; exceções genéricas ao cliente; PII pseudonimizada em auditoria; uploads criptografados em repouso |
| **D**enial of Service | Payload flooding / força bruta | Rate limiting por IP (30 req/60s), limite de `Content-Length`, limite de linhas/colunas de planilha |
| **E**levation of Privilege | Usuário comum vira admin | Cadastro público sempre cria `role=user`; troca de role só via endpoint `admin`-only; RBAC valida perfil em cada endpoint sensível |

**Achado real desta revisão:** o arquivo `.env` entregue junto ao código continha
segredos reais em texto puro (`DB_PASSWORD`, `SECRET_KEY`, `PAYLOAD_SECRET_HMAC`,
`DATA_ENCRYPTION_KEY`). Isso é uma falha de **Information Disclosure** categoria
STRIDE identificada nesta própria revisão — tratada como incidente real, não
hipotético. Ação: rotacionar as credenciais imediatamente e nunca reincluir
`.env` em pacotes de entrega (o arquivo já está listado em `.gitignore`, mas
`.gitignore` só protege o `git`, não protege um `.zip` exportado manualmente).

## 2. Mapeamento com normas e boas práticas

### OWASP API Security Top 10

| Item OWASP API Top 10 | Status | Onde |
|---|---|---|
| API1 Broken Object Level Authorization | Mitigado | RBAC por `veiculo_id`/`user_id` em `deps.py` |
| API2 Broken Authentication | Mitigado | JWT + `cred_fingerprint` + verificação de usuário ativo |
| API3 Broken Object Property Level Authorization | Mitigado | Schemas Pydantic restringem campos aceitos por endpoint |
| API4 Unrestricted Resource Consumption | Mitigado | Rate limiting, limite de payload, limite de linhas/colunas de Excel |
| API5 Broken Function Level Authorization | Mitigado | `verificar_rbac([...])` por rota (`admin` vs `analista` vs `user`) |
| API6 Unrestricted Access to Sensitive Business Flows | Parcial | Falta throttling específico por *usuário* (hoje é só por IP) |
| API7 Server Side Request Forgery | N/A | API não faz requisições a URLs fornecidas pelo cliente |
| API8 Security Misconfiguration | Mitigado | CSP, HSTS, `X-Frame-Options`, docs OpenAPI self-hosted (sem CDN externo) |
| API9 Improper Inventory Management | Parcial | Não há versionamento explícito de API além do prefixo `/api/v1` |
| API10 Unsafe Consumption of APIs | N/A | Sem integrações de saída com APIs de terceiros |

### OWASP ASVS (nível 1, aplicável a este projeto)

- V2 (Autenticação): ✅ hashing forte, expiração de token, revogação por troca de senha.
- V4 (Controle de acesso): ✅ RBAC centralizado em `verificar_rbac`.
- V5 (Validação/Sanitização): ✅ Pydantic + `sanitizar_string`/`normalizar_email`.
- V7 (Tratamento de erros/logging): ✅ exceções genéricas ao cliente, log interno detalhado.
- V9 (Comunicação): ⚠️ Parcial — TLS suportado via `FORCE_HTTPS`/certificado, mas não é
  obrigatório por padrão; recomenda-se `FORCE_HTTPS=true` em produção.
- V14 (Configuração): ⚠️ Parcial — ver achado do `.env` na seção 1.

### LGPD

- Minimização e pseudonimização de dados pessoais em auditoria (`ANONYMIZE_AUDIT_PII`).
- Direito à eliminação/retenção: rotina de expurgo configurável
  (`AUDIT_LOG_RETENTION_DAYS`, `AUTH_LOG_RETENTION_DAYS`, `UPLOAD_RETENTION_DAYS`)
  executável via `POST /api/v1/admin/retencao/expurgar`.
- Criptografia de dados em repouso para arquivos enviados pelo usuário.
- **Pendente:** um registro formal de operações de tratamento de dados (RIPD/relatório
  de impacto) e uma política de privacidade voltada ao titular dos dados — fora do
  escopo do código, mas exigido para conformidade real com a LGPD.

## 3. Plano de segurança contínua

| Rotina | Frequência sugerida | Ferramenta/mecanismo |
|---|---|---|
| Revisão de dependências (SCA) | A cada PR + semanal agendado | `pip-audit` no pipeline (`.github/workflows/devsecops-pipeline.yml`) |
| Testes de segurança (SAST) | A cada PR | `bandit` no pipeline |
| Auditoria de permissões (roles) | Mensal | Consultar `GET /api/v1/admin/usuarios`, revisar quem tem `role=admin` |
| Secret scanning | A cada PR + no histórico completo | `gitleaks` no pipeline |
| Backup e recuperação | Diário (backup) / trimestral (teste de restauração) | Dump do MySQL + backup de `UPLOAD_DIR` (ver `docs/INCIDENT_RESPONSE_PLAYBOOK.md`) |
| Rotação de segredos (`SECRET_KEY`, `PAYLOAD_SECRET_HMAC`, `DATA_ENCRYPTION_KEY`, `DB_PASSWORD`) | A cada incidente confirmado + no mínimo anual | Manual, via variáveis de ambiente do orquestrador |

## 4. Checklist de conformidade (resumo executivo)

- [x] Autenticação forte (bcrypt + JWT + fingerprint de credencial)
- [x] RBAC por perfil em todos os endpoints sensíveis
- [x] Rate limiting e limite de payload
- [x] Cabeçalhos de segurança HTTP (CSP, HSTS, X-Frame-Options, etc.)
- [x] Criptografia de uploads em repouso
- [x] Pseudonimização de PII em logs de auditoria
- [x] Testes automatizados cobrindo autenticação, RBAC e CRUD (19/19 passando)
- [x] SAST, SCA, Secret Scanning e Container Scanning configurados em pipeline CI
- [x] Dockerfile com usuário não-root e sem segredos embutidos (IaC)
- [ ] `.env` com segredos reais removido do pacote de entrega e credenciais rotacionadas
      **(ação pendente do time — ver seção 1)**
- [ ] Dashboard de observabilidade externo (Grafana/Kibana) com prints reais
      **(ação pendente — hoje só existe o painel interno `/admin`)**
- [ ] `FORCE_HTTPS=true` habilitado por padrão em ambiente de apresentação/produção
