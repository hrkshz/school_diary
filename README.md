# 連絡帳管理システム

中学校向け生徒・担任間連絡管理システム。生徒が日々の振り返りを記録し、担任が確認・フィードバックを行う Web アプリケーション。

## 技術スタック

- **Backend**: Python 3.12 / Django 5.1
- **Database**: PostgreSQL 16
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
# 自動セットアップ（推奨）
./setup.sh

# 動作確認
./verify.sh

# ブラウザで http://localhost:8000 にアクセス
# 管理者: admin / admin123
```

**詳細な手順・トラブルシューティング**: [SETUP.md](SETUP.md) を参照

### アクセス URL

- **開発サーバー**: http://localhost:8000
- **管理画面**: http://localhost:8000/admin
- **Mailpit（メール確認）**: http://localhost:8025

## テストアカウント

### 管理者

- メールアドレス: `admin@example.com`
- パスワード: `password123`

### 担任

- メールアドレス: `teacher_1_a@example.com` ～ `teacher_3_c@example.com`（9 名）
- パスワード: `password123`
- 担当クラス: 1 年 A 組 ～ 3 年 C 組

### 生徒

- メールアドレス: `student_1_a_01@example.com` ～ `student_3_c_30@example.com`（270 名）
- パスワード: `password123`
- 各クラス 30 名ずつ配置済み

## ドキュメント

プロジェクトの設計・仕様に関するドキュメントは `docs/` ディレクトリに格納されています。

- [要件定義書](docs/01-requirements.md)
- [システム概要](docs/02-system-overview.md)
- [機能一覧](docs/03-features.md)
- [データモデル設計書](docs/04-data-model.md)
- [アーキテクチャ設計書](docs/05-architecture.md)
- [テスト戦略・結果](docs/07-testing/)

## コード品質管理

本プロジェクトは Django ベストプラクティスに従い、以下のツールで品質を担保しています。

**Lint / Format:**
- Ruff（Django 標準設定、line-length: 120）
- 日本語 UI 対応のため一部ルール緩和（`RUF001/002/003`）
- セキュリティ・バグリスクは全て解決済み

**Type Check:**
- mypy（strict モード）

**Testing:**
- pytest（カバレッジ: 150+ テスト）
