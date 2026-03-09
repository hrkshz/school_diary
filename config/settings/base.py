"""Base settings to build other settings files upon."""

from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve(strict=True).parent.parent.parent
# school_diary/
APPS_DIR = BASE_DIR / "school_diary"
env = environ.Env()

READ_DOT_ENV_FILE: bool = env.bool("DJANGO_READ_DOT_ENV_FILE", default=False)  # type: ignore[arg-type]
if READ_DOT_ENV_FILE:
    # OS environment variables take precedence over variables from .env
    env.read_env(str(BASE_DIR / ".env"))

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG: bool = env.bool("DJANGO_DEBUG", default=False)  # type: ignore[arg-type]
# Site URL（メール送信時のログインURL生成に使用）
SITE_URL = env.str("DJANGO_SITE_URL", default="http://localhost:8000")
# Local time zone. Choices are
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# though not all of them may be available with every OS.
# In Windows, this must be set to your system time zone.
TIME_ZONE = "Asia/Tokyo"
# https://docs.djangoproject.com/en/dev/ref/settings/#language-code
LANGUAGE_CODE = "ja"
# https://docs.djangoproject.com/en/dev/ref/settings/#site-id
SITE_ID = 1
# https://docs.djangoproject.com/en/dev/ref/settings/#use-i18n
USE_I18N = True
# https://docs.djangoproject.com/en/dev/ref/settings/#use-tz
USE_TZ = True
# https://docs.djangoproject.com/en/dev/ref/settings/#locale-paths
LOCALE_PATHS = [str(BASE_DIR / "locale")]

# DATABASES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#databases
database_url = env.str("DATABASE_URL", default="")
postgres_name = env.str("POSTGRES_DB", default="")
postgres_user = env.str("POSTGRES_USER", default="")
postgres_password = env.str("POSTGRES_PASSWORD", default="")
postgres_host = env.str("POSTGRES_HOST", default="")
postgres_port = env.str("POSTGRES_PORT", default="5432")

if database_url:
    default_database = env.db("DATABASE_URL")
elif all([postgres_name, postgres_user, postgres_password, postgres_host]):
    default_database = {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": postgres_name,
        "USER": postgres_user,
        "PASSWORD": postgres_password,
        "HOST": postgres_host,
        "PORT": postgres_port,
    }
else:
    # Build and test settings can import base.py without production DB env vars.
    default_database = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": str(BASE_DIR / "db.sqlite3"),
    }

DATABASES = {"default": default_database}
DATABASES["default"]["ATOMIC_REQUESTS"] = True
# https://docs.djangoproject.com/en/stable/ref/settings/#std:setting-DEFAULT_AUTO_FIELD
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# URLS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#root-urlconf
ROOT_URLCONF = "config.urls"
# https://docs.djangoproject.com/en/dev/ref/settings/#wsgi-application
WSGI_APPLICATION = "config.wsgi.application"

# APPS
# ------------------------------------------------------------------------------
DJANGO_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # "django.contrib.humanize", # Handy template tags
    "django.contrib.admin",
    "django.forms",
]
THIRD_PARTY_APPS = [
    "crispy_forms",
    "crispy_bootstrap5",
    "allauth",
    "allauth.account",
    "allauth.mfa",
    "allauth.socialaccount",
    "rest_framework",
    "anymail",
    "simple_history",
]

LOCAL_APPS = [
    # Your stuff: custom apps go here
    "school_diary.diary.apps.DiaryConfig",
]
# https://docs.djangoproject.com/en/dev/ref/settings/#installed-apps
INSTALLED_APPS = ["jazzmin", *DJANGO_APPS, *THIRD_PARTY_APPS, *LOCAL_APPS]

# MIGRATIONS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#migration-modules
MIGRATION_MODULES = {"sites": "school_diary.contrib.sites.migrations"}

# AUTHENTICATION
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#authentication-backends
AUTHENTICATION_BACKENDS = [
    "school_diary.diary.auth_backends.EmailAuthenticationBackend",
    "django.contrib.auth.backends.ModelBackend",
]
# https://docs.djangoproject.com/en/dev/ref/settings/#login-redirect-url
LOGIN_REDIRECT_URL = "/"
# https://docs.djangoproject.com/en/dev/ref/settings/#login-url
LOGIN_URL = "account_login"
# https://docs.djangoproject.com/en/dev/ref/settings/#logout-redirect-url
LOGOUT_REDIRECT_URL = "account_login"

