import logging

from django.db import transaction
from django.dispatch import receiver
from django_fsm.signals import post_transition

logger = logging.getLogger(__name__)


@receiver(post_transition)
def log_state_transition(sender, instance, name, source, target, **kwargs):
    """FSM状態遷移時に自動実行され、履歴レコードに遷移情報を追記する。"""
    user = kwargs.get("by") or kwargs.get("user")

    if not hasattr(instance, "history"):
        return

    try:
        transaction.on_commit(
            lambda: _update_history_record(instance, user, name, source, target),
        )
    except Exception:
        logger.exception("Failed to schedule history update for state transition")


def _update_history_record(instance, user, transition_name, source, target):
    """履歴レコードに遷移情報を追記する内部関数。"""
    try:
        # 最新の履歴レコードを取得し、期待されるステータスと一致するか確認
        latest_history = instance.history.order_by("-history_id").first()
        if not latest_history:
            return

        # 状態遷移の結果として作成された履歴レコードかどうかを確認
        # 期待されるステータスと一致しない場合は、異なる操作の履歴なのでスキップ
        if latest_history.status != target:
            logger.debug(
                "Skipping history update: expected status '%s' but found '%s'",
                target,
                latest_history.status,
            )
            return

        # 履歴レコードを直接save()すると新しい履歴が作成されてしまうため、
        # update()クエリを使って既存レコードを更新する
        update_fields = {}

        # history_userが未設定の場合のみ設定
        if user and not latest_history.history_user:
            update_fields["history_user"] = user

        # change_reasonが未設定の場合のみ設定する
        # モデル側で明示的に設定された理由を尊重し、上書きしない
        if not latest_history.history_change_reason:
            change_reason = (
                f"State transitioned via '{transition_name}' "
                f"from '{source}' to '{target}'."
            )
            update_fields["history_change_reason"] = change_reason

        # 更新する項目がある場合のみupdate()を実行
        if update_fields:
            instance.history.filter(history_id=latest_history.history_id).update(
                **update_fields,
            )
            logger.info("Successfully logged state transition for %s", instance)

    except Exception:
        logger.exception("Failed to update history record for state transition")
