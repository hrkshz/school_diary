# 連絡帳管理システム システムアーキテクチャ設計書

> **作成日**: 2025-10-07
> **バージョン**: 1.0.0
> **ステータス**: Draft
> **対象**: 連絡帳管理システムPoC開発

---

## 📋 目次

1. [概要](#1-概要)
2. [技術スタック](#2-技術スタック)
3. [アーキテクチャ図](#3-アーキテクチャ図)
4. [ディレクトリ構成](#4-ディレクトリ構成)
5. [デプロイ戦略](#5-デプロイ戦略)
6. [セキュリティ](#6-セキュリティ)
7. [パフォーマンス](#7-パフォーマンス)

---

## 1. 概要

### 1.1 アーキテクチャ方針

| 方針 | 内容 |
|-----|------|
| **シンプルさ優先** | PoC段階では複雑な構成を避け、MVPに集中 |
| **標準技術の活用** | Django標準機能を最大限活用 |
| **拡張性の確保** | 将来の機能追加に対応可能な設計 |
| **クラウドネイティブ** | クラウド環境へのデプロイを想定 |

### 1.2 システム構成の特徴

- **モノリシック構成**: 単一のDjangoアプリケーション
- **PostgreSQLデータベース**: リレーショナルデータの管理
- **非同期処理**: Celery + Redis（将来の拡張用）
- **静的ファイル配信**: Whitenoise
- **フロントエンド**: サーバーサイドレンダリング（Django Templates）

---

## 2. 技術スタック

### 2.1 バックエンド

| 技術 | バージョン | 用途 |
|-----|-----------|------|
| **Python** | 3.12 | プログラミング言語 |
| **Django** | 5.1.x | Webフレームワーク |
| **PostgreSQL** | 16 | データベース |
| **Celery** | 最新 | 非同期タスク処理（将来用） |
| **Redis** | 最新 | Celeryのブローカー |
| **Gunicorn** | 最新 | WSGIサーバー（本番環境） |

#### 主要Djangoライブラリ

| ライブラリ | 用途 |
|-----------|------|
| **django-crispy-forms** | フォームレイアウト |
| **crispy-bootstrap5** | Bootstrap5統合 |
| **django-environ** | 環境変数管理 |
| **psycopg2** | PostgreSQLアダプタ |
| **whitenoise** | 静的ファイル配信 |

### 2.2 フロントエンド

| 技術 | バージョン | 用途 |
|-----|-----------|------|
| **Bootstrap** | 5.3 | CSSフレームワーク |
| **Chart.js** | 4.x | グラフ描画（課題2） |
| **Django Templates** | - | サーバーサイドレンダリング |

### 2.3 開発ツール

| ツール | 用途 |
|-------|------|
| **uv** | 依存関係管理 |
| **Ruff** | Linter / Formatter |
| **pytest** | テストフレームワーク |
| **pytest-django** | Django用テストツール |
| **pytest-cov** | カバレッジ測定 |
| **pre-commit** | コミット前チェック |
| **mypy** | 型チェック |

### 2.4 インフラ

| 項目 | 技術 | 備考 |
|-----|------|------|
| **開発環境** | Docker Compose | ローカル開発 |
| **本番環境** | Render.com / Railway.app | 推奨クラウドサービス |
| **CI/CD** | GitHub Actions | 自動テスト・デプロイ |
| **バージョン管理** | Git / GitLab | quest_1リポジトリ |

---

## 3. アーキテクチャ図

### 3.1 全体構成図

```
+------------------+
|     ブラウザ      |
|  (Edge/Chrome)   |
+--------+---------+
         |
         | HTTPS
         v
+------------------+
|   Web Server     |
| (Nginx/Gunicorn) |
+--------+---------+
         |
         v
+------------------+
| Django App       |
| - MVT Pattern    |
| - ORM            |
| - Admin          |
+--------+---------+
         |
         +------------------+
         |                  |
         v                  v
+------------------+  +------------------+
| PostgreSQL       |  | Redis (将来)     |
| - User           |  | - Celery Broker  |
| - DiaryEntry     |  | - Cache          |
| - ClassRoom      |  +------------------+
| - TeacherNote    |
+------------------+
```

### 3.2 Django MVTパターン

```
Request
   ↓
urls.py (URLconf)
   ↓
views.py (View)
   ↓
models.py (Model) ← → PostgreSQL
   ↓
templates/ (Template)
   ↓
Response
```

### 3.3 データフロー（連絡帳提出）

```
生徒ブラウザ
   ↓ POST /diary/create
Django View (diary/views.py)
   ↓ form.save()
Django ORM (diary/models.py)
   ↓ INSERT INTO diary_entry
PostgreSQL
   ↓ リダイレクト
生徒ダッシュボード
```

---

## 4. ディレクトリ構成

### 4.1 プロジェクト全体

```
school_diary/
├── school_diary/              # プロジェクト設定
│   ├── __init__.py
│   ├── settings.py            # 設定ファイル
│   ├── urls.py                # ルートURLconf
│   ├── wsgi.py                # WSGIエントリーポイント
│   └── asgi.py                # ASGIエントリーポイント
│
├── diary/                     # 連絡帳アプリ（メイン）
│   ├── __init__.py
│   ├── models.py              # DiaryEntry, ClassRoom, TeacherNote
│   ├── views.py               # ビュー関数/クラス
│   ├── forms.py               # フォーム定義
│   ├── admin.py               # Admin設定
│   ├── urls.py                # アプリURLconf
│   ├── tests.py               # テストコード
│   ├── templates/             # テンプレート
│   │   └── diary/
│   │       ├── dashboard.html
│   │       ├── entry_create.html
│   │       ├── entry_list.html
│   │       └── ...
│   └── migrations/            # マイグレーションファイル
│       └── 0001_initial.py
│
├── kits/                      # 共通部品パッケージ
│   ├── accounts/              # ユーザー管理
│   ├── approvals/             # 承認フロー
│   ├── audit/                 # 操作履歴
│   └── demos/                 # 参考実装
│
├── docs/                      # ドキュメント（提出用）
│   ├── USER_MANUAL.md
│   ├── ER_DIAGRAM.md
│   ├── TEST_ACCOUNTS.md
│   └── PRESENTATION.md
│
├── docs-private/              # ドキュメント（開発用）
│   ├── 要件定義書.md
│   ├── 機能仕様書.md
│   ├── データモデル設計書.md
│   ├── システムアーキテクチャ設計書.md
│   └── テスト計画書.md
│
├── static/                    # 静的ファイル
│   ├── css/
│   ├── js/
│   └── images/
│
├── media/                     # アップロードファイル
│
├── pyproject.toml             # 依存関係定義（唯一の情報源）
├── uv.lock                    # 依存関係固定
├── docker-compose.local.yml   # 開発環境Docker設定
├── Dockerfile                 # Dockerイメージ定義
├── manage.py                  # Django管理コマンド
└── README.md                  # プロジェクト説明
```

### 4.2 diary アプリの詳細

```
diary/
├── models.py                  # データモデル
│   ├── DiaryEntry            # 連絡帳エントリー
│   ├── ClassRoom             # クラス情報
│   └── TeacherNote           # 教師メモ
│
├── views.py                   # ビューロジック
│   ├── StudentDashboardView  # 生徒ダッシュボード
│   ├── DiaryCreateView       # 連絡帳作成
│   ├── DiaryListView         # 過去記録一覧
│   ├── TeacherDashboardView  # 担任ダッシュボード
│   ├── SubmissionListView    # 提出状況一覧
│   └── DiaryDetailView       # 連絡帳詳細
│
├── forms.py                   # フォーム定義
│   ├── DiaryEntryForm        # 連絡帳作成フォーム
│   └── TeacherNoteForm       # 教師メモフォーム
│
├── admin.py                   # Admin設定
│   ├── DiaryEntryAdmin       # 連絡帳Admin
│   ├── ClassRoomAdmin        # クラスAdmin
│   └── TeacherNoteAdmin      # 教師メモAdmin
│
└── templates/diary/
    ├── base.html             # ベーステンプレート
    ├── student/              # 生徒用テンプレート
    │   ├── dashboard.html
    │   ├── entry_create.html
    │   ├── entry_list.html
    │   └── entry_detail.html
    └── teacher/              # 担任用テンプレート
        ├── dashboard.html
        ├── submission_list.html
        ├── entry_detail.html
        └── timeline.html
```

---

## 5. デプロイ戦略

### 5.1 開発環境

#### Docker Compose構成

```yaml
services:
  postgres:
    image: postgres:16
    ports:
      - "5432:5432"
    environment:
      POSTGRES_DB: school_diary
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:latest
    ports:
      - "6379:6379"

  django:
    build: .
    command: python manage.py runserver 0.0.0.0:8000
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
    volumes:
      - .:/app
    environment:
      DATABASE_URL: postgresql://postgres:postgres@postgres:5432/school_diary
      REDIS_URL: redis://redis:6379/0
      DEBUG: "True"

  celery:
    build: .
    command: celery -A school_diary worker -l info
    depends_on:
      - postgres
      - redis
    environment:
      DATABASE_URL: postgresql://postgres:postgres@postgres:5432/school_diary
      REDIS_URL: redis://redis:6379/0
```

#### 起動手順

```bash
# 1. コンテナ起動
docker compose -f docker-compose.local.yml up -d

# 2. マイグレーション
docker compose -f docker-compose.local.yml run --rm django python manage.py migrate

# 3. テストデータ作成
docker compose -f docker-compose.local.yml run --rm django python manage.py setup_dev

# 4. アクセス
# http://localhost:8000
```

### 5.2 本番環境（推奨: Render.com）

#### Render.com 構成

| サービス | タイプ | 料金 |
|---------|--------|------|
| **Web Service** | Django (Gunicorn) | Free / $7/月 |
| **PostgreSQL** | Managed Database | Free / $7/月 |
| **Redis** | Upstash Redis | Free |

#### デプロイ手順

1. **リポジトリ準備**
```bash
# Render用の設定ファイルを追加
# render.yaml を作成
services:
  - type: web
    name: school-diary
    env: python
    buildCommand: "pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate"
    startCommand: "gunicorn school_diary.wsgi:application"
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: school-diary-db
          property: connectionString
      - key: SECRET_KEY
        generateValue: true
      - key: DEBUG
        value: "False"
      - key: ALLOWED_HOSTS
        value: ".onrender.com"

databases:
  - name: school-diary-db
    plan: free
```

2. **Renderダッシュボードで設定**
   - GitLabリポジトリを接続
   - Web Service作成
   - PostgreSQL作成
   - 環境変数設定

3. **初回デプロイ**
   - 自動ビルド・デプロイ
   - マイグレーション自動実行
   - テストアカウント作成（管理コマンド）

#### 環境変数

| 変数名 | 説明 | 例 |
|-------|------|---|
| DATABASE_URL | PostgreSQL接続URL | postgresql://user:pass@host:5432/db |
| SECRET_KEY | Django秘密鍵 | ランダム文字列（50文字以上） |
| DEBUG | デバッグモード | False（本番環境） |
| ALLOWED_HOSTS | 許可ホスト | .onrender.com, school-diary.onrender.com |
| REDIS_URL | Redis接続URL | redis://default:pass@host:6379/0 |

### 5.3 代替案: Railway.app

同様の手順でデプロイ可能。

**メリット**:
- より簡単な設定
- GitHub/GitLab統合

**デメリット**:
- 無料枠がRenderより小さい

---

## 6. セキュリティ

### 6.1 認証・認可

| 項目 | 実装方法 |
|-----|---------|
| **認証** | Django標準のユーザー認証 |
| **パスワード** | PBKDF2ハッシュ化（Django標準） |
| **セッション** | Cookie + データベースセッション |
| **ロール管理** | User.is_staff, User.is_superuser |

### 6.2 CSRF対策

Django標準のCSRF保護を使用：
```python
# settings.py
MIDDLEWARE = [
    'django.middleware.csrf.CsrfViewMiddleware',
]

# テンプレート
<form method="post">
  {% csrf_token %}
  ...
</form>
```

### 6.3 XSS対策

Django Templatesの自動エスケープ：
```python
# 自動エスケープ
{{ user_input }}  # <script>タグもエスケープ

# 明示的にエスケープ解除する場合（注意）
{{ content|safe }}
```

### 6.4 SQLインジェクション対策

Django ORMのパラメータ化クエリ：
```python
# 安全（ORMがエスケープ）
DiaryEntry.objects.filter(student__username=username)

# 危険（使用禁止）
DiaryEntry.objects.raw(f"SELECT * FROM diary_entry WHERE student_id = {user_id}")
```

### 6.5 権限チェック

Viewレベルでの権限制御：
```python
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin

@login_required
def student_dashboard(request):
    # ログインユーザーのみアクセス可能
    pass

class TeacherDashboardView(LoginRequiredMixin):
    # ログイン必須
    def get_queryset(self):
        # 担任のみ
        if not self.request.user.is_staff:
            raise PermissionDenied
        return ...
```

### 6.6 HTTPS強制（本番環境）

```python
# settings.py（本番環境）
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

---

## 7. パフォーマンス

### 7.1 データベースクエリ最適化

#### N+1問題の回避

```python
# 悪い例（N+1問題）
entries = DiaryEntry.objects.all()
for entry in entries:
    print(entry.student.get_full_name())  # 毎回SQL実行

# 良い例（JOINを使用）
entries = DiaryEntry.objects.select_related('student').all()
for entry in entries:
    print(entry.student.get_full_name())  # 1回のクエリ
```

#### インデックスの活用

```python
# models.py
class DiaryEntry(models.Model):
    entry_date = models.DateField()
    is_read = models.BooleanField()

    class Meta:
        indexes = [
            models.Index(fields=['entry_date']),  # 日付検索高速化
            models.Index(fields=['is_read']),     # 未読検索高速化
        ]
```

### 7.2 静的ファイル配信

#### 開発環境

Django標準の`staticfiles`アプリ：
```python
# settings.py
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
```

#### 本番環境

Whitenoise使用：
```python
# settings.py
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # ← 追加
    ...
]

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

### 7.3 キャッシュ戦略（将来の拡張）

```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# views.py
from django.views.decorators.cache import cache_page

@cache_page(60 * 15)  # 15分キャッシュ
def classroom_statistics(request):
    # 統計情報の計算
    pass
```

### 7.4 ページネーション

```python
# views.py
from django.core.paginator import Paginator

def diary_list(request):
    entries = DiaryEntry.objects.filter(student=request.user)
    paginator = Paginator(entries, 20)  # 20件/ページ

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'diary/entry_list.html', {'page_obj': page_obj})
```

---

## 8. 監視・ログ

### 8.1 ログ設定

```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'django.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

### 8.2 エラー通知（本番環境）

```python
# settings.py
ADMINS = [('Admin', 'admin@example.com')]
SERVER_EMAIL = 'server@example.com'

# エラー発生時にメール通知
```

---

## 9. 関連ドキュメント

| ドキュメント | ファイルパス |
|------------|-------------|
| 要件定義書 | `docs-private/要件定義書.md` |
| データモデル設計書 | `docs-private/データモデル設計書.md` |
| 機能仕様書 | `docs-private/機能仕様書.md` |
| テスト計画書 | `docs-private/テスト計画書.md` |

---

## 10. 変更履歴

| バージョン | 日付 | 変更内容 | 作成者 |
|-----------|------|---------|--------|
| 1.0.0 | 2025-10-07 | 初版作成 | AI + hirok |

---

**作成者**: AI (Claude Code) + hirok
**最終更新**: 2025-10-07
