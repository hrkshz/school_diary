# プロジェクト情報

## プロジェクト憲章

**目的**: 30分で「動く・再現できる・説明できる」業務Webアプリを完成させる

**完了の定義（DoD）**:
- `/health` エンドポイントが200を返す
- `/admin` に管理者ログインできる
- 主要なビジネスフローが一貫して動作する
- 誰でも30分で環境を再現できる

## 技術スタック

- **基盤**: cookiecutter-django
- **言語・FW**: Python 3.12 / Django 5.x
- **DB**: PostgreSQL
- **非同期**: Celery / Redis
- **UI**: Bootstrap 5
- **依存管理**: pyproject.toml + uv

## 開発ワークフロー

**基本方針**: ホストOS（VS Code/Cursor）→ WSL2（ソースコード）→ Docker Compose（実行環境）

**必須エイリアス** (`.bashrc`に設定):
```bash
alias dc='docker compose -f docker-compose.local.yml'
alias dj='docker compose -f docker-compose.local.yml run --rm django python manage.py'
```

## アクセスURL

- **開発サーバー**: http://localhost:8000
- **管理画面**: http://localhost:8000/admin
- **Mailpit（メール確認）**: http://localhost:8025
- **Flower（Celeryモニタリング）**: http://localhost:5555

## 現在進行中のプロジェクト

**連絡帳管理システム（school_diary）** - 中学校向け生徒・担任連絡帳管理
- Phase: MVP (Minimum Viable Product)
- 詳細: docs-private/PROJECT_STATUS.md 参照
