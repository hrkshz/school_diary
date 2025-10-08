# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/ja/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- MLP-5: 生徒用ダッシュボード実装
  - 過去7日分の連絡帳一覧表示
  - 提出状態の可視化（既読・未読バッジ）
  - 新規作成・過去記録へのナビゲーションリンク
  - LoginRequiredMixinによるアクセス制御
  - select_related()によるクエリ最適化（N+1問題回避）

### Changed
- (なし)

### Deprecated
- (なし)

### Removed
- (なし)

### Fixed
- (なし)

### Security
- (なし)

---

## [0.1.0-mvp] - 2025-10-08

### Added
- MVP-1〜3: プロジェクト基盤構築
  - school_diaryプロジェクト作成
  - diaryアプリ作成・登録
  - データベース設計完了（ER図、SQL、設計書）

- MVP-4〜8: モデル・Admin実装
  - DiaryEntry（連絡帳エントリ）モデル
  - ClassRoom（クラス）モデル
  - TeacherNote（先生メモ）モデル
  - Django Admin登録（全モデル）
  - 一括既読機能（Admin Action）

- MVP-9〜10: テストデータ作成
  - テストユーザー作成コマンド（38名：管理者1、担任6、生徒30、クラス6）
  - サンプルデータ投入コマンド（730件の連絡帳、提出率80%、既読率71.1%）

- MVP-11: 管理画面カスタマイズ
  - 色分け表示実装（体調・メンタル5段階）
  - フィルター・検索機能
  - django-jazzmin導入（モダンUI）
  - 完全日本語化対応

- MVP-12: MVP完了確認
  - /health エンドポイント実装
  - v0.1.0-mvpタグ作成
  - 全DoD（完了の定義）達成

### Changed
- Django Admin UIをjazzminでモダン化
  - AdminLTE 3ベースのレスポンシブUI
  - メニュー順序最適化（業務フロー順）
  - Font Awesomeアイコン設定

### Technical
- **Stack**:
  - Python 3.12
  - Django 5.1.12
  - PostgreSQL
  - Redis
  - Celery
  - Bootstrap 5
  - django-jazzmin 3.0.1

- **Infrastructure**:
  - Docker Compose開発環境
  - WSL2（Windows環境）
  - uv（依存関係管理）

---

## バージョニング方針

### Phase別バージョン体系
- **MVP期間**: 0.1.x-mvp（Minimum Viable Product）
- **MLP期間**: 0.2.x-mlp（Minimum Lovable Product）
- **MAP期間**: 0.3.x-map（Minimum Awesome Product）
- **AWS期間**: 0.9.x-aws（AWS Deployment）
- **DOC期間**: 1.0.x（Production Ready）

### リリースタグ
- `v0.1.0-mvp`: 2025-10-08（MVP完了）
- `v0.2.0-mlp`: TBD（MLP完了予定）
- `v0.3.0-map`: TBD（MAP完了予定）
- `v0.9.0-aws`: TBD（AWS完了予定）
- `v1.0.0`: TBD（Production完了予定）

---

## Keep a Changelog形式について

このCHANGELOGは [Keep a Changelog](https://keepachangelog.com/ja/1.0.0/) 形式に従っています。

### 6つの変更カテゴリ
1. **Added**: 新機能
2. **Changed**: 既存機能の変更
3. **Deprecated**: 非推奨（将来削除予定の機能）
4. **Removed**: 削除された機能
5. **Fixed**: バグ修正
6. **Security**: セキュリティ修正

### 記述ルール
- 変更は新しいものが上
- 各バージョンにリリース日を記載
- 技術的詳細は適度に（ユーザー視点で理解できる範囲）
- 内部実装の変更は省略可（大きな変更のみ記載）

---

**作成者**: Claude Code + hirok
**最終更新**: 2025-10-09
