"""
監査証跡機能の使用例。

このモジュールは、kits.auditの主要機能の使用方法を示します。
"""


from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

from kits.audit.models import AuditMixin
from kits.audit.services import AuditService

User = get_user_model()


# ========================================
# 例1: AuditMixinを使用したモデル
# ========================================


class ExampleDocument(AuditMixin):
    """
    変更履歴を自動記録するドキュメントモデルの例。

    AuditMixinを継承することで、全ての変更が自動的に履歴に記録されます。
    """

    title = models.CharField(max_length=200)
    content = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=[
            ("draft", "下書き"),
            ("published", "公開"),
            ("archived", "アーカイブ"),
        ],
        default="draft",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "audit"  # テスト用のapp_label


def example_basic_history():
    """
    基本的な履歴記録の例。

    AuditMixinを使用したモデルの変更履歴を記録する方法を示します。
    """
    # ユーザー取得（テスト用）
    user = User.objects.first()

    # ドキュメント作成
    doc = ExampleDocument.objects.create(
        title="重要なドキュメント",
        content="これは重要な内容です。",
    )

    # 履歴情報を設定
    doc._history_user = user
    doc._change_reason = "初回作成"
    doc.save()

    # ドキュメント更新
    doc.title = "更新された重要なドキュメント"
    doc.status = "published"
    doc._history_user = user
    doc._change_reason = "タイトル変更と公開"
    doc.save()

    # 履歴を取得
    history = doc.history.all()
    for record in history:
        print(f"{record.history_date}: {record.history_change_reason}")

    return doc


# ========================================
# 例2: AuditServiceを使用したカスタムログ記録
# ========================================


def example_custom_audit_log():
    """
    カスタム監査ログの記録例。

    AuditServiceを使用して、ビジネスロジックレベルのイベントを記録します。
    """
    service = AuditService()
    user = User.objects.first()

    # ドキュメント作成
    doc = ExampleDocument.objects.create(
        title="サンプルドキュメント",
        content="サンプル内容",
    )

    # カスタムイベントを記録
    service.log_event(
        event_type="create",
        event_name="ドキュメント作成",
        obj=doc,
        user=user,
        description="新しいドキュメントが作成されました",
        metadata={
            "department": "営業部",
            "priority": "high",
        },
    )

    # ステータス変更をログ記録
    service.log_event(
        event_type="update",
        event_name="ドキュメント公開",
        obj=doc,
        user=user,
        description="ドキュメントを公開しました",
        changes={
            "status": {
                "from": "draft",
                "to": "published",
            },
        },
    )

    return doc


# ========================================
# 例3: 履歴の検索と比較
# ========================================


def example_search_and_compare():
    """
    履歴の検索と比較の例。

    特定期間のログを検索し、変更内容を比較します。
    """
    service = AuditService()

    # 過去7日間のログを検索
    start_date = timezone.now() - timezone.timedelta(days=7)
    logs = service.search_logs(
        event_type="update",
        start_date=start_date,
        limit=10,
    )

    print(f"Found {len(logs)} update events in the last 7 days")

    # ドキュメントの履歴を比較
    doc = ExampleDocument.objects.first()
    if doc:
        history = service.get_object_history(doc, limit=5)
        if len(history) >= 2:
            # 最新と1つ前のバージョンを比較
            diff = service.compare_history(
                doc,
                history[1].history_id,
                history[0].history_id,
            )
            print("Changes between versions:")
            for field, change in diff.items():
                print(f"  {field}: {change['old']} → {change['new']}")

    return logs


# ========================================
# 例4: ユーザーアクティビティの追跡
# ========================================


def example_user_activity():
    """
    ユーザーアクティビティの追跡例。

    特定ユーザーの最近のアクティビティを取得します。
    """
    service = AuditService()
    user = User.objects.first()

    # 過去30日間のアクティビティ
    activity = service.get_user_activity(user, days=30)

    print(f"User '{user.username}' performed {len(activity)} actions:")
    for log in activity[:10]:  # 最新10件を表示
        print(f"  - {log.created_at}: {log.event_name}")

    return activity


# ========================================
# 例5: 監査レポートの生成
# ========================================


def example_audit_report():
    """
    監査レポートの生成例。

    特定期間の監査レポートを生成します。
    """
    service = AuditService()

    # 今月のレポート
    start_date = timezone.now().replace(day=1, hour=0, minute=0, second=0)
    end_date = timezone.now()

    report = service.generate_audit_report(
        start_date=start_date,
        end_date=end_date,
    )

    print("=== Audit Report ===")
    print(f"Period: {start_date} to {end_date}")
    print(f"Total events: {report['total_events']}")
    print("\nEvents by type:")
    for event_type, count in report["event_type_counts"].items():
        print(f"  {event_type}: {count}")
    print("\nUser activity:")
    for username, count in report["user_activity"].items():
        print(f"  {username}: {count}")
    print("\nChanges by model:")
    for model_name, count in report["model_changes"].items():
        print(f"  {model_name}: {count}")

    return report


# ========================================
# 例6: django-simple-historyの直接使用
# ========================================


def example_simple_history_direct():
    """
    django-simple-historyを直接使用する例。

    低レベルAPIを使用した履歴操作を示します。
    """
    doc = ExampleDocument.objects.first()
    if not doc:
        return None

    # 全履歴を取得
    all_history = doc.history.all()

    # 特定の履歴レコードを取得
    if all_history.exists():
        latest = all_history.first()
        print(f"Latest change: {latest.history_change_reason}")
        print(f"Changed by: {latest.history_user}")
        print(f"Change date: {latest.history_date}")

        # 変更タイプを確認
        if latest.history_type == "+":
            print("Action: Created")
        elif latest.history_type == "~":
            print("Action: Updated")
        elif latest.history_type == "-":
            print("Action: Deleted")

        # 特定のフィールドの履歴を追跡
        status_history = []
        for record in all_history:
            status_history.append(
                {
                    "date": record.history_date,
                    "status": record.status,
                    "user": record.history_user,
                },
            )

        print("\nStatus history:")
        for entry in status_history:
            print(f"  {entry['date']}: {entry['status']} (by {entry['user']})")

    return all_history


# ========================================
# 使用方法（Django Shellから）
# ========================================
"""
# Django Shellで実行:

from kits.audit.examples import *

# 例1: 基本的な履歴記録
doc = example_basic_history()

# 例2: カスタムログ記録
doc = example_custom_audit_log()

# 例3: 履歴の検索と比較
logs = example_search_and_compare()

# 例4: ユーザーアクティビティ
activity = example_user_activity()

# 例5: 監査レポート
report = example_audit_report()

# 例6: django-simple-history直接使用
history = example_simple_history_direct()
"""
