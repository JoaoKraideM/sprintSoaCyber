# Observabilidade, Monitoramento e Resposta a Incidentes — Sprint 3

Entrega separada exigida pelo Passo 2.0 do Sprint 3 (Cybersecurity).

## 1. O que já existe no código (evidência atual)

- **Logs estruturados em banco relacional:**
  - `logs_auth`: toda tentativa de login (sucesso/falha), com IP e user-agent
    pseudonimizados por HMAC (`app/core/privacy.py`) quando `ANONYMIZE_AUDIT_PII=true`.
  - `logs`: eventos de domínio (cadastro, upload, processamento de Excel,
    cadastro/atualização/remoção de veículo, extração competitiva), publicados
    pelo `EventBus` (`app/services/event_bus.py`).
- **Falhas internas são logadas no servidor e nunca expostas ao cliente**
  (`app/core/middleware.py`, bloco de tratamento global de exceções).
- **Health check:** `GET /health/db`, usado pelo `HEALTHCHECK` do `Dockerfile`.
- **Painel administrativo (`/admin` e `GET /api/v1/admin/dashboard`):** consolida
  indicadores de usuários, catálogo e auditoria em tempo real.

## 2. O que faltava e precisa ser anexado como evidência separada

O código acima é a **fonte** dos dados de observabilidade, mas o Sprint 3 pede
also métricas/alertas e um dashboard de infraestrutura (Grafana/Kibana/Azure Monitor
ou equivalente) e um plano de resposta a incidentes documentado — nenhum dos dois
existia no pacote entregue. Este documento cobre a parte de plano; para o
dashboard visual, recomenda-se:

1. Exportar `logs` e `logs_auth` para um coletor (ex.: Grafana Loki, ELK/Kibana)
   ou, no mínimo, tirar prints do painel `/admin` em produção com dados reais.
2. Configurar alertas simples (ex.: mais de N falhas de login por IP em 5 min —
   já mitigado pelo rate limiting, mas o alerta deve ser visível a um humano).

## 3. Plano de monitoramento

| Sinal | Onde é coletado | Frequência | Ação em caso de anomalia |
|---|---|---|---|
| Falhas de autenticação por IP/usuário | `logs_auth` | Tempo real (rate limiting já bloqueia após 30 req/min) | Revisar IP em `logs_auth`, bloquear manualmente se recorrente |
| Erros 5xx | Log de aplicação (`logger.error` no middleware) | Tempo real | Investigar stack trace no servidor (nunca exposta ao cliente) |
| Uploads recusados (tamanho/tipo/MIME) | `logs` (evento de falha de upload) | Tempo real | Confirmar se é uso legítimo ou tentativa de abuso |
| Disponibilidade do banco | `GET /health/db` | Health check a cada 30s (Docker) | Reiniciar contêiner / alertar equipe de infra |
| Alteração de papel (role) de usuário | `logs` | Tempo real | Auditoria mensal de quem tem `role=admin` |

## 4. Plano de resposta a incidentes (Detecção → Análise → Contenção → Erradicação → Recuperação)

### Detecção
- Volume anômalo de falhas de login (`logs_auth.status = false`) para o mesmo `address` pseudonimizado.
- Repetidos `403` de RBAC vindos do mesmo usuário/IP (possível tentativa de escalonamento de privilégio).
- Alertas de `pip-audit`/`bandit`/`gitleaks`/`trivy` no pipeline DevSecOps (ver `docs/DEVSECOPS_PIPELINE.md`).

### Análise
- Consultar `logs_auth` e `logs` filtrando pelo IP/usuário pseudonimizado envolvido.
- Verificar se o token JWT relacionado ainda é válido (`exp`, `cred_fingerprint`).
- Confirmar se a assinatura HMAC de payload (`REQUIRE_PAYLOAD_SIGNATURE`) estava ativa no momento do incidente.

### Contenção
- Desativar a conta (`user.status = false`) via painel admin, invalidando o acesso imediatamente
  (o RBAC já rejeita usuários com `status=false`).
- Forçar redefinição de senha (`AuthService.criar_convite_senha`), o que invalida qualquer sessão
  antiga por causa do `cred_fingerprint` amarrado ao hash da senha.
- Se a suspeita for vazamento de `SECRET_KEY`/`PAYLOAD_SECRET_HMAC`/`DATA_ENCRYPTION_KEY`,
  rotacionar imediatamente essas chaves (isso invalida **todos** os tokens emitidos).

### Erradicação
- Corrigir a causa raiz (ex.: dependência vulnerável reportada pelo SCA, endpoint sem RBAC,
  segredo commitado — ver o achado real de `.env` documentado em `docs/DEVSECOPS_PIPELINE.md`).
- Rodar o pipeline DevSecOps novamente para confirmar que o achado não se repete.

### Recuperação
- Restaurar o funcionamento normal da conta/serviço.
- Comunicar ao usuário afetado (canal seguro), quando aplicável.
- Registrar o incidente e as ações tomadas em um log de pós-mortem (fora do escopo
  do banco de aplicação — recomenda-se um documento/planilha separado da equipe de segurança).

## 5. Rotina de backup e recuperação

- Banco de dados: dump programado (ex.: `mysqldump`) com retenção alinhada a
  `AUDIT_LOG_RETENTION_DAYS`/`UPLOAD_RETENTION_DAYS` já configuráveis no `.env.example`.
- Uploads criptografados em `UPLOAD_DIR`: incluir o diretório no backup, nunca a chave
  de criptografia (`DATA_ENCRYPTION_KEY`) junto do backup de dados — guardar a chave
  em um cofre de segredos separado (ex.: variável de ambiente do orquestrador, não em arquivo).
- Testar a restauração periodicamente (não só o backup em si).
