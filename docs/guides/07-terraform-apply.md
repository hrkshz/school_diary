# Terraform による全環境構築

## なぜやるか

「Terraform でインフラをコード管理している」だけでなく、「destroy して apply すれば再構築できる」状態にすることが IaC の本質。コスト削減のために一時的に環境を落とし、必要なときに再構築するフローを確立する。

## 全体の流れ

```
terraform apply（インフラ構築）
  → generate-env.sh（環境変数生成）
  → setup-ec2.sh（EC2 初期設定）
  → GitHub Secrets 設定
  → git push（GitHub Actions でデプロイ）
```

## 手順

### 手順 1: terraform apply

```bash
cd terraform/environments/production
terraform plan    # 変更内容を確認
terraform apply   # 実行（確認プロンプトで yes）
```

今回の場合、61 リソースが新規作成された（全環境再構築）。
所要時間: 約 15 分（RDS と CloudFront の作成が長い）。

### 手順 2: 出力値の確認

```bash
terraform output
```

重要な出力:
- `ec2_public_ip`: EC2 のパブリック IP
- `alb_dns_name`: ALB の DNS 名
- `cloudfront_domain_name`: CloudFront のドメイン
- `github_actions_role_arn`: GitHub Actions 用 IAM ロール ARN

### 手順 3: セキュリティグループの IP 更新

SSH 接続元の IP が変わっている場合、`terraform.tfvars` の `admin_ip` を更新:

```bash
# 現在の IP を確認
curl -s https://checkip.amazonaws.com

# terraform.tfvars を更新
admin_ip = "xxx.xxx.xxx.xxx/32"

# セキュリティグループだけ更新
terraform apply -target=module.security_groups
```

### 手順 4: 環境変数の自動生成

```bash
cd ../../..  # プロジェクトルートに戻る
bash scripts/generate-env.sh
```

### 手順 5: EC2 セットアップ

```bash
bash scripts/setup-ec2.sh
```

実行内容:
- docker-compose.production.yml と .envs を EC2 に転送
- SSM Agent の起動確認
- swap の設定

### 手順 6: GitHub Secrets の設定

GitHub リポジトリ → Settings → Secrets → Actions:
- `AWS_ROLE_ARN`: terraform output の `github_actions_role_arn`
- `EC2_INSTANCE_ID`: EC2 インスタンス ID

### 手順 7: デプロイ

```bash
git push github main
# → GitHub Actions が自動でビルド・デプロイ
```

## 注意事項

### CloudFront のドメイン名が変わる

CloudFront distribution を削除・再作成すると、ドメイン名（`dXXXXXXXXXX.cloudfront.net`）が変わる。
ブックマークやドキュメントの URL を更新する必要がある。

### RDS のパスワード

terraform.tfvars のパスワードが正しいか確認する。
新しい RDS インスタンスは tfvars のパスワードで作成される。

### State の管理

現在は local state。`terraform.tfstate` を失うと、既存リソースとの対応が取れなくなる。
本番運用では S3 backend + DynamoDB lock を推奨。

## ブログで深掘りできるポイント

- terraform apply の実行計画（Plan）の読み方
- State ファイルの役割と管理方法
- `terraform destroy` → `terraform apply` のサイクルとコスト最適化
- モジュール間の依存関係（module.alb が module.ec2.instance_id を参照する等）
- `-target` オプションの使いどころと注意点
