# 本番環境デプロイガイド

本書は連絡帳管理システムを本番環境（AWS）にデプロイする手順を記載しています。
Terraformによるインフラ構築、GitLab CI/CDによる自動デプロイ、運用管理の方法を説明します。

**ローカル環境での動作確認**: `LOCAL_DEPLOYMENT.md` を参照してください。

---

## 目次

1. [概要](#概要)
2. [アーキテクチャ概要](#アーキテクチャ概要)
3. [前提条件](#前提条件)
4. [Terraformによるインフラ構築](#terraformによるインフラ構築)
5. [アプリケーションのデプロイ](#アプリケーションのデプロイ)
6. [本番環境アクセス情報](#本番環境アクセス情報)
7. [セキュリティ設定](#セキュリティ設定)
8. [監視・運用](#監視運用)
9. [コスト試算](#コスト試算)
10. [トラブルシューティング](#トラブルシューティング)

---

## 概要

### 本書の目的

- 本番環境のアーキテクチャを理解する
- Terraformでインフラを再現可能にする
- GitLab CI/CDによる自動デプロイの仕組みを理解する
- アプリケーションのデプロイ方法を習得する

### 対象読者

- システムの評価者
- インフラエンジニア
- DevOpsエンジニア
- 本番環境の構築・運用担当者

### システム構成

本プロジェクトは本番グレードのAWSインフラ構築をTerraformで実現しています。

- **Terraform**: Infrastructure as Code（IaC）
- **GitLab CI/CD**: 自動テスト・デプロイパイプライン
- **Docker**: コンテナ化されたアプリケーション
- **AWS**: クラウドインフラ（12モジュール）

---

## アーキテクチャ概要

### 3層Webアプリケーション構成

```
インターネット
    ↓ (HTTPS)
CloudFront（CDN）
    ↓ (HTTP)
Application Load Balancer（ALB）
    ↓ (HTTP:8000)
EC2インスタンス（Django + Gunicorn）
    ↓ (PostgreSQL:5432)
RDS（PostgreSQL）
```

### 主要コンポーネント

| コンポーネント | 役割 | 冗長化 |
|-------------|------|-------|
| **CloudFront** | CDN、静的ファイル配信、HTTPS終端 | グローバル |
| **ALB** | ロードバランサー、ヘルスチェック | Multi-AZ対応可能 |
| **EC2** | Djangoアプリケーション | Auto Scaling対応可能 |
| **RDS** | PostgreSQLデータベース | Multi-AZ対応可能 |
| **S3** | 静的ファイル、メディアファイル | 高耐久性 |
| **ECR** | Dockerイメージリポジトリ | 高可用性 |
| **CloudWatch** | 監視・ログ | - |

### Terraformモジュール構成

本プロジェクトは12モジュールに分割されたTerraform構成を採用しています。

```
terraform/
├── modules/
│   ├── vpc/                  # VPC、サブネット、ルートテーブル
│   ├── security_groups/      # セキュリティグループ
│   ├── ec2/                  # EC2インスタンス
│   ├── rds/                  # RDS（PostgreSQL）
│   ├── alb/                  # Application Load Balancer
│   ├── cloudfront/           # CloudFront CDN
│   ├── s3/                   # S3バケット
│   ├── ecr/                  # ECR（Dockerイメージ）
│   ├── iam/                  # IAMロール・ポリシー
│   ├── ses/                  # SES（メール送信）
│   ├── cloudwatch/           # CloudWatch監視
│   └── cloudwatch_logs/      # CloudWatch Logs
├── environments/
│   └── production/
│       ├── main.tf           # メイン設定
│       ├── variables.tf      # 変数定義
│       ├── outputs.tf        # 出力定義
│       └── terraform.tfvars  # 変数値（Git管理外）
└── ARCHITECTURE.md           # 詳細ドキュメント（330行）
```

### 詳細ドキュメント

アーキテクチャの詳細、セキュリティ設計、トラフィックフロー、コスト最適化については以下を参照してください：

- **`terraform/ARCHITECTURE.md`**: 330行の詳細ドキュメント
  - ネットワーク層（VPC、サブネット、Security Groups）
  - コンピューティング層（EC2、IAM）
  - ロードバランサー層（ALB、CloudFront）
  - データベース層（RDS PostgreSQL）
  - CDN層（CloudFront）
  - ストレージ層（S3、ECR）
  - セキュリティ対策（ネットワーク、データ、アクセス制御）
  - 高可用性設計
  - PoCステージのセキュリティ判断
  - 運用管理（モニタリング、バックアップ、メンテナンス）

---

## 前提条件

### インフラ構築に必要なもの

1. **AWSアカウント**
   - IAM権限（EC2、RDS、ALB、CloudFront、S3、ECR等の作成・管理権限）
   - AWS CLI設定済み

2. **Terraform**
   - バージョン ≥ 1.0
   - インストール: https://www.terraform.io/downloads

3. **SSH鍵ペア**
   - EC2インスタンスへのSSH接続用
   - AWS Key Pairの作成

### CI/CDに必要なもの

4. **GitLab Runner**
   - **重要**: 本プロジェクトではhirokのWSL環境でGitLab Runnerが動作しています
   - docker executorを使用
   - **本番デプロイ前の確認事項**:
     - hirokにRunner稼働確認を依頼
     - GitLab Settings → CI/CD → Runners → Active状態確認
     - **注意**: Runner停止時はCI/CDパイプラインが実行できません

5. **環境変数（GitLab CI/CD Variables）**
   - AWS_ACCESS_KEY_ID
   - AWS_SECRET_ACCESS_KEY
   - AWS_ACCOUNT_ID
   - EC2_SSH_PRIVATE_KEY
   - EC2_HOST
   - EC2_USER

---

## Terraformによるインフラ構築

### Step 1: Terraformのインストール

```bash
# Ubuntu/Debian
wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update && sudo apt install terraform

# バージョン確認
terraform --version
```

### Step 2: AWSクレデンシャルの設定

```bash
# AWSクレデンシャル設定
export AWS_ACCESS_KEY_ID="<your-access-key>"
export AWS_SECRET_ACCESS_KEY="<your-secret-key>"
export AWS_DEFAULT_REGION="ap-northeast-1"

# AWS CLI確認
aws sts get-caller-identity
```

### Step 3: 変数ファイルの設定

```bash
cd terraform/environments/production

# サンプルファイルをコピー
cp terraform.tfvars.example terraform.tfvars

# 環境に応じて編集
vim terraform.tfvars
```

**編集項目**:
- `project_name`: プロジェクト名
- `environment`: 環境名（production）
- `admin_ip`: 管理者のIPアドレス（SSH接続用）
- `db_password`: データベースパスワード
- `key_name`: EC2のSSH鍵ペア名
- その他の設定値

### Step 4: Terraformの初期化

```bash
# Terraform初期化（プラグインダウンロード）
terraform init
```

### Step 5: プランの確認

```bash
# プラン確認（変更内容をプレビュー）
terraform plan -out=tfplan

# プラン内容を確認
# - 作成されるリソース数
# - 変更されるリソース
# - 削除されるリソース
```

### Step 6: インフラの構築

```bash
# インフラ構築実行（約10分）
terraform apply tfplan
```

**構築されるリソース**:
- VPC、サブネット、ルートテーブル
- Security Groups
- EC2インスタンス
- RDS PostgreSQL
- ALB
- CloudFront
- S3バケット
- ECR
- IAMロール
- SES
- CloudWatch Alarms
- CloudWatch Logs

### Step 7: 出力情報の確認

```bash
# 出力情報の表示
terraform output
```

**期待される出力**:
```
cloudfront_domain = "d2wk3j2pacp33b.cloudfront.net"
ec2_public_ip = "43.206.211.105"
rds_endpoint = "school-diary-production.xxx.ap-northeast-1.rds.amazonaws.com"
alb_dns_name = "school-diary-production-alb-xxx.ap-northeast-1.elb.amazonaws.com"
s3_bucket_name = "school-diary-production-static"
ecr_repository_url = "123456789012.dkr.ecr.ap-northeast-1.amazonaws.com/school-diary-production-django"
```

これらの情報は後のアプリケーションデプロイで使用します。

---

## アプリケーションのデプロイ

本番環境へのアプリケーションデプロイには2つの方法があります：

1. **手動デプロイ**: EC2にSSH接続して手動でデプロイ
2. **GitLab CI/CD**: 自動テスト・デプロイパイプライン（推奨）

### 5.1 手動デプロイ

#### Step 1: EC2にSSH接続

```bash
# SSH接続
ssh -i ~/.ssh/<your-key>.pem ubuntu@<EC2のパブリックIP>
```

#### Step 2: Dockerのインストール（初回のみ）

```bash
# Dockerインストール
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# ユーザーをdockerグループに追加
sudo usermod -aG docker ubuntu

# 再ログイン（グループ反映のため）
exit
ssh -i ~/.ssh/<your-key>.pem ubuntu@<EC2のパブリックIP>

# Docker確認
docker --version
```

#### Step 3: プロジェクトのクローン

```bash
# プロジェクトディレクトリ作成
sudo mkdir -p /opt/app
sudo chown ubuntu:ubuntu /opt/app

# プロジェクトクローン
cd /opt/app
git clone <リポジトリURL> .
```

#### Step 4: 環境変数の設定

```bash
# 環境変数ディレクトリ作成
mkdir -p .envs/.production

# Django環境変数設定
cat > .envs/.production/.django << 'EOF'
# Django
DJANGO_SETTINGS_MODULE=config.settings.production
DJANGO_SECRET_KEY=<ランダムな文字列（50文字以上）>
DJANGO_ALLOWED_HOSTS=<CloudFrontドメイン>,<ALBドメイン>,<EC2 IP>

# AWS
AWS_STORAGE_BUCKET_NAME=<S3バケット名>
AWS_S3_REGION_NAME=ap-northeast-1

# Database
DATABASE_URL=postgres://<username>:<password>@<RDS endpoint>:5432/<db_name>

# ECR
ECR_REGISTRY=<ECRレジストリURL>
ECR_REPOSITORY=school-diary-production-django
IMAGE_TAG=latest
EOF

# PostgreSQL環境変数設定
cat > .envs/.production/.postgres << 'EOF'
POSTGRES_HOST=<RDS endpoint>
POSTGRES_PORT=5432
POSTGRES_DB=<db_name>
POSTGRES_USER=<username>
POSTGRES_PASSWORD=<password>
EOF

# 権限設定
chmod 600 .envs/.production/.django
chmod 600 .envs/.production/.postgres
```

#### Step 5: ECRログイン

```bash
# ECRログイン
aws ecr get-login-password --region ap-northeast-1 | \
  docker login --username AWS --password-stdin <ECRレジストリURL>
```

#### Step 6: コンテナの起動

```bash
# コンテナ起動
docker compose -f docker-compose.production.yml up -d

# ログ確認
docker compose -f docker-compose.production.yml logs -f django
```

#### Step 7: マイグレーション実行

```bash
# マイグレーション
docker compose -f docker-compose.production.yml exec django \
  python manage.py migrate --noinput

# 静的ファイル収集
docker compose -f docker-compose.production.yml exec django \
  python manage.py collectstatic --noinput

# ヘルスチェック
docker compose -f docker-compose.production.yml exec django \
  python manage.py check --deploy
```

#### Step 8: スーパーユーザー作成

```bash
# スーパーユーザー作成
docker compose -f docker-compose.production.yml exec django \
  python manage.py createsuperuser
```

### 5.2 GitLab CI/CDによる自動デプロイ（推奨）

GitLab CI/CDを使用すると、コードをpushするだけで自動的にテスト・ビルド・デプロイが実行されます。

#### パイプライン概要

- **CI/CDツール**: GitLab CI/CD
- **パイプライン定義**: `.gitlab-ci.yml`（222行）
- **実行環境**: GitLab Runner（docker executor、**hirokのWSL上で動作**）
- **トリガー**: mainブランチへのpush

#### パイプライン構成

本プロジェクトのCI/CDパイプラインは3つのステージで構成されています：

```
git push (main)
  ↓
┌─────────────────────────────────┐
│ Stage 1: Test（自動実行）       │
│ - lint: ruff check              │
│ - type-check: mypy              │
│ - unit-test: pytest + PostgreSQL│
└─────────────────────────────────┘
  ↓ (全テスト合格)
┌─────────────────────────────────┐
│ Stage 2: Build（自動実行）      │
│ - ECRログイン                   │
│ - Dockerイメージビルド          │
│ - ECRにpush（latest + SHA）     │
└─────────────────────────────────┘
  ↓
┌─────────────────────────────────┐
│ Stage 3: Deploy（手動実行）⚠️   │
│ - EC2にSSH接続                  │
│ - ECRからイメージpull           │
│ - docker compose up             │
│ - migrate, collectstatic        │
│ - ヘルスチェック                │
└─────────────────────────────────┘
  ↓
本番環境更新完了
```

#### 前提条件（重要）⚠️

**GitLab Runnerの稼働確認**:

本プロジェクトではhirokのWSL環境でGitLab Runnerが動作しているため、デプロイ実行前に必ず以下を確認してください：

1. **hirokにRunner稼働確認を依頼**
   - Runnerが起動していること
   - docker executorが正常動作していること

2. **GitLab UIで確認**
   - GitLab Settings → CI/CD → Runners
   - 該当Runnerが「Active」状態であることを確認
   - 最終実行時刻が最近であることを確認

3. **Runner停止時の影響**
   - Runner停止中はCI/CDパイプラインが実行できません
   - deploy-productionジョブは「Pending」状態のまま待機します
   - タイムアウト（1時間）後にジョブが失敗します

#### 環境変数設定

GitLab Settings → CI/CD → Variables で以下を設定します：

| 変数名 | 説明 | 保護 | マスク |
|-------|------|------|-------|
| AWS_ACCESS_KEY_ID | AWSアクセスキーID | ✅ | ✅ |
| AWS_SECRET_ACCESS_KEY | AWSシークレットアクセスキー | ✅ | ✅ |
| AWS_ACCOUNT_ID | AWSアカウントID | ✅ | - |
| EC2_SSH_PRIVATE_KEY | EC2へのSSH秘密鍵（PEM形式） | ✅ | ✅ |
| EC2_HOST | EC2のパブリックIP | ✅ | - |
| EC2_USER | EC2のユーザー名（ubuntu） | - | - |

**保護（Protected）**: mainブランチのみで使用可能
**マスク（Masked）**: ログに表示されない

#### デプロイ実行手順

1. **コード変更をmainブランチにpush**

```bash
git add .
git commit -m "feat: 新機能追加"
git push origin main
```

2. **GitLab CI/CDパイプラインが自動起動**

- GitLab UI → CI/CD → Pipelines で確認
- Stage 1（Test）が自動実行
- Stage 2（Build）が自動実行（Testが成功した場合）

3. **deploy stageは手動実行⚠️**

- Stage 2（Build）が成功すると、Stage 3（Deploy）は**手動実行待ち**になります
- これは誤デプロイを防ぐための安全機構です

4. **hirokにRunner稼働確認を依頼**

- 本番デプロイ前に必ずhirokに確認
- Runnerが起動していることを確認
- 承認を得てから次のステップへ

5. **GitLab UIでdeploy-productionジョブを実行**

- GitLab UI → CI/CD → Pipelines
- 該当パイプラインを開く
- deploy-production ジョブの「Play」ボタンをクリック
- デプロイ実行（約5分）

6. **デプロイ完了確認**

```bash
# ヘルスチェック
curl https://d2wk3j2pacp33b.cloudfront.net/diary/health/

# アプリケーションアクセス
open https://d2wk3j2pacp33b.cloudfront.net
```

#### デプロイフロー詳細

**Stage 1: Test**（並列実行、約3分）

- **lint**: ruff checkでコード品質チェック
- **type-check**: mypyで型チェック（警告扱い、失敗してもパイプライン継続）
- **unit-test**: pytest実行
  - PostgreSQL 16を使用（サービスコンテナ）
  - 主要機能テストのみ実行（`school_diary/diary/tests/features/`）
  - カバレッジ測定（coverage.xml生成）
  - カバレッジ結果をGitLab UIに表示

**Stage 2: Build**（約5分）

1. ECRログイン
2. Dockerイメージビルド（`compose/production/django/Dockerfile`）
3. ECRにpush
   - `latest` タグ: 常に最新版
   - `<コミットSHA>` タグ: バージョン管理・ロールバック用

**Stage 3: Deploy**（手動実行、約5分）

1. EC2にSSH接続
2. docker-compose.production.ymlを転送
3. ECRログイン
4. Dockerイメージpull
5. コンテナ再起動（`docker compose up -d --force-recreate`）
6. マイグレーション実行
7. 静的ファイル収集
8. ヘルスチェック
9. 古いDockerイメージ削除（ディスク節約）

#### CI/CDの利点

- ✅ **自動テスト**: 手動テストの手間を削減
- ✅ **一貫性**: デプロイ手順が標準化される
- ✅ **安全性**: テスト失敗時は自動的にデプロイ中止
- ✅ **トレーサビリティ**: デプロイ履歴がGitLabに記録
- ✅ **ロールバック**: コミットSHAタグでバージョン管理
- ✅ **効率化**: 手動デプロイの5ステップ → git push のみ

#### ロールバック方法

過去のバージョンに戻したい場合：

```bash
# 過去のコミットSHAを確認
git log --oneline

# 過去のコミットをmainにpush
git revert <コミットSHA>
git push origin main

# または、EC2で直接イメージを変更
ssh ubuntu@<EC2 IP>
cd /opt/app
export IMAGE_TAG=<過去のコミットSHA>
docker compose -f docker-compose.production.yml pull
docker compose -f docker-compose.production.yml up -d --force-recreate
```

---

## 本番環境アクセス情報

### アクセスURL

- **本番環境**: https://d2wk3j2pacp33b.cloudfront.net
- **管理画面**: https://d2wk3j2pacp33b.cloudfront.net/admin
- **ヘルスチェック**: https://d2wk3j2pacp33b.cloudfront.net/diary/health/

### ログイン情報

#### 管理者アカウント

- メールアドレス: `admin@example.com`
- パスワード: `password123`
- 権限: 全機能アクセス可能

#### 担任アカウント（例）

- メールアドレス: `teacher_1_a@example.com`
- パスワード: `password123`
- 権限: クラス1-Aの連絡帳閲覧・反応記録

#### 生徒アカウント（例）

- メールアドレス: `student_1_a_01@example.com`
- パスワード: `password123`
- 権限: 自分の連絡帳作成・閲覧

### テストデータ

- 管理者: 1名
- 校長: 1名
- 学年主任: 3名（1〜3年）
- 担任: 9名（9クラス分）
- 生徒: 270名（30名/クラス × 9クラス）
- クラス: 9クラス（1-3年 × A-Cクラス）
- 日記: 約6,500件（30日分 × 270名 × 80%提出率）

### 稼働状態

- **稼働期間**: 2025年XX月XX日まで（評価期間中）
- **稼働確認**: https://d2wk3j2pacp33b.cloudfront.net/diary/health/
- **注意事項**:
  - GitLab Runner（hirokのWSL）が動作している必要があります
  - 新規デプロイ前にhirokに確認してください

---

## セキュリティ設定

本番環境では以下のセキュリティ対策を実施しています。

### ネットワークセキュリティ

- **Private Subnet**: RDSはインターネットから隔離
- **Security Groups**: 最小権限の原則
  - EC2: ALBからのみアクセス可能
  - RDS: EC2からのみアクセス可能
  - ALB: CloudFrontからのみアクセス可能
- **SSH制限**: 管理者IPからのみEC2へSSH接続可能
- **CloudFront Managed Prefix List**: ALBへのアクセスをCloudFrontのみに制限

### データセキュリティ

- **暗号化**: RDS、S3ともに暗号化有効
  - RDS: ストレージ暗号化（AES256）
  - S3: SSE-S3（AES256）
- **バックアップ**: RDS自動バックアップ（7日保持）
- **S3バージョニング**: 誤削除対策

### アクセス制御

- **IAM Role**: EC2にはS3アクセス権限のみ付与
- **S3パブリックアクセスブロック**: 全て有効
- **最小権限の原則**: 必要最小限の権限のみ付与

### PoCステージで許容するリスク

コスト優先のため、以下のリスクを許容しています：

- CloudFront → ALB間HTTP通信（AWS内部ネットワーク、傍受リスク極小）
- WAF未実装（アプリケーション層対策で補完）
- RDS Single-AZ（バックアップで対応、ダウンタイム許容）
- EC2 Public Subnet（NAT Gateway不要、コスト削減）

### サービスイン時に必須の対策

本番サービスイン時は以下の対策を追加してください：

1. **カスタムドメイン + ACM**: End-to-End HTTPS（年$12〜）
2. **WAF**: OWASP Top 10対策（月$5-10）
3. **NAT Gateway + EC2移動**: Private Subnet化（月$32）
4. **RDS Multi-AZ**: 自動フェイルオーバー（月+$15）
5. **CloudTrail**: API監査ログ（無料、S3ストレージのみ月$1-2）

詳細は `terraform/ARCHITECTURE.md` を参照してください。

---

## 監視・運用

### CloudWatch監視

以下のメトリクスを監視し、異常時にアラートを送信します：

#### EC2メトリクス

- CPU使用率: 80%以上で警告
- メモリ使用率: 80%以上で警告
- ディスク使用率: 80%以上で警告

#### ALBメトリクス

- リクエスト数: 急増時に警告
- レイテンシ: 1秒以上で警告
- 5xxエラー: 発生時に警告

#### RDSメトリクス

- CPU使用率: 80%以上で警告
- 接続数: 上限に近づいたら警告
- ストレージ使用率: 80%以上で警告

### ログ管理

- **CloudWatch Logs**: アプリケーションログ、エラーログ
- **RDS Logs**: PostgreSQLログ、クエリログ
- **ALB Access Logs**: アクセスログ（オプション）

### バックアップ

- **RDS自動バックアップ**: 日次バックアップ、7日間保持
- **S3バージョニング**: ファイル変更履歴保持、90日後に古いバージョン削除

### メンテナンスウィンドウ

- **RDS**: 月曜 04:00-05:00 JST（自動メンテナンス）
- **EC2**: 手動パッチ適用

詳細は `terraform/ARCHITECTURE.md` を参照してください。

---

## コスト試算

### 月額コスト（概算）

| リソース | インスタンスタイプ | 月額コスト（概算） |
|---------|-----------------|-----------------|
| EC2 | t3.micro | $8 |
| RDS | db.t3.micro（Single-AZ） | $15 |
| CloudFront | データ転送量依存 | $5-10 |
| ALB | 時間課金 | $20 |
| S3 | ストレージ + 転送 | $5 |
| ECR | ストレージ | $1 |
| CloudWatch | メトリクス + ログ | $5 |
| **合計** | - | **$59-64** |

### コスト削減施策

- **S3 VPC Endpoint**: データ転送料削減（Gateway型、無料）
- **Single-AZ RDS**: Multi-AZよりコスト50%削減
- **CloudFront**: Origin側の負荷軽減
- **S3ライフサイクルポリシー**: 古いバージョン自動削除

### サービスイン時の追加コスト

- **カスタムドメイン**: 年$12〜
- **WAF**: 月$5-10
- **NAT Gateway**: 月$32
- **RDS Multi-AZ**: 月+$15

詳細は `terraform/ARCHITECTURE.md` を参照してください。

---

## トラブルシューティング

### EC2にSSH接続できない

#### 原因1: Security Groupの設定ミス

```bash
# Security Group確認
aws ec2 describe-security-groups \
  --group-ids <security-group-id> \
  --region ap-northeast-1

# SSH（ポート22）が管理者IPから許可されているか確認
```

#### 原因2: SSH鍵の権限エラー

```bash
# SSH鍵の権限を600に変更
chmod 600 ~/.ssh/<your-key>.pem

# SSH接続確認
ssh -i ~/.ssh/<your-key>.pem ubuntu@<EC2 IP>
```

#### 原因3: EC2インスタンスが起動していない

```bash
# EC2状態確認
aws ec2 describe-instances \
  --instance-ids <instance-id> \
  --region ap-northeast-1

# インスタンス起動
aws ec2 start-instances \
  --instance-ids <instance-id> \
  --region ap-northeast-1
```

### GitLab CI/CDパイプラインが失敗

#### 原因1: GitLab Runnerが停止している⚠️

- **hirokに確認**: Runner（WSL）が起動しているか
- GitLab Settings → CI/CD → Runners で確認
- Runner再起動後、パイプラインを再実行

#### 原因2: 環境変数が設定されていない

```bash
# GitLab Settings → CI/CD → Variables で確認
# 必要な変数:
# - AWS_ACCESS_KEY_ID
# - AWS_SECRET_ACCESS_KEY
# - AWS_ACCOUNT_ID
# - EC2_SSH_PRIVATE_KEY
# - EC2_HOST
# - EC2_USER
```

#### 原因3: ECRログイン失敗

- AWS認証情報が正しいか確認
- ECRリポジトリが存在するか確認
- IAM権限を確認（`ecr:GetAuthorizationToken`, `ecr:BatchGetImage`等）

#### 原因4: テスト失敗

```bash
# ローカルでテスト実行して確認
docker compose -f docker-compose.local.yml run --rm django pytest
```

### デプロイ後にアプリケーションが起動しない

#### 原因1: 環境変数の設定ミス

```bash
# EC2にSSH接続
ssh -i ~/.ssh/<your-key>.pem ubuntu@<EC2 IP>

# 環境変数確認
cd /opt/app
cat .envs/.production/.django
cat .envs/.production/.postgres

# 特に確認すべき項目:
# - DATABASE_URL
# - DJANGO_ALLOWED_HOSTS
# - AWS_STORAGE_BUCKET_NAME
```

#### 原因2: データベース接続エラー

```bash
# RDS接続確認
docker compose -f docker-compose.production.yml exec django \
  python manage.py dbshell

# Security Group確認（EC2 → RDS接続許可）
```

#### 原因3: コンテナログ確認

```bash
# コンテナログ確認
docker compose -f docker-compose.production.yml logs django

# エラーメッセージを確認して対処
```

### CloudFrontでアクセスできない

#### 原因1: ALBが正常に動作していない

```bash
# ALBヘルスチェック確認
aws elbv2 describe-target-health \
  --target-group-arn <target-group-arn> \
  --region ap-northeast-1

# ヘルスチェックが「unhealthy」の場合:
# - EC2でアプリケーションが起動しているか確認
# - Security Group確認
# - /diary/health/ エンドポイントが正常に応答するか確認
```

#### 原因2: CloudFrontのオリジン設定ミス

```bash
# CloudFront設定確認
aws cloudfront get-distribution \
  --id <distribution-id>

# オリジンがALBのDNS名になっているか確認
```

#### 原因3: Security Group設定ミス

- ALB Security GroupでCloudFront Managed Prefix Listからのアクセスを許可しているか確認
- EC2 Security GroupでALBからのアクセスを許可しているか確認

### ディスク容量不足

```bash
# ディスク使用状況確認
df -h

# 古いDockerイメージ削除
docker image prune -af

# 古いDockerビルドキャッシュ削除
docker builder prune -af

# 不要なログ削除
sudo journalctl --vacuum-time=7d
```

---

## まとめ

本ガイドでは本番環境へのデプロイ手順を説明しました。

### インフラ構築

- ✅ Terraformで12モジュール構成のAWSインフラを構築
- ✅ Infrastructure as Code（IaC）で再現可能
- ✅ 詳細は `terraform/ARCHITECTURE.md` 参照

### デプロイ方法

- ✅ 手動デプロイ: EC2にSSH接続してデプロイ
- ✅ **GitLab CI/CD**: 自動テスト・デプロイパイプライン（推奨）
  - test → build → deploy（手動実行）
  - **重要**: hirokにRunner稼働確認を依頼

### 本番環境

- ✅ URL: https://d2wk3j2pacp33b.cloudfront.net
- ✅ 管理者: admin@example.com / password123
- ✅ 稼働期間: 評価期間中

### セキュリティ・運用

- ✅ ネットワーク・データ・アクセス制御を実施
- ✅ CloudWatch監視、RDS自動バックアップ
- ✅ PoCステージに適したコスト最適化

**ローカル環境での動作確認**: `LOCAL_DEPLOYMENT.md` を参照してください。

---

**作成日**: 2025-10-30
**最終更新**: 2025-10-30
**バージョン**: 1.0
