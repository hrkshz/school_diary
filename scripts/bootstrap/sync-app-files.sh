#!/bin/bash

set -Eeuo pipefail

APP_DIR="${APP_DIR:-/opt/app}"
BIN_DIR="${APP_DIR}/bin"
GITHUB_REPOSITORY="${GITHUB_REPOSITORY:?GITHUB_REPOSITORY is required}"
REF="${1:-${GITHUB_REF:-main}}"
RAW_BASE_URL="https://raw.githubusercontent.com/${GITHUB_REPOSITORY}/${REF}"

log() {
  printf '[bootstrap] %s\n' "$1"
}

download() {
  local source_path="$1"
  local destination_path="$2"

  curl -fsSL "${RAW_BASE_URL}/${source_path}" -o "${destination_path}"
}

mkdir -p "${APP_DIR}" "${BIN_DIR}" "${APP_DIR}/.envs/.production" "${APP_DIR}/.release"

log "syncing app files from ${GITHUB_REPOSITORY}@${REF}"
download "docker-compose.production.yml" "${APP_DIR}/docker-compose.production.yml"
download "scripts/ssm-deploy.sh" "${BIN_DIR}/ssm-deploy.sh"
download "scripts/bootstrap/render-env-from-ssm.sh" "${BIN_DIR}/render-env-from-ssm.sh"

chmod +x "${BIN_DIR}/ssm-deploy.sh" "${BIN_DIR}/render-env-from-ssm.sh"
log "app files synced"
