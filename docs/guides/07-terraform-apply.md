# Terraform による全環境構築

## なぜやるか

「Terraform でインフラをコード管理している」だけでなく、「destroy して apply すれば再構築できる」状態にすることが IaC の本質。コスト削減のために一時的に環境を落とし、必要なときに再構築するフローを確立する。

## 全体の流れ

```
terraform apply（production-config: 永続設定 / secret 登録）
  → terraform apply（production: インフラ構築 + 動的 SSM 更新）
  → user_data bootstrap（EC2 初期化 + env 生成 + 初回 deploy 試行）
  → setup-ec2.sh（bootstrap 検証）
  → GitHub Secrets 設定
  → git push（GitHub Actions でデプロイ）
```

## 手順

### 手順 1: production-config を apply

```bash
cd terraform/environments/production-config
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform plan
terraform apply
```

ここでは `terraform destroy` しても残したい値を SSM Parameter Store に登録する。

- `DJANGO_SECRET_KEY`
- `POSTGRES_PASSWORD`
- `DJANGO_ADMIN_URL`
- `WEB_CONCURRENCY`

重要:

- `django_secret_key` と `db_password` は `terraform/environments/production-config/terraform.tfvars` に設定する
- `terraform/environments/production/terraform.tfvars` に `django_secret_key` は入れない

### 手順 2: production を apply

```bash
cd terraform/environments/production
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform plan    # 変更内容を確認
terraform apply   # 実行（確認プロンプトで yes）
```

今回の場合、61 リソースが新規作成された（全環境再構築）。
所要時間: 約 15 分（RDS と CloudFront の作成が長い）。

`production` は `production-config` に保存済みの `POSTGRES_PASSWORD` を参照し、
ALB DNS / CloudFront / RDS endpoint など再生成値だけを SSM に更新する。

`production/terraform.tfvars` では、インフラ値に加えて次も確認しておく。

- `github_repo`
- `github_bootstrap_ref`
- `ses_sender_email`
- `cloudwatch_alarm_email`

### 手順 3: 出力値の確認

```bash
terraform output
```

重要な出力:
- `ec2_public_ip`: EC2 のパブリック IP
- `alb_dns_name`: ALB の DNS 名
- `cloudfront_domain_name`: CloudFront のドメイン
- `github_actions_role_arn`: GitHub Actions 用 IAM ロール ARN

### 手順 4: セキュリティグループの IP 更新

SSH 接続元の IP が変わっている場合、`terraform.tfvars` の `admin_ip` を更新:

```bash
# 現在の IP を確認
curl -s https://checkip.amazonaws.com

# terraform.tfvars を更新
admin_ip = "xxx.xxx.xxx.xxx/32"

# セキュリティグループだけ更新
terraform apply -target=module.security_groups
```

### 手順 5: EC2 bootstrap の完了を待つ

```bash
bash scripts/setup-ec2.sh
```

EC2 は `user_data` で次を自動実行する。

- Docker / compose / AWS CLI / SSM Agent のセットアップ
- `/opt/app` の作成
- GitHub から deploy に必要なファイルを取得
- SSM Parameter Store から `.envs/.production/*` を生成
- `latest` タグで初回 deploy を試行

### 手順 6: bootstrap 検証

`setup-ec2.sh` は、手動セットアップではなく bootstrap の結果確認用。

実行内容:
- `/opt/app` 配下の bootstrap 生成物を確認
- SSM Agent の起動確認
- `/var/log/user-data.log` の確認

### 手順 7: GitHub Secrets の設定

GitHub リポジトリ → Settings → Secrets → Actions:
- `AWS_ROLE_ARN`: terraform output の `github_actions_role_arn`
- `EC2_INSTANCE_ID`: EC2 インスタンス ID

### 手順 8: デプロイ

```bash
# まずは手動実行で 1 回成功ログを確認
# GitHub Actions > Deploy to Production > Run workflow

# 問題なければ通常運用は push でよい
git push github main
```

手動実行で確認したいこと:

- Docker build / ECR push が成功する
- SSM Run Command が `Success` になる
- ALB の `/diary/health/` が `200` になる

## 注意事項

### CloudFront のドメイン名が変わる

CloudFront distribution を削除・再作成すると、ドメイン名（`dXXXXXXXXXX.cloudfront.net`）が変わる。
ブックマークやドキュメントの URL を更新する必要がある。

### 永続設定と動的設定は分かれている

- `production-config`: secret / 長寿命設定を SSM に保持
- `production`: destroy/apply 対象の AWS リソースと、再生成される SSM 値を管理

そのため、再構築時は `production-config` を消さずに `production` だけを destroy/apply できる。

### bootstrap の依存関係

EC2 bootstrap は次に依存する。

- GitHub raw から `scripts/bootstrap/sync-app-files.sh` を取得できること
- `sync-app-files.sh` が `docker-compose.production.yml` / `ssm-deploy.sh` / `render-env-from-ssm.sh` を取得できること
- SSM に `DJANGO_SECRET_KEY` と動的接続情報がそろっていること

そのため、手順の順番は必ず次にする。

1. `production-config` apply
2. `production` apply
3. EC2 bootstrap 確認
4. GitHub Secrets 設定
5. workflow 実行

### 失敗時の確認順

1. `production-config` apply 後に永続 SSM が入っているか
2. `production` apply 後に動的 SSM が更新されているか
3. EC2 の `/var/log/user-data.log`
4. GitHub Actions の `SSM Standard Output` / `SSM Standard Error`
5. 必要なら `/opt/app/bin` と `.envs/.production` の生成状態

### State の管理

現在は local state。`terraform.tfstate` を失うと、既存リソースとの対応が取れなくなる。
本番運用では S3 backend + DynamoDB lock を推奨。

## ブログで深掘りできるポイント

- terraform apply の実行計画（Plan）の読み方
- State ファイルの役割と管理方法
- `terraform destroy` → `terraform apply` のサイクルとコスト最適化
- モジュール間の依存関係（module.alb が module.ec2.instance_id を参照する等）
- `-target` オプションの使いどころと注意点
