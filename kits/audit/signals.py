"""
Audit trail signals.

自動的に監査ログを記録するためのシグナルハンドラー。
"""

import logging

logger = logging.getLogger(__name__)


def get_field_changes(instance, old_instance=None):
    """
    モデルインスタンスのフィールド変更を検出する。

    Args:
        instance: 新しいインスタンス
        old_instance: 古いインスタンス（更新時のみ）

    Returns:
        dict: 変更されたフィールドの辞書
    """
    if not old_instance:
        return {}

    changes = {}
    for field in instance._meta.fields:
        field_name = field.name
        old_value = getattr(old_instance, field_name, None)
        new_value = getattr(instance, field_name, None)

        if old_value != new_value:
            changes[field_name] = {
                "old": str(old_value) if old_value is not None else None,
                "new": str(new_value) if new_value is not None else None,
            }

    return changes


# Note: これらのシグナルはプロジェクトの設定で有効化/無効化できるようにすることを推奨
# 現在はコメントアウトしており、必要に応じて有効化する

# @receiver(post_save)
# def auto_log_create_update(sender, instance, created, **kwargs):
#     """
#     モデルの作成・更新時に自動的にログを記録する。
#
#     Note:
#         この機能はパフォーマンスへの影響があるため、
#         設定で有効化した場合のみ動作するようにすることを推奨。
#     """
#     # AuditLog自身のログは記録しない
#     if isinstance(instance, AuditLog):
#         return
#
#     # 履歴管理を持つモデルのみ処理
#     if not hasattr(instance, 'history'):
#         return
#
#     event_type = "create" if created else "update"
#     event_name = f"{instance._meta.verbose_name} {'作成' if created else '更新'}"
#
#     # 変更内容の取得（更新時のみ）
#     changes = {}
#     if not created:
#         try:
#             old_instance = sender.objects.get(pk=instance.pk)
#             changes = get_field_changes(instance, old_instance)
#         except sender.DoesNotExist:
#             pass
#
#     # ログ記録
#     AuditLog.objects.create(
#         event_type=event_type,
#         event_name=event_name,
#         model_name=instance._meta.model_name,
#         object_id=str(instance.pk),
#         object_repr=str(instance),
#         changes=changes,
#     )
#
#     logger.debug(
#         "Auto-logged %s for %s (id=%s)",
#         event_type,
#         instance._meta.model_name,
#         instance.pk
#     )


# @receiver(post_delete)
# def auto_log_delete(sender, instance, **kwargs):
#     """
#     モデルの削除時に自動的にログを記録する。
#     """
#     # AuditLog自身のログは記録しない
#     if isinstance(instance, AuditLog):
#         return
#
#     # 履歴管理を持つモデルのみ処理
#     if not hasattr(instance, 'history'):
#         return
#
#     AuditLog.objects.create(
#         event_type="delete",
#         event_name=f"{instance._meta.verbose_name} 削除",
#         model_name=instance._meta.model_name,
#         object_id=str(instance.pk),
#         object_repr=str(instance),
#     )
#
#     logger.debug(
#         "Auto-logged delete for %s (id=%s)",
#         instance._meta.model_name,
#         instance.pk
#     )
