# 本番環境デプロイ記録

本書は連絡帳管理システムを本番環境（AWS）にデプロイした際の実施内容を記録しています。
Terraform によるインフラ構築、GitLab CI/CD による自動デプロイ、運用管理の方法を記載します。

**重要**: 本ドキュメントは筆者の個人 AWS 環境でのデプロイ記録です。第三者が同様の環境を構築するには、AWS アカウント、認証情報、環境設定のカスタマイズが必要です。

**ローカル環境での動作確認**: `LOCAL_DEPLOYMENT.md` を参照してください。

---

## 目次

1. [実施環境](#実施環境)
2. [Terraform によるインフラ構築](#terraformによるインフラ構築)
3. [アプリケーションのデプロイ](#アプリケーションのデプロイ)
4. [本番環境アクセス情報](#本番環境アクセス情報)
5. [今後の改善予定](#今後の改善予定)

---

## 実施環境

### 使用したインフラ環境

本デプロイで使用した環境・ツールは以下の通りです：

1. **AWS アカウント**

   - 筆者の個人アカウント
   - IAM 権限（EC2、RDS、ALB、CloudFront、S3、ECR 等の作成・管理権限）
   - AWS CLI 設定済み

2. **Terraform**

   - バージョン 1.5+
   - インストール: https://www.terraform.io/downloads

3. **SSH 鍵ペア**
   - EC2 インスタンスへの SSH 接続用
   - AWS Key Pair で作成

### 使用した CI/CD 環境

4. **GitLab Runner**

   - **環境**: 筆者の WSL 環境で GitLab Runner を稼働
   - docker executor を使用
   - **注意**: 第三者が利用する場合は独自の Runner 環境が必要

5. **環境変数（GitLab CI/CD Variables）**
   - AWS_ACCESS_KEY_ID
   - AWS_SECRET_ACCESS_KEY
   - AWS_ACCOUNT_ID
   - EC2_SSH_PRIVATE_KEY
   - EC2_HOST
   - EC2_USER

### 第三者が構築する場合の要件

同様の環境を構築する場合、以下が必要です：

- 独自の AWS アカウントと IAM 権限
- AWS 認証情報（Access Key / Secret Key）
- Terraform 環境（バージョン ≥ 1.0）
- GitLab Runner 環境（docker executor 推奨）
- 環境変数のカスタマイズ（`terraform.tfvars`、GitLab CI/CD Variables）

---

## Terraform によるインフラ構築

### Step 1: Terraform のインストール

```bash
# Ubuntu/Debian
wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update && sudo apt install terraform

# バージョン確認
terraform --version
```

### Step 2: AWS クレデンシャルの設定

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
- `admin_ip`: 管理者の IP アドレス（SSH 接続用）
- `db_password`: データベースパスワード
- `key_name`: EC2 の SSH 鍵ペア名
- その他の設定値

### Step 4: Terraform の初期化

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
- EC2 インスタンス
- RDS PostgreSQL
- ALB
- CloudFront
- S3 バケット
- ECR
- IAM ロール
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

本番環境へのアプリケーションデプロイには 2 つの方法があります：

1. **手動デプロイ**: EC2 に SSH 接続して手動でデプロイ
2. **GitLab CI/CD**: 自動テスト・デプロイパイプライン（推奨）

### 5.1 手動デプロイ

#### Step 1: EC2 に SSH 接続

```bash
# SSH接続
ssh -i ~/.ssh/<your-key>.pem ubuntu@<EC2のパブリックIP>
```

#### Step 2: Docker のインストール（初回のみ）

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

#### Step 5: ECR ログイン

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

### 5.2 GitLab CI/CD による自動デプロイ（推奨）

GitLab CI/CD を使用すると、コードを push するだけで自動的にテスト・ビルド・デプロイが実行されます。

#### パイプライン概要

- **CI/CD ツール**: GitLab CI/CD
- **パイプライン定義**: `.gitlab-ci.yml`（222 行）
- **実行環境**: GitLab Runner（docker executor、**hirok の WSL 上で動作**）
- **トリガー**: main ブランチへの push

#### パイプライン構成

本プロジェクトの CI/CD パイプラインは 3 つのステージで構成されています：

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

**GitLab Runner の稼働確認**:

本プロジェクトでは hirok の WSL 環境で GitLab Runner が動作しているため、デプロイ実行前に必ず以下を確認してください：

1. **hirok に Runner 稼働確認を依頼**

   - Runner が起動していること
   - docker executor が正常動作していること

2. **GitLab UI で確認**

   - GitLab Settings → CI/CD → Runners
   - 該当 Runner が「Active」状態であることを確認
   - 最終実行時刻が最近であることを確認

3. **Runner 停止時の影響**
   - Runner 停止中は CI/CD パイプラインが実行できません
   - deploy-production ジョブは「Pending」状態のまま待機します
   - タイムアウト（1 時間）後にジョブが失敗します

#### 環境変数設定

GitLab Settings → CI/CD → Variables で以下を設定します：

| 変数名                | 説明                            | 保護 | マスク |
| --------------------- | ------------------------------- | ---- | ------ |
| AWS_ACCESS_KEY_ID     | AWS アクセスキー ID             | ✅   | ✅     |
| AWS_SECRET_ACCESS_KEY | AWS シークレットアクセスキー    | ✅   | ✅     |
| AWS_ACCOUNT_ID        | AWS アカウント ID               | ✅   | -      |
| EC2_SSH_PRIVATE_KEY   | EC2 への SSH 秘密鍵（PEM 形式） | ✅   | ✅     |
| EC2_HOST              | EC2 のパブリック IP             | ✅   | -      |
| EC2_USER              | EC2 のユーザー名（ubuntu）      | -    | -      |

**保護（Protected）**: main ブランチのみで使用可能
**マスク（Masked）**: ログに表示されない

#### デプロイ実行手順

1. **コード変更を main ブランチに push**

```bash
git add .
git commit -m "feat: 新機能追加"
git push origin main
```

2. **GitLab CI/CD パイプラインが自動起動**

- GitLab UI → CI/CD → Pipelines で確認
- Stage 1（Test）が自動実行
- Stage 2（Build）が自動実行（Test が成功した場合）

3. **deploy stage は手動実行 ⚠️**

- Stage 2（Build）が成功すると、Stage 3（Deploy）は**手動実行待ち**になります
- これは誤デプロイを防ぐための安全機構です

4. **hirok に Runner 稼働確認を依頼**

- 本番デプロイ前に必ず hirok に確認
- Runner が起動していることを確認
- 承認を得てから次のステップへ

5. **GitLab UI で deploy-production ジョブを実行**

- GitLab UI → CI/CD → Pipelines
- 該当パイプラインを開く
- deploy-production ジョブの「Play」ボタンをクリック
- デプロイ実行（約 5 分）

6. **デプロイ完了確認**

```bash
# ヘルスチェック
curl https://d2wk3j2pacp33b.cloudfront.net/diary/health/

# アプリケーションアクセス
open https://d2wk3j2pacp33b.cloudfront.net
```

#### デプロイフロー詳細

**Stage 1: Test**（並列実行、約 3 分）

- **lint**: ruff check でコード品質チェック
- **type-check**: mypy で型チェック（警告扱い、失敗してもパイプライン継続）
- **unit-test**: pytest 実行
  - PostgreSQL 16 を使用（サービスコンテナ）
  - 主要機能テストのみ実行（`school_diary/diary/tests/features/`）
  - カバレッジ測定（coverage.xml 生成）
  - カバレッジ結果を GitLab UI に表示

**Stage 2: Build**（約 5 分）

1. ECR ログイン
2. Docker イメージビルド（`compose/production/django/Dockerfile`）
3. ECR に push
   - `latest` タグ: 常に最新版
   - `<コミットSHA>` タグ: バージョン管理・ロールバック用

**Stage 3: Deploy**（手動実行、約 5 分）

1. EC2 に SSH 接続
2. docker-compose.production.yml を転送
3. ECR ログイン
4. Docker イメージ pull
5. コンテナ再起動（`docker compose up -d --force-recreate`）
6. マイグレーション実行
7. 静的ファイル収集
8. ヘルスチェック
9. 古い Docker イメージ削除（ディスク節約）

#### CI/CD の利点

- ✅ **自動テスト**: 手動テストの手間を削減
- ✅ **一貫性**: デプロイ手順が標準化される
- ✅ **安全性**: テスト失敗時は自動的にデプロイ中止
- ✅ **トレーサビリティ**: デプロイ履歴が GitLab に記録
- ✅ **ロールバック**: コミット SHA タグでバージョン管理
- ✅ **効率化**: 手動デプロイの 5 ステップ → git push のみ

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

### アクセス URL

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
- 権限: クラス 1-A の連絡帳閲覧・反応記録

#### 生徒アカウント（例）

- メールアドレス: `student_1_a_01@example.com`
- パスワード: `password123`
- 権限: 自分の連絡帳作成・閲覧

### テストデータ

- 管理者: 1 名
- 校長: 1 名
- 学年主任: 3 名（1〜3 年）
- 担任: 9 名（9 クラス分）
- 生徒: 270 名（30 名/クラス × 9 クラス）
- クラス: 9 クラス（1-3 年 × A-C クラス）
- 日記: 約 6,500 件（30 日分 × 270 名 × 80%提出率）

### 稼働状態

- **稼働期間**: 2025 年 XX 月 XX 日まで（評価期間中）
- **稼働確認**: https://d2wk3j2pacp33b.cloudfront.net/diary/health/
- **注意事項**:
  - GitLab Runner（hirok の WSL）が動作している必要があります
  - 新規デプロイ前に hirok に確認してください

---

## 今後の改善予定

### 現状の制約

本デプロイは筆者の個人 AWS 環境で実施したため、以下の制約があります：

- **個人環境専用**: 筆者の AWS アカウント、認証情報に依存
- **ハードコードされた値**: IP アドレス、リソース名、アカウント ID などが固定
- **特定環境依存**: GitLab Runner（筆者の WSL 環境）、環境変数設定
- **手動設定**: terraform.tfvars、GitLab CI/CD Variables の手動設定が必要

### テンプレート化の構想

第三者が独自の AWS 環境で利用できるよう、以下の改善を検討しています：

#### 1. パラメータ外部化

- **terraform.tfvars のテンプレート化**: 環境変数による設定の外部化
- **変数化**: プロジェクト名、リージョン、IP アドレスなどを変数化
- **ハードコード除去**: アカウント ID、リソース名の自動生成

**例**:

```hcl
# terraform.tfvars.example
project_name     = "your-project-name"
aws_region       = "ap-northeast-1"
admin_ip         = "your-ip-address/32"
db_password      = "your-secure-password"
key_name         = "your-ssh-key-name"
```

#### 2. 環境別設定ファイルの分離

- **dev / staging / prod**: 環境別の terraform.tfvars
- **環境切り替え**: ワークスペースまたはディレクトリ分離

**ディレクトリ構成案**:

```
terraform/
├── modules/           # 共通モジュール（変更なし）
└── environments/
    ├── dev/
    │   ├── main.tf
    │   └── terraform.tfvars
    ├── staging/
    │   ├── main.tf
    │   └── terraform.tfvars
    └── production/
        ├── main.tf
        └── terraform.tfvars
```

#### 3. デプロイガイドの整備

- **セットアップガイド**: 初回セットアップ手順の詳細化
- **環境構築チェックリスト**: AWS アカウント準備、IAM 権限、環境変数設定
- **トラブルシューティング**: よくある問題と解決方法

#### 4. CI/CD 環境の汎用化

- **GitLab Runner**: セルフホスト / GitLab.com Shared Runners の選択肢
- **環境変数テンプレート**: GitLab CI/CD Variables の設定例
- **複数環境デプロイ**: dev/staging/prod の自動デプロイ

### 期待される効果

テンプレート化により、以下の効果が期待できます：

- ✅ **第三者が独自の AWS 環境で利用可能**: AWS アカウントがあれば誰でも構築可能
- ✅ **複数環境への展開が容易**: dev/staging/prod を簡単に構築
- ✅ **チーム開発での再利用性向上**: 他のプロジェクトでも利用可能
- ✅ **オープンソース的活用**: コミュニティへの貢献、テンプレートとして公開

### 実装時期

- **Phase 1**: terraform.tfvars.example の作成、セットアップガイドの整備（1-2 日）
- **Phase 2**: 環境別設定の分離、変数化の徹底（2-3 日）
- **Phase 3**: CI/CD 環境の汎用化、ドキュメント整備（2-3 日）

---

**作成日**: 2025-10-30
**最終更新**: 2025-10-30
**バージョン**: 2.0
