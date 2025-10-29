# デプロイ手順

本書は連絡帳管理システムをUbuntu 24.04環境で動作させる手順を記載しています。

---

## 目次

1. [ローカル環境構築（10分）](#ローカル環境構築10分)
2. [動作確認](#動作確認)
3. [トラブルシューティング](#トラブルシューティング)
4. [本番環境デプロイ（AWS）](#本番環境デプロイaws)

---

## ローカル環境構築（10分）

評価者がすぐにシステムを動かせる手順を記載します。

### 前提条件

以下がインストール済みであることを確認してください：

```bash
# OS確認
cat /etc/os-release | grep -E "PRETTY_NAME|VERSION_ID"
# 期待: Ubuntu 24.04 LTS

# RAM確認（4GB以上必要）
free -h | grep Mem

# ディスク容量確認（10GB以上必要）
df -h .

# Docker確認
docker --version
# 期待: Docker version 20.10以降

# Docker Compose確認
docker compose version
# 期待: Docker Compose version v2.0以降

# Git確認
git --version
# 期待: git version 2.30以降
```

**未インストールの場合**:
- Docker: https://docs.docker.com/get-docker/
- Git: `sudo apt install -y git`

### Step 1: 作業ディレクトリの作成

任意の場所にプロジェクト用ディレクトリを作成します。

```bash
# 例: ホームディレクトリ配下に作成
mkdir -p ~/projects/school-diary-eval
cd ~/projects/school-diary-eval

# 現在のディレクトリを確認
pwd
```

**ポイント**: ディレクトリ名は任意です。評価しやすい場所を選択してください。

### Step 2: プロジェクトのクローン

作成したディレクトリ内にプロジェクトをクローンします。

```bash
# カレントディレクトリにクローン
git clone <リポジトリURL> .

# ファイル確認
ls -la

# ブランチ確認（mainブランチであることを確認）
git branch
```

**注意**: `git clone <URL> .` の最後の `.` は重要です（カレントディレクトリに展開）。

### Step 3: 自動セットアップ

プロジェクトに用意されている自動セットアップスクリプトを実行します。

```bash
# セットアップスクリプトに実行権限を付与
chmod +x setup.sh verify.sh

# 自動セットアップ実行（所要時間: 約5分）
./setup.sh
```

**setup.shが実行する内容**:
1. Dockerコンテナのビルド（Django, PostgreSQL）
2. データベースマイグレーション実行
3. テストデータ作成（管理者、担任9名、生徒270名）
4. 静的ファイルの収集
5. 動作確認

**期待される出力**:
```
✅ セットアップが完了しました！

🌐 アクセスURL: http://localhost:8000
👤 管理者アカウント: admin@example.com / password123
```

### Step 4: 動作確認

自動セットアップが完了したら、以下のコマンドで動作確認します。

```bash
# 動作確認スクリプト実行
./verify.sh
```

**期待される出力**:
```
✅ Djangoサーバーが起動しています
✅ PostgreSQLに接続できます
✅ 管理画面にアクセスできます
✅ テストアカウントでログインできます
```

### Step 5: ブラウザでアクセス

ブラウザを開き、以下のURLにアクセスします。

- **アプリケーション**: http://localhost:8000
- **管理画面**: http://localhost:8000/admin
- **Mailpit（メール確認）**: http://localhost:8025

**ポート番号を変更した場合**:
- `DJANGO_PORT=8100` を設定した場合: http://localhost:8100
- `MAILPIT_PORT=8125` を設定した場合: http://localhost:8125

**ログイン**:
- メールアドレス: `admin@example.com`
- パスワード: `password123`

---

## 動作確認

**注意**: 以下のURL例はデフォルトポート（8000）を使用しています。ポート番号を変更した場合は、適宜読み替えてください（例: 8100に変更した場合は `http://localhost:8100`）。

### 1. 管理画面にログイン

1. http://localhost:8000/admin にアクセス
2. `admin@example.com` / `password123` でログイン
3. 「連絡帳エントリー」「クラス」「ユーザー」が表示されることを確認

### 2. 生徒として連絡帳作成

1. http://localhost:8000/accounts/logout/ でログアウト
2. http://localhost:8000/accounts/login/ にアクセス
3. `student_1_a_01@example.com` / `password123` でログイン
4. 「今日の連絡帳を書く」ボタンをクリック
5. 体調・メンタル・振り返りを入力して提出
6. 生徒ダッシュボードに連絡帳が表示されることを確認

### 3. 担任として連絡帳確認

1. http://localhost:8000/accounts/logout/ でログアウト
2. http://localhost:8000/accounts/login/ にアクセス
3. `teacher_1_a@example.com` / `password123` でログイン
4. 担任ダッシュボードに「P2-2（未読）」として連絡帳が表示されることを確認
5. 「既読にする」ボタンをクリック
6. 反応を選択して保存

---

## トラブルシューティング

### Dockerが起動しない

```bash
# Dockerサービスの状態確認
sudo systemctl status docker

# Dockerサービスの起動
sudo systemctl start docker

# Dockerサービスの自動起動設定
sudo systemctl enable docker
```

### ポート競合エラー

**症状**:
```
Error starting userland proxy: listen tcp4 0.0.0.0:8000: bind: address already in use
```

または setup.sh 実行時：
```
エラー: ポート 8000 (Django) は既に使用中です
```

**解決方法1**: 使用中のプロセスを停止
```bash
# ポート8000を使用しているプロセスを確認
lsof -i :8000

# プロセスを停止（PIDは上記コマンドで確認）
kill -9 <PID>
```

**解決方法2**: 別のポートを使用（推奨）
```bash
# 環境変数でポート番号を変更
export DJANGO_PORT=8100
export MAILPIT_PORT=8125

# セットアップ実行
./setup.sh

# アクセスURL: http://localhost:8100
```

**恒久的な設定（オプション）**:
```bash
# .env ファイルを作成
echo "DJANGO_PORT=8100" > .env
echo "MAILPIT_PORT=8125" >> .env

# 以降は自動的に8100, 8125を使用
./setup.sh
```

### Dockerビルドエラー

**症状**:
```
failed to compute cache key: "/compose/local/django/start": not found
```

**原因**: .dockerignore の設定により、ローカル開発に必要なファイルが除外されている

**解決方法**:
```bash
# .dockerignore の該当行をコメントアウト
sed -i '71s/^compose\/local\//# compose\/local\//' .dockerignore

# 再度セットアップ実行
./setup.sh
```

**確認**:
```bash
# 修正されたことを確認
grep "compose/local" .dockerignore
# 期待: # compose/local/  (コメントアウト済み)
```

### データベースに接続できない

```bash
# PostgreSQLコンテナのログ確認
docker compose -f docker-compose.local.yml logs postgres

# PostgreSQLコンテナの再起動
docker compose -f docker-compose.local.yml restart postgres

# データベースのリセット（全データ削除）
docker compose -f docker-compose.local.yml down -v
./setup.sh
```

### テストデータが作成されない

```bash
# 手動でテストデータ作成
docker compose -f docker-compose.local.yml run --rm django python manage.py setup_dev

# マイグレーションの再実行
docker compose -f docker-compose.local.yml run --rm django python manage.py migrate
```

### コンテナのログ確認

```bash
# 全コンテナのログ表示
docker compose -f docker-compose.local.yml logs

# Djangoコンテナのログのみ表示
docker compose -f docker-compose.local.yml logs django

# リアルタイムでログ表示
docker compose -f docker-compose.local.yml logs -f django
```

### コンテナの停止・再起動

```bash
# コンテナの停止
docker compose -f docker-compose.local.yml stop

# コンテナの起動
docker compose -f docker-compose.local.yml start

# コンテナの再起動
docker compose -f docker-compose.local.yml restart

# コンテナの完全削除（データも削除）
docker compose -f docker-compose.local.yml down -v
```

---

## 本番環境デプロイ（AWS）

本プロジェクトは本番グレードのAWSインフラ構築をTerraformで実現しています。

### アーキテクチャ概要

```
インターネット
    ↓
CloudFront（CDN）
    ↓
Network Load Balancer
    ↓
EC2（Django + Gunicorn）
    ↓
RDS（PostgreSQL）
```

### 主要コンポーネント

| コンポーネント | 役割 | 冗長化 |
|-------------|------|-------|
| **CloudFront** | CDN、静的ファイル配信 | グローバル |
| **NLB** | ロードバランサー、SSL終端 | Multi-AZ対応可能 |
| **EC2** | Djangoアプリケーション | Auto Scaling対応可能 |
| **RDS** | PostgreSQLデータベース | Multi-AZ対応可能 |
| **CloudWatch** | 監視・ログ | - |

### Terraformによるインフラ構築

本プロジェクトは14モジュールに分割されたTerraform構成を採用しています。

```bash
# Terraformディレクトリ構造
terraform/
├── modules/
│   ├── vpc/                  # VPC、サブネット、ルートテーブル
│   ├── security_groups/      # セキュリティグループ
│   ├── ec2/                  # EC2インスタンス
│   ├── rds/                  # RDS（PostgreSQL）
│   ├── nlb/                  # Network Load Balancer
│   ├── cloudfront/           # CloudFront CDN
│   ├── cloudwatch/           # CloudWatch監視
│   └── ...                   # その他12モジュール
├── main.tf                   # メイン設定
├── variables.tf              # 変数定義
├── outputs.tf                # 出力定義
└── terraform.tfvars          # 変数値（Git管理外）
```

### デプロイ手順（Terraform）

```bash
# 1. Terraformのインストール（Ubuntu）
wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update && sudo apt install terraform

# 2. AWSクレデンシャルの設定
export AWS_ACCESS_KEY_ID="<your-access-key>"
export AWS_SECRET_ACCESS_KEY="<your-secret-key>"
export AWS_DEFAULT_REGION="ap-northeast-1"

# 3. Terraformの初期化
cd terraform
terraform init

# 4. Terraformの計画確認
terraform plan

# 5. インフラの構築（約10分）
terraform apply

# 6. 出力情報の確認
terraform output
```

**期待される出力**:
```
cloudfront_domain = "d2wk3j2pacp33b.cloudfront.net"
ec2_public_ip = "54.xxx.xxx.xxx"
rds_endpoint = "school-diary.xxx.ap-northeast-1.rds.amazonaws.com"
```

### アプリケーションのデプロイ

Terraform実行後、EC2インスタンスにSSHで接続してアプリケーションをデプロイします。

```bash
# 1. EC2にSSH接続
ssh -i <秘密鍵> ubuntu@<EC2のパブリックIP>

# 2. Dockerのインストール（EC2上）
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# 3. プロジェクトのクローン（EC2上）
git clone <リポジトリURL> school_diary
cd school_diary

# 4. 環境変数の設定（EC2上）
cp .envs/.production/.django.example .envs/.production/.django
cp .envs/.production/.postgres.example .envs/.production/.postgres

# 環境変数の編集（RDSエンドポイント、SECRET_KEYなど）
nano .envs/.production/.django

# 5. 本番環境の起動（EC2上）
docker compose -f docker-compose.production.yml up -d

# 6. マイグレーション実行（EC2上）
docker compose -f docker-compose.production.yml run --rm django python manage.py migrate

# 7. スーパーユーザー作成（EC2上）
docker compose -f docker-compose.production.yml run --rm django python manage.py createsuperuser
```

### セキュリティ設定

- **セキュリティグループ**: 必要最小限のポート開放（80, 443のみ）
- **RDS**: プライベートサブネットに配置、EC2からのみアクセス可能
- **CloudWatch**: アプリケーションログ、エラーログを記録
- **SSL/TLS**: ACM証明書によるHTTPS通信

### 監視・運用

- **CloudWatch Alarms**: CPU使用率、メモリ使用率、RDS接続数
- **CloudWatch Logs**: アプリケーションログ、エラーログ
- **RDS自動バックアップ**: 日次バックアップ、保持期間7日

### コスト試算

| リソース | インスタンスタイプ | 月額コスト（概算） |
|---------|-----------------|-----------------|
| EC2 | t3.small | $15 |
| RDS | db.t3.micro | $15 |
| CloudFront | データ転送量依存 | $5-10 |
| NLB | 時間課金 | $20 |
| **合計** | - | **$55-60** |

---

## まとめ

本プロジェクトは以下の2つのデプロイ方法を提供します。

1. **ローカル環境**（評価用）: `./setup.sh` で10分で動作
2. **本番環境（AWS）**: Terraformで完全なIaC化、`terraform apply` で同一環境を構築可能

