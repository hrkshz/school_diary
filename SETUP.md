# 環境構築ガイド

連絡帳管理システムの開発環境を構築する手順を説明します。

## 前提条件

### 必須ソフトウェア

- **Docker Desktop** 20.10以降
- **Git** 2.30以降
- **メモリ**: 4GB以上の空きメモリ推奨

### Docker Desktop インストール

#### Windows
1. [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/) をダウンロード
2. インストーラーを実行
3. WSL 2バックエンドを有効化（推奨）
4. インストール完了後、再起動

#### macOS
1. [Docker Desktop for Mac](https://docs.docker.com/desktop/install/mac-install/) をダウンロード
2. `.dmg` ファイルをダブルクリック
3. Docker.app を Applications フォルダにドラッグ
4. Docker Desktop を起動

#### Linux
1. [Docker Engine](https://docs.docker.com/engine/install/) をインストール
2. [Docker Compose](https://docs.docker.com/compose/install/) をインストール
3. ユーザーをdockerグループに追加: `sudo usermod -aG docker $USER`
4. ログアウト後、再ログイン

### インストール確認

```bash
# Docker バージョン確認
docker --version

# Docker Compose バージョン確認
docker compose version
```

## クイックスタート

### 1. リポジトリクローン

```bash
git clone <repository-url>
cd school_diary
```

### 2. 自動セットアップ

```bash
./setup.sh
```

このスクリプトが以下を自動実行します：
- 環境変数ファイル生成
- Dockerコンテナビルド・起動
- データベース初期化
- テストデータ投入

**所要時間**: 初回 5〜10分、2回目以降 1〜2分

### 3. 動作確認

```bash
./verify.sh
```

全ての検証項目が ✓ になればセットアップ完了です。

### 4. アクセス

ブラウザで以下にアクセス：
- **開発サーバー**: http://localhost:8000
- **管理画面**: http://localhost:8000/admin
- **メール確認**: http://localhost:8025

**テストアカウント**:
- 管理者: `admin@example.com` / `password123`
- 担任: `teacher_1_a@example.com` / `password123`
- 生徒: `student_1_a_01@example.com` / `password123`

## 手動セットアップ

自動セットアップスクリプトが使えない場合、以下の手順で手動セットアップできます。

### 1. 環境変数ファイル生成

```bash
# ディレクトリ作成
mkdir -p .envs/.local

# テンプレートをコピー
cp .envs.example/.local/.django .envs/.local/.django
cp .envs.example/.local/.postgres .envs/.local/.postgres
```

### 2. Dockerコンテナ起動

```bash
# コンテナビルド・起動
docker compose -f docker-compose.local.yml up -d --build

# ログ確認（オプション）
docker compose -f docker-compose.local.yml logs -f
```

### 3. データベース初期化

```bash
# マイグレーション実行
docker compose -f docker-compose.local.yml run --rm django python manage.py migrate
```

### 4. テストデータ投入

```bash
# テストユーザー・データ作成
docker compose -f docker-compose.local.yml run --rm django python manage.py load_production_test_data --clear
```

### 5. 動作確認

```bash
./verify.sh
```

## トラブルシューティング

### エラー1: ポート競合

**症状**:
```
Error starting userland proxy: listen tcp4 0.0.0.0:8000: bind: address already in use
```

**原因**: 8000番ポートが既に使用中

**解決方法**:
```bash
# 使用中のプロセスを確認
lsof -ti:8000

# プロセスを停止
lsof -ti:8000 | xargs kill -9

# または、docker-compose.local.yml のポート番号を変更
# ports: - '8080:8000'  # 8000 → 8080 に変更
```

### エラー2: Docker Daemon未起動

**症状**:
```
error during connect: This error may indicate that the docker daemon is not running
```

**原因**: Docker Desktop が起動していない

**解決方法**:
- Docker Desktop を起動
- タスクバー（Windows）またはメニューバー（Mac）にDockerアイコンが表示されるまで待つ

### エラー3: マイグレーション失敗

**症状**: `No migrations to apply` だがテーブルが作られていない

**原因**: ボリュームに古いデータが残っている

**解決方法**:
```bash
# 全てのコンテナとボリュームを削除
docker compose -f docker-compose.local.yml down -v

# 再セットアップ
./setup.sh
```

## 検証方法

### 自動検証

```bash
./verify.sh
```

### 手動検証

#### 1. コンテナ起動確認
```bash
docker compose -f docker-compose.local.yml ps
# 全てのコンテナが "Up" になっていることを確認
```

#### 2. データベース接続確認
```bash
docker compose -f docker-compose.local.yml exec postgres psql -U debug -d school_diary -c '\dt'
# テーブル一覧が表示されることを確認
```

#### 3. Webサーバー確認
```bash
curl http://localhost:8000
# HTMLが返ってくることを確認
```

#### 4. 管理画面確認
ブラウザで http://localhost:8000/admin にアクセス
- ログイン画面が表示される
- `admin@example.com` / `password123` でログインできる

## 運用

### ログ確認

```bash
# 全サービスのログ確認
docker compose -f docker-compose.local.yml logs

# 特定サービスのログ確認
docker compose -f docker-compose.local.yml logs django

# リアルタイムログ
docker compose -f docker-compose.local.yml logs -f
```

### コンテナ管理

```bash
# コンテナ停止
docker compose -f docker-compose.local.yml stop

# コンテナ再起動
docker compose -f docker-compose.local.yml restart

# コンテナ削除（ボリュームは保持）
docker compose -f docker-compose.local.yml down

# コンテナ・ボリューム完全削除
docker compose -f docker-compose.local.yml down -v
```

## 関連ドキュメント

- [README.md](README.md) - プロジェクト概要
- [要件定義書](docs/01-requirements.md) - 機能要件
- [システム概要](docs/02-system-overview.md) - システム全体像
- [機能一覧](docs/03-features.md) - 機能詳細
- [データモデル設計書](docs/04-data-model.md) - データベース設計
- [アーキテクチャ設計書](docs/05-architecture.md) - 技術スタック

## 補足

### Windowsユーザー向け

- PowerShellではなく Git Bash または WSL を使用してください
- パスの区切り文字に注意（`\` ではなく `/`）

### 開発環境での注意点

- Djangoコードは自動リロードされます（コンテナ再起動不要）
- Docker Desktopのダッシュボードでコンテナの状態を確認できます
