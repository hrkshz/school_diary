#!/usr/bin/env bash

# 連絡帳管理システム - 環境検証スクリプト
# セットアップが正しく完了したかを検証します

# ポート番号の設定（環境変数 or デフォルト値）
DJANGO_PORT=${DJANGO_PORT:-8000}
MAILPIT_PORT=${MAILPIT_PORT:-8025}

# 色の定義
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# 検証結果カウンター
ok_count=0
ng_count=0

# ログ出力用の関数
log_ok() {
    echo -e "${GREEN}✓${NC} $1"
    ((ok_count++))
}

log_ng() {
    echo -e "${RED}✗${NC} $1"
    ((ng_count++))
}

log_info() {
    echo -e "  $1"
}

# ヘッダー表示
echo "================================================"
echo "  連絡帳管理システム - 環境検証"
echo "================================================"
echo ""

# 検証1: Dockerコンテナ起動確認
echo "[1/5] Dockerコンテナ起動確認"
if docker compose -f docker-compose.local.yml ps | grep -q "Up"; then
    running=$(docker compose -f docker-compose.local.yml ps --services --filter "status=running" | wc -l)
    log_ok "Dockerコンテナ: ${running}個のコンテナが起動中"
else
    log_ng "Dockerコンテナ: コンテナが起動していません"
    log_info "対処: ./setup.sh を実行してください"
fi
echo ""

# 検証2: PostgreSQL接続確認
echo "[2/5] データベース接続確認"
if docker compose -f docker-compose.local.yml exec -T postgres pg_isready -U debug > /dev/null 2>&1; then
    log_ok "PostgreSQL: 接続OK"
else
    log_ng "PostgreSQL: 接続失敗"
    log_info "対処: docker compose -f docker-compose.local.yml restart postgres"
fi
echo ""

# 検証3: Webサーバー応答確認
echo "[3/5] Webサーバー応答確認"
sleep 2  # Djangoの起動を待つ
if curl -s -o /dev/null -w "%{http_code}" http://localhost:${DJANGO_PORT} | grep -q "200\|302"; then
    log_ok "Webサーバー: 応答OK (http://localhost:${DJANGO_PORT})"
else
    log_ng "Webサーバー: 応答なし"
    log_info "対処: docker compose -f docker-compose.local.yml logs django"
fi
echo ""

# 検証4: テストユーザー作成確認
echo "[4/5] テストユーザー作成確認"
user_count=$(docker compose -f docker-compose.local.yml exec -T django python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); print(User.objects.count())" 2>/dev/null | tail -n 1)
if [ "$user_count" -ge 31 ]; then
    log_ok "テストユーザー: ${user_count}名作成済み"
else
    log_ng "テストユーザー: 作成されていません (現在: ${user_count}名)"
    log_info "対処: docker compose -f docker-compose.local.yml run --rm django python manage.py load_production_test_data --clear"
fi
echo ""

# 検証5: 管理画面アクセス確認
echo "[5/5] 管理画面アクセス確認"
if curl -s -o /dev/null -w "%{http_code}" http://localhost:${DJANGO_PORT}/admin/ | grep -q "200\|302"; then
    log_ok "管理画面: アクセスOK (http://localhost:${DJANGO_PORT}/admin/)"
else
    log_ng "管理画面: アクセス失敗"
    log_info "対処: docker compose -f docker-compose.local.yml logs django"
fi
echo ""

# 結果表示
echo "================================================"
if [ $ng_count -eq 0 ]; then
    echo -e "${GREEN}検証OK: すべての項目をクリアしました (${ok_count}/${ok_count})${NC}"
    echo "================================================"
    echo ""
    echo "次のステップ:"
    echo "  1. ブラウザで http://localhost:${DJANGO_PORT} にアクセス"
    echo "  2. 管理者アカウントでログイン: admin@example.com / password123"
    echo "  3. 機能を試してみてください"
else
    echo -e "${RED}検証NG: ${ng_count}個のエラーがあります (OK: ${ok_count}, NG: ${ng_count})${NC}"
    echo "================================================"
    echo ""
    echo "トラブルシューティング:"
    echo "  - SETUP.md の「トラブルシューティング」を参照"
    echo "  - ログ確認: docker compose -f docker-compose.local.yml logs"
    echo "  - 再セットアップ: docker compose -f docker-compose.local.yml down -v && ./setup.sh"
    exit 1
fi
echo ""
