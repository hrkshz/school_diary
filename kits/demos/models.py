from django.conf import settings
from django.db import models
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from django_fsm import FSMField
from django_fsm import transition
from simple_history.models import HistoricalRecords


class DemoRequest(models.Model):
    """
    承認フローのデモンストレーション用モデル。

    kits.approvalsやkits.auditなどの共通部品の動作確認に使用する。
    """

    title = models.CharField(_("Title"), max_length=200)
    description = models.TextField(_("Description"), blank=True)

    # 状態を管理するためのFSMField
    status = FSMField("ステータス", default="draft", max_length=50)

    # 最初にレコードを作成したユーザー
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_("Created by"),
        related_name="demo_requests",
    )
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated at"), auto_now=True)

    # 申請者と承認者を記録するためのフィールド
    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="requested_demos",
        verbose_name="申請者",
    )
    approver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_demos",
        verbose_name="承認者",
    )
    # 変更履歴を自動記録するためのフィールド
    history = HistoricalRecords()

    class Meta:
        verbose_name = _("サンプル申請")
        verbose_name_plural = _("サンプル申請")
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        """
        saveメソッドをオーバーライドし、新規作成時の履歴メタデータを自動設定する。

        新規作成時(self.pk が None の場合)に、以下を自動設定:
        - _history_user: created_by と同じユーザー
        - _change_reason: "新規作成"

        これにより、監査ログの完全性を保証する。
        """
        is_new = not self.pk

        if is_new:
            # history_userが明示的に設定されておらず、created_byが存在する場合
            if not hasattr(self, "_history_user") and self.created_by:
                self._history_user = self.created_by

            # change_reasonが明示的に設定されていない場合
            if not hasattr(self, "_change_reason"):
                self._change_reason = "新規作成"

        super().save(*args, **kwargs)

    # --- 状態遷移メソッド(公開API) ---

    def submit(self, by=None, reason=None):
        """
        申請する (下書き -> 申請中)

        Args:
            by: 申請を行ったユーザー(history_userとして記録される)
            reason: 変更理由(省略時は「申請されました。」)

        Raises:
            TransitionNotAllowed: 現在の状態から申請できない場合

        Example:
            >>> req.submit(by=user)
            >>> req.submit(by=user, reason="緊急対応のため")
        """
        with transaction.atomic():
            self.requester = by
            if by:
                self._history_user = by
            self._change_reason = reason if reason is not None else "申請されました。"
            self._perform_submit()
            self.save(update_fields=["requester", "status", "updated_at"])

    def approve(self, by=None, reason=None):
        """
        承認する (申請中 -> 承認済み)

        Args:
            by: 承認を行ったユーザー(history_userとして記録される)
            reason: 変更理由(省略時は「承認されました。」)

        Raises:
            TransitionNotAllowed: 現在の状態から承認できない場合

        Example:
            >>> req.approve(by=approver)
            >>> req.approve(by=approver, reason="条件を満たしているため")
        """
        with transaction.atomic():
            self.approver = by
            if by:
                self._history_user = by
            self._change_reason = reason if reason is not None else "承認されました。"
            self._perform_approve()
            self.save(update_fields=["approver", "status", "updated_at"])

    def deny(self, by=None, reason=None):
        """
        否認する (申請中 -> 否認)

        Args:
            by: 否認を行ったユーザー(history_userとして記録される)
            reason: 変更理由(省略時は「否認されました。」)

        Raises:
            TransitionNotAllowed: 現在の状態から否認できない場合

        Example:
            >>> req.deny(by=approver)
            >>> req.deny(by=approver, reason="要件を満たしていないため")
        """
        with transaction.atomic():
            self.approver = by
            if by:
                self._history_user = by
            self._change_reason = reason if reason is not None else "否認されました。"
            self._perform_deny()
            self.save(update_fields=["approver", "status", "updated_at"])

    def return_to_draft(self, by=None, reason=None):
        """
        差戻しする (申請中/承認済み -> 下書き)

        Args:
            by: 差戻しを行ったユーザー(history_userとして記録される)
            reason: 変更理由(省略時は「差戻しされました。」)

        Raises:
            TransitionNotAllowed: 現在の状態から差戻しできない場合

        Example:
            >>> req.return_to_draft(by=approver)
            >>> req.return_to_draft(by=approver, reason="修正が必要なため")
        """
        with transaction.atomic():
            if by:
                self._history_user = by
            self._change_reason = reason if reason is not None else "差戻しされました。"
            self._perform_return_to_draft()
            self.save(update_fields=["status", "updated_at"])

    # --- 状態遷移の内部実装(django-fsm用) ---

    @transition(field=status, source="draft", target="submitted")
    def _perform_submit(self):
        """内部用: django-fsmによる状態遷移の実装(draft -> submitted)"""

    @transition(field=status, source="submitted", target="approved")
    def _perform_approve(self):
        """内部用: django-fsmによる状態遷移の実装(submitted -> approved)"""

    @transition(field=status, source="submitted", target="denied")
    def _perform_deny(self):
        """内部用: django-fsmによる状態遷移の実装(submitted -> denied)"""

    @transition(field=status, source="submitted", target="draft")
    @transition(field=status, source="approved", target="draft")
    def _perform_return_to_draft(self):
        """内部用: django-fsmによる状態遷移の実装(submitted/approved -> draft)"""
