#!/bin/bash

set -Eeuo pipefail

APP_DIR="${APP_DIR:-/opt/app}"
ENV_DIR="${APP_DIR}/.envs/.production"
PARAMETER_PREFIX="${PARAMETER_PREFIX:?PARAMETER_PREFIX is required}"
AWS_REGION="${AWS_REGION:?AWS_REGION is required}"
WAIT_RETRIES="${WAIT_RETRIES:-60}"
WAIT_SECONDS="${WAIT_SECONDS:-10}"

log() {
  printf '[render-env] %s\n' "$1"
}

get_param() {
  local name="$1"
  aws ssm get-parameter \
    --region "${AWS_REGION}" \
    --with-decryption \
    --name "${name}" \
    --query 'Parameter.Value' \
    --output text
}

wait_for_parameter() {
  local name="$1"
  local attempt

  for attempt in $(seq 1 "${WAIT_RETRIES}"); do
    if get_param "${name}" >/dev/null 2>&1; then
      return 0
    fi

    log "waiting for parameter ${name} (${attempt}/${WAIT_RETRIES})"
    sleep "${WAIT_SECONDS}"
  done

  return 1
}

add_env() {
  local file_path="$1"
  local key="$2"
  local value="$3"
  printf '%s=%s\n' "${key}" "${value}" >> "${file_path}"
}

mkdir -p "${ENV_DIR}"
wait_for_parameter "${PARAMETER_PREFIX}/django/DJANGO_SECRET_KEY"

DJANGO_FILE="${ENV_DIR}/.django"
POSTGRES_FILE="${ENV_DIR}/.postgres"

: > "${DJANGO_FILE}"
{
  echo "# General"
  echo "# ------------------------------------------------------------------------------"
} >> "${DJANGO_FILE}"
add_env "${DJANGO_FILE}" "DJANGO_SETTINGS_MODULE" "$(get_param "${PARAMETER_PREFIX}/django/DJANGO_SETTINGS_MODULE")"
add_env "${DJANGO_FILE}" "DJANGO_SECRET_KEY" "$(get_param "${PARAMETER_PREFIX}/django/DJANGO_SECRET_KEY")"
add_env "${DJANGO_FILE}" "DJANGO_ADMIN_URL" "$(get_param "${PARAMETER_PREFIX}/django/DJANGO_ADMIN_URL")"
add_env "${DJANGO_FILE}" "DJANGO_ALLOWED_HOSTS" "$(get_param "${PARAMETER_PREFIX}/django/DJANGO_ALLOWED_HOSTS")"
add_env "${DJANGO_FILE}" "DJANGO_SITE_URL" "$(get_param "${PARAMETER_PREFIX}/django/DJANGO_SITE_URL")"
{
  echo
  echo "# Security"
  echo "# ------------------------------------------------------------------------------"
} >> "${DJANGO_FILE}"
add_env "${DJANGO_FILE}" "DJANGO_SECURE_SSL_REDIRECT" "$(get_param "${PARAMETER_PREFIX}/django/DJANGO_SECURE_SSL_REDIRECT")"
{
  echo
  echo "# Email"
  echo "# ------------------------------------------------------------------------------"
} >> "${DJANGO_FILE}"
add_env "${DJANGO_FILE}" "DJANGO_DEFAULT_FROM_EMAIL" "$(get_param "${PARAMETER_PREFIX}/django/DJANGO_DEFAULT_FROM_EMAIL")"
add_env "${DJANGO_FILE}" "DJANGO_SERVER_EMAIL" "$(get_param "${PARAMETER_PREFIX}/django/DJANGO_SERVER_EMAIL")"
{
  echo
  echo "# Database (RDS)"
  echo "# ------------------------------------------------------------------------------"
} >> "${DJANGO_FILE}"
{
  echo
  echo "# AWS"
  echo "# ------------------------------------------------------------------------------"
} >> "${DJANGO_FILE}"
add_env "${DJANGO_FILE}" "DJANGO_AWS_STORAGE_BUCKET_NAME" "$(get_param "${PARAMETER_PREFIX}/django/DJANGO_AWS_STORAGE_BUCKET_NAME")"
add_env "${DJANGO_FILE}" "DJANGO_AWS_S3_REGION_NAME" "$(get_param "${PARAMETER_PREFIX}/django/DJANGO_AWS_S3_REGION_NAME")"
add_env "${DJANGO_FILE}" "AWS_REGION" "$(get_param "${PARAMETER_PREFIX}/django/AWS_REGION")"
add_env "${DJANGO_FILE}" "AWS_DEFAULT_REGION" "$(get_param "${PARAMETER_PREFIX}/django/AWS_DEFAULT_REGION")"
add_env "${DJANGO_FILE}" "AWS_SES_REGION" "$(get_param "${PARAMETER_PREFIX}/django/AWS_SES_REGION")"
{
  echo
  echo "# django-allauth"
  echo "# ------------------------------------------------------------------------------"
} >> "${DJANGO_FILE}"
add_env "${DJANGO_FILE}" "DJANGO_ACCOUNT_ALLOW_REGISTRATION" "$(get_param "${PARAMETER_PREFIX}/django/DJANGO_ACCOUNT_ALLOW_REGISTRATION")"
{
  echo
  echo "# Gunicorn"
  echo "# ------------------------------------------------------------------------------"
} >> "${DJANGO_FILE}"
add_env "${DJANGO_FILE}" "WEB_CONCURRENCY" "$(get_param "${PARAMETER_PREFIX}/django/WEB_CONCURRENCY")"

: > "${POSTGRES_FILE}"
{
  echo "# PostgreSQL (RDS)"
  echo "# ------------------------------------------------------------------------------"
} >> "${POSTGRES_FILE}"
add_env "${POSTGRES_FILE}" "POSTGRES_HOST" "$(get_param "${PARAMETER_PREFIX}/postgres/POSTGRES_HOST")"
add_env "${POSTGRES_FILE}" "POSTGRES_PORT" "$(get_param "${PARAMETER_PREFIX}/postgres/POSTGRES_PORT")"
add_env "${POSTGRES_FILE}" "POSTGRES_DB" "$(get_param "${PARAMETER_PREFIX}/postgres/POSTGRES_DB")"
add_env "${POSTGRES_FILE}" "POSTGRES_USER" "$(get_param "${PARAMETER_PREFIX}/postgres/POSTGRES_USER")"
add_env "${POSTGRES_FILE}" "POSTGRES_PASSWORD" "$(get_param "${PARAMETER_PREFIX}/postgres/POSTGRES_PASSWORD")"

log "rendered ${DJANGO_FILE} and ${POSTGRES_FILE}"
