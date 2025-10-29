#!/usr/bin/env bash

# 連絡帳管理システム - 自動セットアップスクリプト
# 開発環境を自動構築します

set -e  # エラー時に即座に停止

# 色の定義
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# ログ出力用の関数
log_ok() {
    echo -e "${GREEN}✓${NC} $1"
}

log_error() {
    echo -e "${RED}エラー:${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}注意:${NC} $1"
}

# ヘッダー表示
echo "================================================"
echo "  連絡帳管理システム - 環境構築"
echo "================================================"
echo ""

# ステップ1: 前提条件チェック
echo "[1/6] 前提条件チェック"
if ! command -v docker &> /dev/null; then
    log_error "Docker がインストールされていません"
    echo "  インストール方法: https://docs.docker.com/get-docker/"
    exit 1
fi
log_ok "Docker インストール済み ($(docker --version))"

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    log_error "Docker Compose がインストールされていません"
    echo "  インストール方法: https://docs.docker.com/compose/install/"
    exit 1
fi
log_ok "Docker Compose インストール済み"
echo ""

# ポート番号の設定（環境変数 or デフォルト値）
DJANGO_PORT=${DJANGO_PORT:-8000}
MAILPIT_PORT=${MAILPIT_PORT:-8025}

# ポート競合チェック関数
check_port() {
    local port=$1
    local service=$2
    # curlで接続確認（タイムアウト1秒、WSL2環境でも動作）
    if curl -s --max-time 1 http://localhost:$port > /dev/null 2>&1; then
        log_error "ポート ${port} (${service}) は既に使用中です"
        echo ""
        echo "【解決方法】"
        echo "  方法1: 使用中のコンテナを停止"
        echo "    docker ps | grep ${port}"
        echo "    docker stop <コンテナID>"
        echo ""
        echo "  方法2: 別のポートを使用（推奨）"
        echo "    export DJANGO_PORT=8100"
        echo "    export MAILPIT_PORT=8125"
        echo "    ./setup.sh"
        echo ""
        echo "詳細: doc/DEPLOYMENT.md の「トラブルシューティング」を参照"
        return 1
    fi
    return 0
}

# ポート使用状況チェック
if ! check_port $DJANGO_PORT "Django"; then
    exit 1
fi
if ! check_port $MAILPIT_PORT "Mailpit"; then
    exit 1
fi

# ステップ2: 環境変数ファイル生成
echo "[2/6] 環境変数ファイル生成"
if [ -d ".envs/.local" ]; then
    log_warn "環境変数ファイルは既に存在します（スキップ）"
else
    mkdir -p .envs/.local
    cp .envs.example/.local/.django .envs/.local/.django
    cp .envs.example/.local/.postgres .envs/.local/.postgres
    log_ok "環境変数ファイル生成完了"
fi
echo ""

# ステップ3: Dockerコンテナ起動
echo "[3/6] Dockerコンテナ起動"
echo "コンテナをビルド・起動中... (初回は数分かかります)"
docker compose -f docker-compose.local.yml up -d --build
log_ok "コンテナ起動完了"
echo ""

# ステップ4: PostgreSQL起動待機
echo "[4/6] データベース起動待機"
echo "PostgreSQLの起動を待っています..."
sleep 5
for i in {1..30}; do
    if docker compose -f docker-compose.local.yml exec -T postgres pg_isready -U debug > /dev/null 2>&1; then
        log_ok "PostgreSQL起動完了"
        break
    fi
    if [ $i -eq 30 ]; then
        log_error "PostgreSQLが起動しませんでした"
        echo "  ログ確認: docker compose -f docker-compose.local.yml logs postgres"
        exit 1
    fi
    sleep 2
done
echo ""

# ステップ5: データベース初期化
echo "[5/6] データベース初期化"
docker compose -f docker-compose.local.yml run --rm django python manage.py migrate
log_ok "マイグレーション完了"
echo ""

# ステップ6: テストデータ投入
echo "[6/6] テストデータ投入"
docker compose -f docker-compose.local.yml run --rm django python manage.py load_production_test_data --clear
log_ok "テストデータ投入完了"
echo ""

# 完了メッセージ
echo "================================================"
echo "セットアップ完了"
echo "================================================"
echo ""
echo "アクセスURL:"
echo "  開発サーバー: http://localhost:${DJANGO_PORT}"
echo "  管理画面: http://localhost:${DJANGO_PORT}/admin"
echo "  メール確認: http://localhost:${MAILPIT_PORT}"
echo ""
echo "テストアカウント:"
echo "  管理者: admin@example.com / password123"
echo "  担任: teacher_1_a@example.com / password123"
echo "  生徒: student_1_a_01@example.com / password123"
echo ""
echo "次のステップ:"
echo "  1. ブラウザで http://localhost:${DJANGO_PORT} にアクセス"
echo "  2. 検証スクリプト実行: ./verify.sh"
echo "  3. 詳しい使い方: SETUP.md を参照"
echo ""
echo "停止方法:"
echo "  docker compose -f docker-compose.local.yml down"
echo ""
