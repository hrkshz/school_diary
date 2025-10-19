"""
監査証跡機能の使用例。

Note: AuditLog model has been removed.
Only AuditMixin examples remain.
"""

from django.contrib.auth import get_user_model
from django.db import models

from kits.audit.models import AuditMixin

User = get_user_model()


# ========================================
# 例: AuditMixinを使用したモデル
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

    AuditMixinを継承したモデルは、save()時に自動的に履歴が記録されます。
    django-simple-historyが提供する`history`属性で履歴にアクセスできます。
    """
    # ドキュメント作成
    doc = ExampleDocument.objects.create(
        title="Example Document",
        content="Initial content",
    )

    # 更新
    doc.title = "Updated Document"
    doc._change_reason = "タイトル変更"  # 変更理由を記録
    doc.save()

    # 履歴の取得
    history = doc.history.all()
    for record in history:
        print(f"{record.history_date}: {record.title} - {record.history_change_reason}")
