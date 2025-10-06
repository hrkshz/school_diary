# LabApp

業務 Web アプリ共通土台の検証用プロジェクト

[![Built with Cookiecutter Django](https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg?logo=cookiecutter)](https://github.com/cookiecutter/cookiecutter-django/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

License: MIT

---

## 🚀 クイックスタート（5 分で起動）

```bash
# 1. エイリアスを設定（初回のみ）
echo "alias dc='docker compose'" >> ~/.bashrc
echo "alias dj='docker compose run --rm django python manage.py'" >> ~/.bashrc
source ~/.bashrc

# 2. 環境を起動
dc up -d

# 3. データベース初期化
dj migrate
dj setup_dev  # テストユーザー・グループを作成

# 4. 管理画面にアクセス
# http://localhost:8000/admin
# ユーザー: admin@example.com / パスワード: password123
```

**詳細は [オンボーディングガイド](docs/ONBOARDING.md) へ** 👉

## Settings

Moved to [settings](https://cookiecutter-django.readthedocs.io/en/latest/1-getting-started/settings.html).

## Basic Commands

### Setting Up Your Users

- To create a **normal user account**, just go to Sign Up and fill out the form. Once you submit it, you'll see a "Verify Your E-mail Address" page. Go to your console to see a simulated email verification message. Copy the link into your browser. Now the user's email should be verified and ready to go.

- To create a **superuser account**, use this command:

      uv run python manage.py createsuperuser

For convenience, you can keep your normal user logged in on Chrome and your superuser logged in on Firefox (or similar), so that you can see how the site behaves for both kinds of users.

### Type checks

Running type checks with mypy:

    uv run mypy school_diary

### Test coverage

To run the tests, check your test coverage, and generate an HTML coverage report:

    uv run coverage run -m pytest
    uv run coverage html
    uv run open htmlcov/index.html

#### Running tests with pytest

    uv run pytest

### Live reloading and Sass CSS compilation

Moved to [Live reloading and SASS compilation](https://cookiecutter-django.readthedocs.io/en/latest/2-local-development/developing-locally.html#using-webpack-or-gulp).

### Celery

This app comes with Celery.

To run a celery worker:

```bash
cd school_diary
uv run celery -A config.celery_app worker -l info
```

Please note: For Celery's import magic to work, it is important _where_ the celery commands are run. If you are in the same folder with _manage.py_, you should be right.

To run [periodic tasks](https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html), you'll need to start the celery beat scheduler service. You can start it as a standalone process:

```bash
cd school_diary
uv run celery -A config.celery_app beat
```

or you can embed the beat service inside a worker with the `-B` option (not recommended for production use):

```bash
cd school_diary
uv run celery -A config.celery_app worker -B -l info
```

### Email Server

In development, it is often nice to be able to see emails that are being sent from your application. For that reason local SMTP server [Mailpit](https://github.com/axllent/mailpit) with a web interface is available as docker container.

Container mailpit will start automatically when you will run all docker containers.
Please check [cookiecutter-django Docker documentation](https://cookiecutter-django.readthedocs.io/en/latest/2-local-development/developing-locally-docker.html) for more details how to start all containers.

With Mailpit running, to view messages that are sent by your application, open your browser and go to `http://127.0.0.1:8025`

## Deployment

The following details how to deploy this application.

### Docker

See detailed [cookiecutter-django Docker documentation](https://cookiecutter-django.readthedocs.io/en/latest/3-deployment/deployment-with-docker.html).

---

## 📚 プロジェクトドキュメント

### 新メンバー向け

- **[オンボーディングガイド](docs/ONBOARDING.md)** - プロジェクトに初めて参加する方は、まずこちらをお読みください
- **[Cursor 最適化設定ガイド](docs/CURSOR_SETUP.md)** - Cursor を AI メンターとして最大限活用する方法
- **[過去の課題一覧](docs/past-challenges/README.md)** - インターンシップで出題された課題とLabAppでの実装アプローチ

### 重要な設定ファイル

- **[.cursorrules](.cursorrules)** - Cursor に常に理解させるプロジェクトのルール
- **[.cursorignore](.cursorignore)** - AI に読ませない不要なファイルの定義
- **[.vscode/settings.json](.vscode/settings.json)** - プロジェクト固有のエディタ設定

### 開発のルール

- **プロジェクト憲章**: 30 分で「動く・再現できる・説明できる」業務 Web アプリを完成させる
- **二本の柱**: ① 準備の軸（必勝パターンの錬成） / ② 実践の軸（価値提供の高速化）
