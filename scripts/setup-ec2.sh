#!/bin/bash
# EC2 初期セットアップスクリプト
# terraform apply 後に1回だけ実行する
#
# 使い方:
#   bash scripts/setup-ec2.sh
#
# 前提:
#   - terraform apply 済み
#   - SSH鍵 ~/.ssh/school-diary-key.pem が存在
#   - scripts/generate-env.sh で .envs を生成済み

set -euo pipefail

TF_DIR="terraform/environments/production"
EC2_IP=$(cd "$TF_DIR" && terraform output -raw ec2_public_ip)
SSH_KEY="$HOME/.ssh/school-diary-key.pem"
SSH_OPTS="-i $SSH_KEY -o StrictHostKeyChecking=no"

echo "EC2 IP: $EC2_IP"

# 1. EC2上にアプリディレクトリ作成
echo "--- EC2 ディレクトリ準備 ---"
ssh $SSH_OPTS ubuntu@$EC2_IP "sudo mkdir -p /opt/app && sudo chown ubuntu:ubuntu /opt/app"

# 2. docker-compose.production.yml と .envs を転送
echo "--- ファイル転送 ---"
scp $SSH_OPTS docker-compose.production.yml ubuntu@$EC2_IP:/opt/app/
scp -r $SSH_OPTS .envs ubuntu@$EC2_IP:/opt/app/

# 3. SSM Agent の起動確認
echo "--- SSM Agent 確認 ---"
ssh $SSH_OPTS ubuntu@$EC2_IP "sudo snap install amazon-ssm-agent 2>/dev/null || true && sudo systemctl enable snap.amazon-ssm-agent.amazon-ssm-agent.service && sudo systemctl start snap.amazon-ssm-agent.amazon-ssm-agent.service && sudo systemctl status snap.amazon-ssm-agent.amazon-ssm-agent.service --no-pager | head -5"

# 4. swap 設定（メモリ対策）
echo "--- Swap 設定 ---"
ssh $SSH_OPTS ubuntu@$EC2_IP "if [ ! -f /swapfile ]; then sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile && echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab; echo 'Swap created'; else echo 'Swap already exists'; fi"

echo ""
echo "=== EC2 セットアップ完了 ==="
echo "次のステップ:"
echo "  1. GitHub Secrets を設定"
echo "  2. git push で GitHub Actions がトリガーされる"
echo "  3. または手動: Actions タブ → Run workflow"
