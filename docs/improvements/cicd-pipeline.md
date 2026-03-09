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

## 変更ファイル

- `.github/workflows/deploy.yml`
- `terraform/modules/github_actions/`（新規モジュール）
- `terraform/modules/iam/main.tf`（SSM 権限追加）
- `scripts/setup-ec2.sh`（EC2 初期セットアップ）

## 詳細手順

[docs/guides/06-github-actions-cicd.md](../guides/06-github-actions-cicd.md)
