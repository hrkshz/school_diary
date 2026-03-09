# Terraform による shared/app 環境構築

## なぜやるか

「残すもの」と「止めるもの」を state でも分離し、`app` だけを `terraform destroy` / `terraform apply` しても、公開入口と固定値を維持できる運用にする。

## 全体の流れ

```text
terraform apply（backend-bootstrap: remote state bucket 作成）
  → terraform apply（shared: CloudFront + maintenance S3 + 永続 SSM）
  → terraform apply（app: アプリ基盤 + 動的 SSM）
  → terraform apply（shared: service_mode=active へ切替）
  → user_data bootstrap（EC2 初期化 + env 生成 + 初回 deploy 試行）
  → GitHub Secrets 設定
  → git push（GitHub Actions でデプロイ）
```

## 手順

### 手順 1: backend-bootstrap を apply

```bash
cd terraform/environments/backend-bootstrap
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform plan
terraform apply
```

ここでは Terraform remote state 用の S3 bucket を作成する。

### 手順 2: shared を apply

```bash
cd terraform/environments/shared
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform plan
terraform apply
```

ここでは通常 destroy しない共有リソースを作成する。

- CloudFront distribution
- maintenance page 用 S3 bucket
- `DJANGO_SECRET_KEY`
- `POSTGRES_PASSWORD`
- `DJANGO_ADMIN_URL`
- `WEB_CONCURRENCY`

重要:

- 初回は `service_mode = "maintenance"` のままでよい
- `django_secret_key` と `db_password` は `terraform/environments/shared/terraform.tfvars` に設定する
- CloudFront のドメイン名は `shared` が SSM に保存する

### 手順 3: app を apply

```bash
cd terraform/environments/app
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform plan
terraform apply
```

`app` は `shared` に保存済みの `POSTGRES_PASSWORD` と CloudFront ドメインを参照し、ALB DNS / RDS endpoint など再生成値を SSM に更新する。

確認項目:

- `github_repo`
- `github_bootstrap_ref`
- `ses_sender_email`
- `cloudwatch_alarm_email`

### 手順 4: shared を active に切り替える

CloudFront のオリジンを maintenance から ALB に切り替える。

```bash
cd terraform/environments/shared
terraform apply -var='service_mode=active'
```

### 手順 5: 出力値の確認

```bash
cd terraform/environments/app
terraform output

cd ../shared
terraform output
```

重要な出力:

- `ec2_public_ip`
- `alb_dns_name`
- `cloudfront_domain_name`
- `github_actions_role_arn`

### 手順 6: セキュリティグループの IP 更新

SSH 接続元の IP が変わっている場合は `terraform/environments/app/terraform.tfvars` の `admin_ip` を更新する。

```bash
curl -s https://checkip.amazonaws.com
```

### 手順 7: EC2 bootstrap の完了を待つ

EC2 は `user_data` で次を自動実行する。

- Docker / compose / AWS CLI / SSM Agent のセットアップ
- `/opt/app` の作成
- GitHub から deploy に必要なファイルを取得
- SSM Parameter Store から `.envs/.production/*` を生成
- `latest` タグで初回 deploy を試行

### 手順 8: GitHub Secrets の設定

GitHub リポジトリ → Settings → Secrets → Actions:

- `AWS_ROLE_ARN`: `terraform/environments/app` の `github_actions_role_arn`
- `EC2_INSTANCE_ID`: `terraform/environments/app` の EC2 インスタンス ID

### 手順 9: デプロイ

```bash
# まずは手動実行で 1 回成功ログを確認
# GitHub Actions > Deploy to Production > Run workflow

git push github main
```

## app 停止時の運用

```text
1. shared を maintenance に切り替える
2. app を destroy する
3. 再開時は app apply
4. shared を active に戻す
```

```bash
cd terraform/environments/shared
terraform apply -var='service_mode=maintenance'

cd ../app
terraform destroy
```

この運用なら CloudFront URL と永続 SSM は残る。

## 注意事項

### CloudFront の URL

CloudFront distribution は `shared` 管理に移したため、通常の `app destroy` では `dXXXXXXXXXX.cloudfront.net` は変わらない。

### 永続設定と動的設定

- `shared`: CloudFront、maintenance S3、secret / 長寿命設定、共有システム値
- `app`: destroy/apply 対象の AWS リソースと、再生成される SSM 値

### bootstrap の依存関係

EC2 bootstrap は次に依存する。

- `shared` 側に `DJANGO_SECRET_KEY` と CloudFront ドメインがあること
- `app` 側に DB 接続先などの動的 SSM があること
- GitHub raw から bootstrap スクリプトを取得できること

順番は必ず次にする。

1. `backend-bootstrap` apply
2. `shared` apply
3. `app` apply
4. `shared` を `active` に切り替え
5. EC2 bootstrap 確認
6. GitHub Secrets 設定
7. workflow 実行

### State の管理

初回は local state で backend bucket を作り、その後は S3 backend に移行する。`shared` と `app` は別 key に分離し、`use_lockfile = true` で lock を有効化する。
