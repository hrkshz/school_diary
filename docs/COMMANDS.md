# よく使うコマンド

## Docker環境

```bash
# 起動
dc up -d

# ビルド（依存関係変更後）
dc build

# ログ確認
dc logs -f django

# 停止
dc down
```

## Django管理コマンド

```bash
# マイグレーション
dj makemigrations
dj migrate

# テストユーザー作成（パスワード: password123）
dj setup_dev  # admin@example.com, approver@example.com, user@example.com

# 管理画面スーパーユーザー作成
dj createsuperuser

# Djangoシェル
dj shell
```

## テスト・Lint

```bash
# テスト実行
dj pytest

# カバレッジ
dj coverage run -m pytest
dj coverage report

# Ruff（Linter + Formatter）
dj ruff check .
dj ruff format .

# 型チェック
dj mypy school_diary

# テンプレートフォーマット
dj djlint --reformat .
```

## Just（タスクランナー）

```bash
just          # コマンド一覧
just up       # docker compose up -d
just down     # docker compose down
just manage makemigrations  # manage.py実行
```

## 依存関係管理

```bash
# 1. pyproject.toml を編集（唯一の情報源）
# 2. uv lock で依存関係を固定
uv lock

# 3. Dockerイメージに反映
dc build

# 4. コンテナ起動
dc up
```
