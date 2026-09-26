#!/usr/bin/env bash
# Rotina de backup do banco de dados (Compliance / Seguranca Continua - Sprint 3).
#
# Uso:
#   ./scripts/backup_db.sh
#
# Agendamento sugerido (cron diario as 02:00, mantendo 30 dias de historico):
#   0 2 * * * /caminho/para/sprintSoaCyber/scripts/backup_db.sh >> /var/log/backup_veiculos_db.log 2>&1
#
# Variaveis lidas do .env do projeto (nao commitar segredos).

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${PROJECT_DIR}/.env"
BACKUP_DIR="${PROJECT_DIR}/data/backups"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"

if [ -f "$ENV_FILE" ]; then
  # shellcheck disable=SC1090
  set -a; source "$ENV_FILE"; set +a
fi

DB_HOST="${DB_HOST:-127.0.0.1}"
DB_PORT="${DB_PORT:-3306}"
DB_USER="${DB_USER:-root}"
DB_PASSWORD="${DB_PASSWORD:?DB_PASSWORD nao configurado no .env}"
DB_NAME="${DB_NAME:-veiculos_db}"

mkdir -p "$BACKUP_DIR"
DUMP_FILE="${BACKUP_DIR}/${DB_NAME}_${TIMESTAMP}.sql.gz"

echo "[backup] iniciando dump de ${DB_NAME} em ${DUMP_FILE}"
mysqldump \
  --host="$DB_HOST" \
  --port="$DB_PORT" \
  --user="$DB_USER" \
  --password="$DB_PASSWORD" \
  --single-transaction \
  --routines \
  --triggers \
  "$DB_NAME" | gzip > "$DUMP_FILE"

echo "[backup] dump concluido: $(du -h "$DUMP_FILE" | cut -f1)"

echo "[backup] removendo backups com mais de ${RETENTION_DAYS} dias"
find "$BACKUP_DIR" -name "${DB_NAME}_*.sql.gz" -mtime "+${RETENTION_DAYS}" -delete

echo "[backup] rotina finalizada com sucesso"