# PASSWORDS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#password-hashers
PASSWORD_HASHERS = [
    # https://docs.djangoproject.com/en/dev/topics/auth/passwords/#using-argon2-with-django
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
]
# https://docs.djangoproject.com/en/dev/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# MIDDLEWARE
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#middleware
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "simple_history.middleware.HistoryRequestMiddleware",
    "school_diary.diary.middleware.PasswordChangeRequiredMiddleware",  # パスワード変更強制
]

# STATIC
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#static-root
STATIC_ROOT = str(BASE_DIR / "staticfiles")
# https://docs.djangoproject.com/en/dev/ref/settings/#static-url
STATIC_URL = "/static/"
# https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#std:setting-STATICFILES_DIRS
STATICFILES_DIRS = [str(APPS_DIR / "static")]
# https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#staticfiles-finders
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]

# MEDIA
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#media-root
MEDIA_ROOT = str(APPS_DIR / "media")
# https://docs.djangoproject.com/en/dev/ref/settings/#media-url
MEDIA_URL = "/media/"

# TEMPLATES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#templates
TEMPLATES = [
    {
        # https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-TEMPLATES-BACKEND
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # https://docs.djangoproject.com/en/dev/ref/settings/#dirs
        "DIRS": [str(APPS_DIR / "templates")],
        # https://docs.djangoproject.com/en/dev/ref/settings/#app-dirs
        "APP_DIRS": True,
        "OPTIONS": {
            # https://docs.djangoproject.com/en/dev/ref/settings/#template-context-processors
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# https://docs.djangoproject.com/en/dev/ref/settings/#form-renderer
FORM_RENDERER = "django.forms.renderers.TemplatesSetting"

# http://django-crispy-forms.readthedocs.io/en/latest/install.html#template-packs
CRISPY_TEMPLATE_PACK = "bootstrap5"
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"

# FIXTURES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#fixture-dirs
FIXTURE_DIRS = (str(APPS_DIR / "fixtures"),)

# SECURITY
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#session-cookie-httponly
SESSION_COOKIE_HTTPONLY = True
# https://docs.djangoproject.com/en/dev/ref/settings/#csrf-cookie-httponly
# Note: Set to False to allow JavaScript to read CSRF token for AJAX requests
CSRF_COOKIE_HTTPONLY = False
# https://docs.djangoproject.com/en/dev/ref/settings/#x-frame-options
X_FRAME_OPTIONS = "DENY"

# EMAIL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
EMAIL_BACKEND = env.str(
    "DJANGO_EMAIL_BACKEND",
    default="django.core.mail.backends.smtp.EmailBackend",  # type: ignore[arg-type]
)
# https://docs.djangoproject.com/en/dev/ref/settings/#email-timeout
EMAIL_TIMEOUT = 5
# https://docs.djangoproject.com/en/dev/ref/settings/#default-from-email
DEFAULT_FROM_EMAIL = "noreply@school_diary.local"
# https://docs.djangoproject.com/en/dev/ref/settings/#server-email
SERVER_EMAIL = "admin@school_diary.local"

# ADMIN
# ------------------------------------------------------------------------------
# Django Admin URL.
ADMIN_URL = "admin/"
# https://docs.djangoproject.com/en/dev/ref/settings/#admins
ADMINS = [("""BizApp Team""", "admin@example.com")]
# https://docs.djangoproject.com/en/dev/ref/settings/#managers
MANAGERS = ADMINS
# https://cookiecutter-django.readthedocs.io/en/latest/settings.html#other-environment-settings
# Force the `admin` sign in process to go through the `django-allauth` workflow
DJANGO_ADMIN_FORCE_ALLAUTH = env.bool("DJANGO_ADMIN_FORCE_ALLAUTH", default=False)  # type: ignore[arg-type]

# LOGGING
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#logging
# See https://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s",
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {"level": "INFO", "handlers": ["console"]},
}

# django-allauth
# ------------------------------------------------------------------------------
# https://docs.allauth.org/en/latest/account/configuration.html
ACCOUNT_ALLOW_REGISTRATION = env.bool("DJANGO_ACCOUNT_ALLOW_REGISTRATION", default=False)  # type: ignore[arg-type]
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]
ACCOUNT_EMAIL_VERIFICATION = "none"  # PoC環境のため、メール認証を無効化
ACCOUNT_ADAPTER = "school_diary.diary.adapters.RoleBasedRedirectAdapter"

# Django REST Framework
# ------------------------------------------------------------------------------
# https://www.django-rest-framework.org/api-guide/settings/
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 100,
}

