from django.contrib import admin
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import path
from django_fsm import TransitionNotAllowed

from .models import DemoRequest


@admin.register(DemoRequest)
class DemoRequestAdmin(admin.ModelAdmin):
    # --- 1. 表示設定 ---
    list_display = (
        "title",
        "status",
        "requester",
        "approver",
        "created_by",
        "created_at",
    )
    list_filter = ("status", "created_at")
    search_fields = ("title", "description")
    readonly_fields = (
        "status",
        "created_at",
        "updated_at",
    )  # statusもreadonlyが望ましい
    fieldsets = (
        (None, {"fields": ("title", "description", "status", "created_by")}),
        ("Participants", {"fields": ("requester", "approver")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    # --- 2. カスタムテンプレートの指定 ---
    change_form_template = "admin/demos/demorequest/change_form.html"

    # --- 3. カスタムURLの追加 ---
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<path:object_id>/submit/",
                self.admin_site.admin_view(self.submit_view),
                name="demorequest-submit",
            ),
            path(
                "<path:object_id>/approve/",
                self.admin_site.admin_view(self.approve_view),
                name="demorequest-approve",
            ),
            path(
                "<path:object_id>/deny/",
                self.admin_site.admin_view(self.deny_view),
                name="demorequest-deny",
            ),
            path(
                "<path:object_id>/return_to_draft/",
                self.admin_site.admin_view(self.return_to_draft_view),
                name="demorequest-return-to-draft",
            ),
        ]
        return custom_urls + urls

    # --- 4. テンプレートに渡す動的データの準備 ---
    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        obj = self.get_object(request, object_id)
        if obj:
            transitions = obj.get_available_status_transitions()
            # django-fsmのTransitionオブジェクトから遷移情報を取得
            extra_context["available_transitions"] = [  # type: ignore[index]
                {
                    "name": t.name,
                    "verbose": (
                        t.method.__doc__.split("(")[0].strip() if t.method.__doc__ else t.name.replace("_", " ").title()
                    ),
                }
                for t in transitions
            ]
        return super().change_view(request, object_id, form_url, extra_context)

    # --- 5. ボタンに対応する処理(ビュー)の実装 ---
    def _handle_transition(self, request, object_id, transition_name):
        obj = self.get_object(request, object_id)
        if not obj:
            self.message_user(
                request,
                "対象のオブジェクトが見つかりませんでした。",
                messages.ERROR,
            )
            return HttpResponseRedirect("../../")
        try:
            transition_method = getattr(obj, transition_name)
            transition_method(by=request.user)
            obj.save()
            self.message_user(
                request,
                f"'{obj.title}' の状態を更新しました。",
                messages.SUCCESS,
            )
        except TransitionNotAllowed:
            self.message_user(
                request,
                "現在の状態からは許可されていない操作です。",
                messages.ERROR,
            )
        except Exception as e:
            self.message_user(
                request,
                f"予期しないエラーが発生しました: {e}",
                messages.ERROR,
            )
        return HttpResponseRedirect("../")

    def submit_view(self, request, object_id):
        return self._handle_transition(request, object_id, "submit")

    def approve_view(self, request, object_id):
        return self._handle_transition(request, object_id, "approve")

    def deny_view(self, request, object_id):
        return self._handle_transition(request, object_id, "deny")

    def return_to_draft_view(self, request, object_id):
        return self._handle_transition(request, object_id, "return_to_draft")
