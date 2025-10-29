# ローカル環境構築ガイド

本書は連絡帳管理システムをローカル環境で動作させる手順を記載しています。
評価者が10分でシステムを動作確認できるように設計されています。

**本番環境のデプロイ手順**: `PRODUCTION_DEPLOYMENT.md` を参照してください。

---

## 目次

1. [概要](#概要)
2. [前提条件](#前提条件)
3. [クイックスタート（10分）](#クイックスタート10分)
4. [動作確認](#動作確認)
5. [トラブルシューティング](#トラブルシューティング)

---

## 概要

### 本書の目的

- 評価者がローカル環境でシステムを10分で動作確認できる
- 開発者がローカル環境を構築して開発を開始できる

### 対象読者

- システムの評価者
- 開発者
- ローカル環境での動作確認を行いたい方

### システム構成

- **Django 5.x**: Webアプリケーションフレームワーク
- **PostgreSQL 16**: データベース
- **Docker Compose**: コンテナオーケストレーション
- **Mailpit**: 開発用メールサーバー

---

## 前提条件

以下がインストール済みであることを確認してください：

```bash
# OS確認
cat /etc/os-release | grep -E "PRETTY_NAME|VERSION_ID"
# 期待: Ubuntu 24.04 LTS（またはDocker対応OS）

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

### 未インストールの場合

- **Docker**: https://docs.docker.com/get-docker/
- **Git**: `sudo apt install -y git`（Ubuntu/Debian系）

---

## クイックスタート（10分）

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

#### setup.sh が実行する内容

1. ✅ **前提条件チェック**: Docker, Docker Composeのインストール確認
2. ✅ **ポート競合チェック**: 8000, 8025番ポートが使用可能か確認
3. ✅ **環境変数ファイル生成**: データベース接続情報等の設定ファイルを作成（`.envs/.local/`）
4. ✅ **Dockerコンテナ構築**: Django, PostgreSQL, Mailpitの3つのコンテナをビルド・起動
5. ✅ **データベース初期化**: テーブル作成（マイグレーション実行）
6. ✅ **テストデータ投入**: 管理者1名、担任9名、生徒270名、日記約6,500件を自動生成

**安全性**: このスクリプトは独立した環境を構築するため、既存のシステムには影響しません。

#### 期待される出力

```
================================================
セットアップ完了
================================================

アクセスURL:
  開発サーバー: http://localhost:8000
  管理画面: http://localhost:8000/admin
  メール確認: http://localhost:8025

テストアカウント:
  管理者: admin@example.com / password123
```

### Step 4: 動作確認

自動セットアップが完了したら、以下のコマンドで動作確認します。

```bash
# 動作確認スクリプト実行
./verify.sh
```

#### verify.sh が実行する内容

1. ✅ **Dockerコンテナ起動確認**: 3つのコンテナ（Django, PostgreSQL, Mailpit）が起動しているか
2. ✅ **データベース接続確認**: PostgreSQLに正常に接続できるか
3. ✅ **Webサーバー応答確認**: Djangoアプリケーションが正常に応答するか
4. ✅ **テストユーザー確認**: テストデータが正しく作成されたか（284名）
5. ✅ **管理画面アクセス確認**: 管理画面にアクセスできるか

#### 期待される出力

```
================================================
検証OK: すべての項目をクリアしました (5/5)
================================================

次のステップ:
  1. ブラウザで http://localhost:8000 にアクセス
  2. 管理者アカウントでログイン: admin@example.com / password123
  3. 機能を試してみてください
```

### Step 5: ブラウザでアクセス

ブラウザを開き、以下のURLにアクセスします。

- **アプリケーション**: http://localhost:8000
- **管理画面**: http://localhost:8000/admin
- **Mailpit（メール確認）**: http://localhost:8025

#### ポート番号を変更した場合

- `DJANGO_PORT=8100` を設定した場合: http://localhost:8100
- `MAILPIT_PORT=8125` を設定した場合: http://localhost:8125

#### ログイン

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

#### 解決方法1: 使用中のプロセスを停止

```bash
# ポート8000を使用しているプロセスを確認
lsof -i :8000

# プロセスを停止（PIDは上記コマンドで確認）
kill -9 <PID>
```

#### 解決方法2: 別のポートを使用（推奨）

```bash
# 環境変数でポート番号を変更
export DJANGO_PORT=8100
export MAILPIT_PORT=8125

# セットアップ実行
./setup.sh

# アクセスURL: http://localhost:8100
```

#### 環境変数の影響範囲について

`export DJANGO_PORT=8100` を実行した場合：

- ✅ **影響あり**: 現在のターミナルセッションのみ
- ❌ **影響なし**: 他のターミナルウィンドウ、他のユーザー、システム全体、他のプロジェクト

**つまり**: このターミナルウィンドウを閉じるまで有効で、他には一切影響しません。

#### 恒久的な設定（オプション）

ターミナルを閉じても設定を保持したい場合は、`.env` ファイルを作成します：

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

## まとめ

本ガイドではローカル環境での動作確認手順を説明しました。

- ✅ `./setup.sh` で10分で環境構築
- ✅ `./verify.sh` で動作確認
- ✅ 284名のテストユーザー（管理者、校長、学年主任、担任、生徒）
- ✅ 約6,500件のテストデータ（30日分の日記）

**本番環境へのデプロイ**: `PRODUCTION_DEPLOYMENT.md` を参照してください。

---

**作成日**: 2025-10-30
**最終更新**: 2025-10-30
**バージョン**: 1.0
