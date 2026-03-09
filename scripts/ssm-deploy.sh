#!/bin/bash

set -Eeuo pipefail

APP_DIR="/opt/app"
COMPOSE_FILE="docker-compose.production.yml"
SERVICE_NAME="django"
HEALTH_RETRIES="${HEALTH_RETRIES:-12}"
HEALTH_SLEEP_SECONDS="${HEALTH_SLEEP_SECONDS:-10}"
RELEASE_DIR="${APP_DIR}/.release"
CURRENT_RELEASE_FILE="${RELEASE_DIR}/current"
PREVIOUS_RELEASE_FILE="${RELEASE_DIR}/previous"
LAST_RUN_ID_FILE="${RELEASE_DIR}/last-run-id"
LAST_DEPLOY_SHA_FILE="${RELEASE_DIR}/last-deploy-sha"
DEPLOY_RUN_ID="${DEPLOY_RUN_ID:-unknown}"
DEPLOY_SHA="${DEPLOY_SHA:-${IMAGE_TAG:-unknown}}"

log() {
  printf '[deploy run=%s sha=%s] %s\n' "${DEPLOY_RUN_ID}" "${DEPLOY_SHA}" "$1"
}

dump_service_state() {
  log "docker compose ps (${SERVICE_NAME})"
  docker compose -f "${COMPOSE_FILE}" ps "${SERVICE_NAME}" || true

  log "recent container logs (${SERVICE_NAME})"
  docker compose -f "${COMPOSE_FILE}" logs --tail 100 "${SERVICE_NAME}" || true
}

service_container_id() {
  docker compose -f "${COMPOSE_FILE}" ps -q "${SERVICE_NAME}" 2>/dev/null || true
}

wait_for_service_health() {
  local attempt status container_id

  for attempt in $(seq 1 "${HEALTH_RETRIES}"); do
    container_id="$(service_container_id)"
    if [ -z "${container_id}" ]; then
      status="container-not-found"
    else
      status="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "${container_id}" 2>/dev/null || true)"
    fi
    log "health check attempt ${attempt}/${HEALTH_RETRIES}: ${status:-container-not-found}"

    if [ "${status}" = "healthy" ]; then
      return 0
    fi

    sleep "${HEALTH_SLEEP_SECONDS}"
  done

  return 1
}

rollback_to_latest() {
  local rollback_tag=""

  if [ -f "${CURRENT_RELEASE_FILE}" ]; then
    rollback_tag="$(tr -d '\n' < "${CURRENT_RELEASE_FILE}")"
  fi

  if [ -z "${rollback_tag}" ]; then
    log "no previously successful release recorded; skipping rollback"
    return 1
  fi

  log "rolling back to previously successful tag: ${rollback_tag}"
  export IMAGE_TAG="${rollback_tag}"

  docker compose -f "${COMPOSE_FILE}" pull "${SERVICE_NAME}"
  docker compose -f "${COMPOSE_FILE}" up -d "${SERVICE_NAME}"
  dump_service_state
}

record_successful_release() {
  mkdir -p "${RELEASE_DIR}"

  if [ -f "${CURRENT_RELEASE_FILE}" ]; then
    cp "${CURRENT_RELEASE_FILE}" "${PREVIOUS_RELEASE_FILE}"
  fi

  printf '%s\n' "${DEPLOY_RUN_ID}" > "${LAST_RUN_ID_FILE}"
  printf '%s\n' "${DEPLOY_SHA}" > "${LAST_DEPLOY_SHA_FILE}"
  printf '%s\n' "${IMAGE_TAG}" > "${CURRENT_RELEASE_FILE}"
  log "recorded successful release: ${IMAGE_TAG}"
}

main() {
  log "starting remote deploy"
  cd "${APP_DIR}"
  mkdir -p "${RELEASE_DIR}"

  : "${AWS_REGION:?AWS_REGION is required}"
  : "${ECR_REGISTRY:?ECR_REGISTRY is required}"
  : "${ECR_REPOSITORY:?ECR_REPOSITORY is required}"
  : "${IMAGE_TAG:?IMAGE_TAG is required}"

  log "target image: ${ECR_REGISTRY}/${ECR_REPOSITORY}:${IMAGE_TAG}"
  CURRENT_CONTAINER_ID="$(service_container_id)"
  if [ -n "${CURRENT_CONTAINER_ID}" ]; then
    CURRENT_IMAGE="$(docker inspect --format '{{.Config.Image}}' "${CURRENT_CONTAINER_ID}" 2>/dev/null || true)"
  else
    CURRENT_IMAGE=""
  fi
  log "current running image: ${CURRENT_IMAGE:-none}"

  log "logging in to ECR"
  aws ecr get-login-password --region "${AWS_REGION}" | docker login --username AWS --password-stdin "${ECR_REGISTRY}"

  export ECR_REGISTRY
  export ECR_REPOSITORY
  export IMAGE_TAG

  log "pulling target image"
  docker compose -f "${COMPOSE_FILE}" pull "${SERVICE_NAME}"

  log "running database migrations"
  docker compose -f "${COMPOSE_FILE}" run --rm "${SERVICE_NAME}" python manage.py migrate --noinput

  log "starting service"
  docker compose -f "${COMPOSE_FILE}" up -d "${SERVICE_NAME}"
  dump_service_state

  log "waiting for container health"
  if wait_for_service_health; then
    log "deploy successful"
    record_successful_release
  else
    log "health check failed before rollback"
    dump_service_state
    rollback_to_latest || true
    exit 1
  fi

  log "pruning unused docker images"
  docker image prune -f
  log "remote deploy completed"
}

main "$@"
