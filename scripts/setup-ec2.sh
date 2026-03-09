#!/bin/bash
# EC2 bootstrap 検証スクリプト
# user_data による初期化結果を SSH で補助確認する
# 正本の deploy 経路は GitHub Actions + SSM Run Command

set -euo pipefail

TF_DIR="terraform/environments/production"
EC2_IP=$(cd "$TF_DIR" && terraform output -raw ec2_public_ip)
SSH_KEY="$HOME/.ssh/school-diary-key.pem"
SSH_OPTS="-i $SSH_KEY -o StrictHostKeyChecking=no"

echo "EC2 IP: $EC2_IP"

# 1. bootstrap ファイル確認
echo "--- EC2 bootstrap ファイル確認 ---"
ssh $SSH_OPTS ubuntu@$EC2_IP "sudo ls -la /opt/app && sudo ls -la /opt/app/bin && sudo ls -la /opt/app/.envs/.production"

# 2. SSM Agent の起動確認
echo "--- SSM Agent 確認 ---"
ssh $SSH_OPTS ubuntu@$EC2_IP "sudo snap install amazon-ssm-agent 2>/dev/null || true && sudo systemctl enable snap.amazon-ssm-agent.amazon-ssm-agent.service && sudo systemctl start snap.amazon-ssm-agent.amazon-ssm-agent.service && sudo systemctl status snap.amazon-ssm-agent.amazon-ssm-agent.service --no-pager | head -5"

# 3. user_data ログ確認
echo "--- user_data ログ ---"
ssh $SSH_OPTS ubuntu@$EC2_IP "sudo tail -n 50 /var/log/user-data.log"

echo ""
echo "=== EC2 bootstrap 確認完了 ==="
echo "次のステップ:"
echo "  1. production-config -> production の順で apply 済みか確認"
echo "  2. bootstrap の結果を補助確認"
echo "  3. 必要なら Actions タブから Run workflow"
