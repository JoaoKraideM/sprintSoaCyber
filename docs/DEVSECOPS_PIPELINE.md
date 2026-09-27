# Pipeline DevSecOps Integrado — Sprint 3 (Ford Challenge)

Este documento apresenta a implementação do Pipeline DevSecOps da Sprint 3 de Cybersecurity do projeto Ford Challenge.

O objetivo é demonstrar como controles de segurança foram incorporados ao ciclo de desenvolvimento, desde o commit ou Pull Request até a validação da aplicação antes de sua integração.

O workflow oficial está localizado em:

`.github/workflows/devsecops-pipeline.yml`

O pipeline é executado automaticamente em:

- `push` para a branch `main`;
- `push` para a branch `develop`;
- `pull_request` direcionado para `main`;
- `pull_request` direcionado para `develop`.

Também pode ser executado manualmente pelo GitHub Actions através de `workflow_dispatch`.

---

## Diagrama do pipeline

```mermaid
flowchart TD
    dev[Commit / Pull Request] --> testes[Testes automatizados<br/>pytest]

    testes --> sast[SAST<br/>Bandit]
    testes --> sca[SCA<br/>pip-audit]
    testes --> container[Container Security<br/>Docker + Trivy]

    dev --> secrets[Secret Scanning<br/>Gitleaks]

    sast --> resultado[Resultado DevSecOps]
    sca --> resultado
    secrets --> resultado
    container --> resultado

    sast -->|Falha de segurança| bloqueio[Bloqueio do pipeline]
    sca -->|Dependência vulnerável| bloqueio
    secrets -->|Secret encontrado| bloqueio
    container -->|Configuração crítica| bloqueio

    resultado --> gate{Resultado final}
    gate -->|Sucesso| aprovado[Pipeline aprovado]
    gate -->|Falha| correcao[Correção necessária]