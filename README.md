# 連絡帳管理システム

中学校向け生徒・担任間連絡管理システム。生徒が日々の振り返りを記録し、担任が確認・フィードバックを行う Web アプリケーション。

## 技術スタック

- **Backend**: Python 3.12 / Django 5.1
- **Database**: PostgreSQL 16
- **Cache/Queue**: Redis 7
- **Task Queue**: Celery 5.4
- **Infrastructure**: Docker / Docker Compose
- **Admin UI**: django-jazzmin
- **Forms**: django-crispy-forms (Bootstrap 5)

## 主要機能

### 生徒向け機能

- 連絡帳の作成・提出
- 体調・メンタル状態の記録
- 過去の連絡帳閲覧

### 担任向け機能

- 連絡帳の確認・既読管理
- 担任メモの作成・共有
- クラス単位での一覧表示

### 管理者機能

- ユーザー・クラス管理
- データの一括管理
- 検索・フィルタ機能

## クイックスタート

```bash
# 1. Docker起動
docker compose -f docker-compose.local.yml up -d

# 2. マイグレーション
docker compose -f docker-compose.local.yml run --rm django python manage.py migrate

# 3. テストデータ投入
docker compose -f docker-compose.local.yml run --rm django python manage.py setup_dev

# 4. アクセス
# http://localhost:8000 (管理者: admin/admin123)
```

### アクセス URL

- **開発サーバー**: http://localhost:8000
- **管理画面**: http://localhost:8000/admin
- **Mailpit（メール確認）**: http://localhost:8025

## テストアカウント

### 管理者

- ユーザー名: `admin`
- パスワード: `admin123`

### 担任

- ユーザー名: `teacher_1_A` ～ `teacher_3_B`（6 名）
- パスワード: `password123`
- 担当クラス: 1 年 A 組 ～ 3 年 B 組

### 生徒

- ユーザー名: `student_001` ～ `student_030`（30 名）
- パスワード: `password123`
- 各クラス 5 名ずつ配置済み

## ドキュメント

プロジェクトの設計・仕様に関するドキュメントは `docs/` ディレクトリに格納されています。

- [要件定義書](docs/要件定義書.md)
- [データモデル設計書](docs/データモデル設計書.md)
- [機能仕様書](docs/機能仕様書.md)
- [システムアーキテクチャ設計書](docs/システムアーキテクチャ設計書.md)
- [テスト計画書](docs/テスト計画書.md)

## コード品質管理

### Lint 設定の方針

本プロジェクトは日本語業務アプリケーションのため、ruff 設定を業界標準（Instagram, Sentry, GitLab等）に準拠させています。

**主な設定:**
- `line-length: 120`（Django標準）
- 全角文字許可: `RUF001/002/003`（日本語UI対応）
- print文許可: `T201`（開発スクリプト用）
- テストコード緩和: `S106`（ハードコードパスワード）、`PT009`（unittest assertion）

### 技術的負債

現在362件のlint警告をignore設定しており、全てスタイル・保守性に関する項目です。セキュリティ・バグリスクは解決済みです。

**優先度 High: なし**
- セキュリティ・バグリスクは全て解決済み

**優先度 Medium: 73件（AWS Phase完了後に対応予定）**
- `ERA001`（55件）: コメントアウトコード削除
- `DTZ011`（13件）: timezone対応
- `E402`（5件）: import順序修正

**優先度 Low: 289件（将来の改善タスク）**
- `PLC0415`（99件）: import位置（保守性改善）
- `PLR2004`（63件）: マジックナンバー（可読性改善）
- その他: 複雑度、logging、スタイル改善

**設計判断の根拠:**
- データ駆動の意思決定（ROI計算、リスク評価）
- クリティカルパス保護（デプロイ成功を最優先）
- 透明性（負債を明示し、計画的に管理）

## 開発環境

本プロジェクトは Claude Code（AI ペアプログラミングツール）を使用して開発されました。AI はコード生成補助、デバッグ支援を担当し、設計・実装・テストの最終判断は開発者が実施しています。
