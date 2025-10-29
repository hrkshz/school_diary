# 連絡帳管理システム

中学校向け生徒・担任間連絡管理システム。生徒が日々の振り返りを記録し、担任が確認・フィードバックを行う Web アプリケーション。

**技術スタック**: Python 3.12 / Django 5.1 / PostgreSQL 16 / Docker

## インフラ構成

![インフラ構成図](doc/infrastructure-architecture.png)

## 本番環境

**URL**: https://d2wk3j2pacp33b.cloudfront.net

**テストアカウント**（パスワード: `password123`）:

- 生徒: `student_001@example.com`（1 年 A 組 山田太郎）
- 担任: `teacher_1_b@example.com`（1 年 B 組担任）
- 学年主任: `teacher_1_a@example.com`（1 年 A 組担任 兼 1 年学年主任）
- 校長: `principal@example.com`
- 管理者: `admin@example.com`

全アカウント一覧: [MANUAL_FOR_CLIENT.md](doc/MANUAL_FOR_CLIENT.md)

## ドキュメント

### デプロイガイド

- **[LOCAL_DEPLOYMENT.md](doc/LOCAL_DEPLOYMENT.md)** - ローカル環境構築（10分で動作確認）
  - 評価者、開発者向け
  - Docker Composeで簡単セットアップ
  - テストデータ自動生成
- **[PRODUCTION_DEPLOYMENT.md](doc/PRODUCTION_DEPLOYMENT.md)** - 本番環境デプロイ
  - インフラエンジニア、評価者向け
  - Terraformによるインフラ構築（AWS）
  - GitLab CI/CDによる自動デプロイ
  - 運用管理、監視設定

### その他ドキュメント

- [MANUAL_FOR_CLIENT.md](doc/MANUAL_FOR_CLIENT.md) - 操作マニュアル
- [FEATURES.md](doc/FEATURES.md) - 機能一覧、セキュリティポリシー
- [データモデル設計書](docs/04-data-model.md) - ER 図含む
