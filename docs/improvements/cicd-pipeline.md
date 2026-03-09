# GitHub Actions デプロイパイプライン

ステータス: **完了**（2026-03-09）

---

## なぜやるか

- 手動デプロイ（SSH + rsync + docker build）は手順が多く間違えやすい
- ローカルに Docker が不要になる
- git push だけでデプロイが完了する

## 何をしたか

- GitHub Actions OIDC による AWS 認証（静的クレデンシャル不要）
- Docker build → ECR push → SSM Run Command による EC2 デプロイ
- Terraform で OIDC プロバイダ + IAM ロール + SSM 権限を構築
- EC2 `user_data` bootstrap と SSM Parameter Store 前提で `.env` を再生成する構成へ整理

## 変更ファイル

- `.github/workflows/deploy.yml`
- `terraform/modules/github_actions/`（新規モジュール）
- `terraform/modules/iam/main.tf`（SSM 権限追加）
- `scripts/setup-ec2.sh`（EC2 初期セットアップ）

## 詳細手順

[docs/guides/06-github-actions-cicd.md](../guides/06-github-actions-cicd.md)

補足:

- 実運用の apply 順序は `production-config` → `production`
- `DJANGO_SECRET_KEY` と `POSTGRES_PASSWORD` は `production-config` 側で SSM に入れる
- deploy 前チェックは [docs/guides/07-terraform-apply.md](../guides/07-terraform-apply.md) と [docs/guides/08-current-cd-flow.md](../guides/08-current-cd-flow.md) を正本とする
