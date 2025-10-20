"""
使用例

他のアプリケーションからkits.notificationsを使用する例
"""
from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model

from kits.notifications.models import NotificationTemplate
from kits.notifications.models import NotificationType
from kits.notifications.services import NotificationService
from kits.notifications.tasks import send_notification_task

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser as User
else:
    User = get_user_model()


def example_1_simple_notification():
    """例1: シンプルな通知送信"""
    # テンプレートを作成
    template, created = NotificationTemplate.objects.get_or_create(
        code="welcome_email",
        defaults={
            "name": "ウェルカムメール",
            "subject_template": "{{ site_name }}へようこそ、{{ user.name }}様！",
            "body_template": """
# ようこそ！

{{ user.name }}様、{{ site_name }}へのご登録ありがとうございます。

## 次のステップ

1. プロフィールを設定する
2. 最初のプロジェクトを作成する
3. チームメンバーを招待する

ご不明な点がございましたら、お気軽にお問い合わせください。
            """,
            "notification_types": [NotificationType.EMAIL],
        },
    )

    # ユーザーを取得
    user = User.objects.first()
    if not user:
        print("テストユーザーが必要です。python manage.py setup_dev を実行してください。")
        return

    # 通知を作成して送信
    service = NotificationService()
    notification = service.create_from_template(
        template_code="welcome_email",
        recipient=user,
        context={
            "site_name": "school_diary",
        },
    )

    # 同期送信
    service.send_notification(notification)

    # または非同期送信
    # send_notification_task.delay(notification.id)  # type: ignore[misc]


def example_2_approval_request():
    """例2: 承認依頼通知"""
    # テンプレートを作成
    template, created = NotificationTemplate.objects.get_or_create(
        code="approval_request",
        defaults={
            "name": "承認依頼",
            "subject_template": "【要承認】{{ request_title }}",
            "body_template": """
# 承認依頼

{{ approver.name }}様

{{ requester.name }}から承認依頼が届いています。

## 申請内容

**タイトル:** {{ request_title }}

**申請日:** {{ request_date }}

**内容:**
{{ request_description }}

**承認期限:** {{ deadline }}

[承認画面を開く]({{ approval_url }})
            """,
            "notification_types": [NotificationType.EMAIL, NotificationType.IN_APP],
        },
    )

    # 承認者と申請者を取得
    users = list(User.objects.all()[:2])
    if len(users) < 2:
        print("テストユーザーが2人必要です。python manage.py setup_dev を実行してください。")
        return

    approver = users[0]
    requester = users[1]

    # 通知を作成
    service = NotificationService()
    notification = service.create_from_template(
        template_code="approval_request",
        recipient=approver,
        context={
            "approver": approver,
            "requester": requester,
            "request_title": "残業申請(2025年10月分)",
            "request_date": "2025-10-04",
            "request_description": "緊急案件対応のため、10月に20時間の残業を申請します。",
            "deadline": "2025-10-07",
            "approval_url": "https://school_diary.example.com/approvals/123",
        },
        notification_type=NotificationType.IN_APP,
        priority="high",
        related_object_type="approval_request",
        related_object_id="123",
    )

    # 非同期送信
    send_notification_task.delay(notification.id)  # type: ignore[misc]


def example_3_bulk_reminder():
    """例3: 一括リマインダー送信"""
    # 返却期限が近い図書館利用者に一括通知

    # テンプレート作成
    template, created = NotificationTemplate.objects.get_or_create(
        code="library_return_reminder",
        defaults={
            "name": "返却リマインダー",
            "subject_template": "【図書館】返却期限のお知らせ",
            "body_template": """
{{ user.name }}様

以下の資料の返却期限が近づいています。

{% for book in books %}
- {{ book.title }}(返却期限: {{ book.due_date }})
{% endfor %}

期限までに返却をお願いいたします。
            """,
            "notification_types": [NotificationType.EMAIL],
        },
    )

    # 返却期限が3日以内のユーザーを取得(仮)
    user = User.objects.first()
    if not user:
        print("テストユーザーが必要です。python manage.py setup_dev を実行してください。")
        return

    due_soon_users = [
        {
            "user": user,
            "books": [
                {"title": "Djangoの教科書", "due_date": "2025-10-07"},
                {"title": "Pythonクックブック", "due_date": "2025-10-08"},
            ],
        },
        # ... 他のユーザー
    ]

    # 一括通知作成
    service = NotificationService()
    notifications = []

    for data in due_soon_users:
        user_obj: User = data["user"]
        notification = service.create_from_template(
            template_code="library_return_reminder",
            recipient=user_obj,
            context={"books": data["books"]},
        )
        notifications.append(notification)

    # バッチ送信
    result = service.send_batch(notifications)
    print(f"送信成功: {result['success']}件、失敗: {result['failed']}件")
