"""
変更履歴追跡のためのモデルとヘルパー。

このモジュールはdjango-simple-historyをラップし、以下の機能を提供します:
- 自動的な変更履歴記録
- 変更理由の記録
- 変更ユーザーの記録
- 履歴の検索とフィルタリング
"""

from django.db import models
from simple_history.models import HistoricalRecords


class AuditMixin(models.Model):
    """
    変更履歴を自動記録するためのMixin。

    このMixinを継承することで、モデルに自動的に履歴記録機能が追加されます。

    Example:
        >>> class MyModel(AuditMixin):
        ...     name = models.CharField(max_length=100)
        ...
        >>> obj = MyModel.objects.create(name="Test")
        >>> obj._history_user = request.user
        >>> obj._change_reason = "Created by user"
        >>> obj.name = "Updated"
        >>> obj.save()
        >>> # 履歴が自動的に記録される
    """

    history = HistoricalRecords(inherit=True)

    class Meta:
        abstract = True
