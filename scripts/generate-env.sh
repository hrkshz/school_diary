#!/bin/bash
# SSM Parameter Store から .envs/.production/ の環境変数を生成する

set -euo pipefail

AWS_REGION="${AWS_REGION:-ap-northeast-1}"
PARAMETER_PREFIX="${PARAMETER_PREFIX:-/school-diary/production}"
APP_DIR="${APP_DIR:-$(pwd)}"

APP_DIR="${APP_DIR}" \
AWS_REGION="${AWS_REGION}" \
PARAMETER_PREFIX="${PARAMETER_PREFIX}" \
bash scripts/bootstrap/render-env-from-ssm.sh