# Notifications (Disabled: Celery dependency removed in Option D-Ultra)
# ------------------------------------------------------------------------------
NOTIFICATIONS_CONFIG = {
    "ENABLED": False,
    "DEFAULT_BACKEND": "email",  # email, in_app, push
    "BATCH_SIZE": 100,  # 一度に送信する通知の最大数
    "RETRY_ATTEMPTS": 3,  # 失敗時のリトライ回数
    "RETENTION_DAYS": 90,  # 通知履歴の保持期間(日)
}

# Reports
# ------------------------------------------------------------------------------
REPORTS_CONFIG = {
    "ENABLED": True,
    "OUTPUT_DIR": BASE_DIR / "media" / "reports",  # レポート保存先
    "TEMP_DIR": BASE_DIR / "media" / "reports" / "temp",  # 一時ファイル
    "RETENTION_DAYS": 30,  # レポートファイルの保持期間(日)
    "MAX_FILE_SIZE_MB": 50,  # 最大ファイルサイズ(MB)
    "ALLOWED_FORMATS": ["pdf", "csv", "xlsx"],  # 許可する形式
    "CHART_LIBRARY": "chartjs",  # chartjs または plotly
    "PDF_BACKEND": "weasyprint",  # weasyprint または reportlab
}

# WeasyPrint設定
WEASYPRINT_BASEURL = "file://" + str(BASE_DIR)

# IO
# ------------------------------------------------------------------------------
IO_CONFIG = {
    "ENABLED": True,
    "UPLOAD_DIR": BASE_DIR / "media" / "imports",  # アップロード先
    "TEMP_DIR": BASE_DIR / "media" / "imports" / "temp",  # 一時ファイル
    "MAX_FILE_SIZE_MB": 100,  # 最大ファイルサイズ（MB）
    "ALLOWED_EXTENSIONS": ["csv", "tsv", "txt", "xlsx", "xls"],
    "DEFAULT_ENCODING": "utf-8",  # デフォルト文字コード
    "AUTO_DETECT_ENCODING": True,  # 文字コード自動検出
    "CHUNK_SIZE": 1000,  # チャンク処理のサイズ（行数）
    "VALIDATION_ENABLED": True,  # バリデーション有効化
    "DUPLICATE_STRATEGY": "skip",  # skip, update, renumber, error
}

# ======================
# Jazzmin Settings
# ======================
JAZZMIN_SETTINGS = {
    # 基本情報
    "site_title": "連絡帳管理",
    "site_header": "連絡帳管理システム",
    "site_brand": "連絡帳",
    "site_logo": None,
    "welcome_sign": "ようこそ 連絡帳管理システムへ",
    "copyright": "連絡帳管理システム 2025",
    # 検索設定
    "search_model": ["auth.User", "diary.DiaryEntry"],
    # サイドバー設定
    "show_sidebar": True,
    "navigation_expanded": True,
    # メニュー順序（使用頻度と業務フローに基づく）
    "order_with_respect_to": [
        "auth",  # ユーザー・グループ
        "diary",  # 連絡帳関連
        "reports",  # レポート
        # "approvals",  # 承認フロー（未使用のため削除）
        "notifications",  # 通知
        "io",  # データ入出力
        "audit",  # 監査ログ
        "account",  # アカウント
        "socialaccount",  # 外部アカウント
        "mfa",  # 多要素認証
        "sites",  # サイト
        "demos",  # デモ・参考実装
    ],
    # アイコン設定（Font Awesome）
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "diary.DiaryEntry": "fas fa-book",
        "diary.ClassRoom": "fas fa-school",
        "diary.TeacherNote": "fas fa-sticky-note",
        "reports": "fas fa-chart-bar",
        "notifications": "fas fa-bell",
        "io": "fas fa-file-import",
        "audit": "fas fa-history",
        "account": "fas fa-user-circle",
        "mfa": "fas fa-shield-alt",
        "demos": "fas fa-flask",
    },
    # UI設定
    "show_ui_builder": False,
}
