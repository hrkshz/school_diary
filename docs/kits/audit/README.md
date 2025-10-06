# kits.audit - 監査証跡システム

**バージョン**: 1.0.0
**ステータス**: ✅ 完成（2025-10-05）
**テスト**: 18/18成功
**コード品質**: Pylanceエラー0、Ruff All checks passed

---

## 📖 概要

kits.auditは、Django アプリケーションに**監査証跡（Audit Trail）**機能を提供するパッケージです。

**主な機能**:
- ✅ モデルの変更履歴を自動記録（django-simple-history）
- ✅ カスタムイベントのログ記録
- ✅ IPアドレス、User-Agent等の追加情報記録
- ✅ 強力な検索とレポート生成機能
- ✅ Django Admin統合

---

## 🚀 クイックスタート

### 1. モデルに履歴記録を追加

```python
from kits.audit.models import AuditMixin

class Product(AuditMixin):
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
```

### 2. マイグレーション実行

```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. 履歴を記録

```python
product.price = 15000
product._history_user = request.user
product._change_reason = "価格改定"
product.save()
```

**これだけで、全ての変更が記録されます！**

---

## 📚 ドキュメント

| ドキュメント | 内容 | 読了時間 |
|-------------|------|---------|
| [01_概要と目的.md](01_概要と目的.md) | 監査証跡とは？なぜ必要？ | 7分 |
| [02_設計思想.md](02_設計思想.md) | アーキテクチャと設計判断 | 10分 |
| [03_実装の全体像.md](03_実装の全体像.md) | モジュール構成と依存関係 | 8分 |
| [04_コード解説.md](04_コード解説.md) | 各クラス・関数の詳細解説 | 15分 |
| [05_使い方ガイド.md](05_使い方ガイド.md) | コピペで使えるコード例 | 10分 |
| [06_よくある質問.md](06_よくある質問.md) | トラブルシューティング | 5分 |
| [00_実装ログ.md](00_実装ログ.md) | 実装の経緯と学び | 5分 |

---

## 💡 使用例

### 基本的な使い方

```python
from kits.audit.models import AuditMixin

class OvertimeRequest(AuditMixin):
    employee = models.ForeignKey(User)
    hours = models.DecimalField(max_digits=4, decimal_places=2)
    status = models.CharField(max_length=20)

# 履歴を記録しながら保存
overtime._history_user = request.user
overtime._change_reason = "残業時間を変更"
overtime.hours = 3.5
overtime.save()
```

### カスタムイベントログ

```python
from kits.audit.services import AuditService

service = AuditService()
service.log_event(
    event_type="approve",
    event_name="残業申請承認",
    obj=overtime,
    user=manager,
    description="課長が承認しました",
    changes={"status": {"from": "pending", "to": "approved"}}
)
```

### 履歴の検索

```python
# 過去30日間のユーザーアクティビティ
activity = service.get_user_activity(user, days=30)

# 特定期間の監査レポート
report = service.generate_audit_report(
    start_date=datetime(2025, 1, 1),
    end_date=datetime(2025, 1, 31)
)
```

---

## 🏗️ アーキテクチャ

### コンポーネント構成

```
kits/audit/
├── models.py          # AuditMixin, AuditLogモデル
├── services.py        # AuditService（検索、レポート生成）
├── admin.py           # Django Admin統合
├── tasks.py           # Celeryタスク（クリーンアップ等）
├── signals.py         # 自動ログ記録（オプション）
└── examples.py        # 使用例
```

### 主要クラス

| クラス | 役割 |
|-------|------|
| `AuditMixin` | モデルに履歴記録機能を追加するMixin |
| `AuditLog` | カスタムイベントログのモデル |
| `AuditService` | 履歴検索、レポート生成などのサービス層 |

---

## 📊 実装状況

### コード統計

| 項目 | 行数 |
|------|------|
| models.py | 161行 |
| services.py | 321行 |
| admin.py | 190行 |
| tasks.py | 288行 |
| examples.py | 379行 |
| signals.py | 117行 |
| **合計** | **1,456行** |

### テスト

- **test_models.py**: 7個のテスト
- **test_services.py**: 11個のテスト
- **合計**: 18個のテスト、全て成功 ✅

### コード品質

- ✅ Pylanceエラー: 0件
- ✅ Ruff: All checks passed
- ✅ 型ヒント: 完備
- ✅ ドキュメント文字列: 完備

---

## 🔗 関連kits

| kit | 関連 |
|-----|------|
| **kits.approvals** | 承認フローと監査証跡を組み合わせて使用 |
| **kits.notifications** | 定期レポートをメール送信（今後対応） |

---

## ⚙️ 設定

### Django設定（必須）

```python
# config/settings/base.py

INSTALLED_APPS = [
    # ...
    'simple_history',  # django-simple-history
    'kits.audit',
]

MIDDLEWARE = [
    # ...
    'simple_history.middleware.HistoryRequestMiddleware',
]
```

### Celeryタスク（オプション）

```python
# 古いログの自動削除
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'cleanup-old-audit-logs': {
        'task': 'kits.audit.tasks.cleanup_old_audit_logs',
        'schedule': crontab(hour=2, minute=0),
        'kwargs': {'days': 365}
    },
}
```

---

## 🎯 過去課題での使用例

| 課題 | 使用箇所 |
|------|---------|
| **課題1（残業管理）** | 承認後のデータ改ざん防止、監査ログ |
| **課題2（母子手帳）** | 健康記録の変更履歴追跡 |
| **課題3（野球部）** | 測定記録の変更履歴 |
| **課題4（図書館）** | 貸出履歴、予約履歴 |

**全課題で必須の機能です。**

---

## 📝 ライセンス

MIT License

---

## 👥 開発者

- 初期実装: Claude Code
- メンテナー: school_diaryプロジェクトチーム

---

**最終更新**: 2025-10-05
