"""Admin views - test data management."""

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.shortcuts import render

from ..models import ClassRoom
from ..models import DiaryEntry
from ..models import UserProfile

User = get_user_model()

__all__ = [
    "test_data_complete",
    "test_data_config",
    "test_data_confirm",
    "test_data_loading",
]


@login_required
def test_data_config(request):
    """テストデータ作成 - 設定画面（管理者専用）"""
    if not request.user.is_superuser:
        msg = "管理者のみがアクセス可能です"
        raise PermissionDenied(msg)

    from ..forms import TestDataConfigForm

    if request.method == "POST":
        form = TestDataConfigForm(request.POST)
        if form.is_valid():
            # セッションに設定を保存
            request.session["test_data_config"] = {
                "clean_existing": form.cleaned_data["clean_existing"],
                "diary_days": form.cleaned_data["diary_days"],
                "students_per_class": form.cleaned_data["students_per_class"],
                "include_special_patterns": form.cleaned_data["include_special_patterns"],
            }
            return redirect("diary:test_data_confirm")
    else:
        form = TestDataConfigForm()

    return render(request, "diary/admin/test_data_config.html", {"form": form})


@login_required
def test_data_confirm(request):
    """テストデータ作成 - 確認画面（管理者専用）"""
    if not request.user.is_superuser:
        msg = "管理者のみがアクセス可能です"
        raise PermissionDenied(msg)

    config = request.session.get("test_data_config")
    if not config:
        return redirect("diary:test_data_config")

    if request.method == "POST":
        # バックグラウンドでコマンド実行
        import logging
        import threading

        from django.core.management import call_command

        def run_command():
            """バックグラウンドでテストデータ生成コマンドを実行"""
            try:
                args = []
                if config["clean_existing"]:
                    args.append("--clean")
                if not config["include_special_patterns"]:
                    args.append("--no-special-patterns")

                call_command(
                    "create_test_data",
                    *args,
                    diary_days=config["diary_days"],
                    students_per_class=config["students_per_class"],
                )
            except Exception:
                logger = logging.getLogger(__name__)
                logger.exception("テストデータ作成エラー")

        thread = threading.Thread(target=run_command)
        thread.daemon = True
        thread.start()

        return redirect("diary:test_data_loading")

    # 推定データ量を計算
    estimated_students = config["students_per_class"] * 9
    estimated_diaries = int(estimated_students * config["diary_days"] * 0.8)

    context = {
        "config": config,
        "estimated_students": estimated_students,
        "estimated_diaries": estimated_diaries,
    }
    return render(request, "diary/admin/test_data_confirm.html", context)


@login_required
def test_data_loading(request):
    """テストデータ作成 - ローディング画面（管理者専用）"""
    if not request.user.is_superuser:
        msg = "管理者のみがアクセス可能です"
        raise PermissionDenied(msg)

    return render(request, "diary/admin/test_data_loading.html")


@login_required
def test_data_complete(request):
    """テストデータ作成 - 完了画面（管理者専用）"""
    if not request.user.is_superuser:
        msg = "管理者のみがアクセス可能です"
        raise PermissionDenied(msg)

    # 統計情報を取得
    admin_count = User.objects.filter(is_superuser=True).count()
    school_leader_count = User.objects.filter(profile__role=UserProfile.ROLE_SCHOOL_LEADER).count()
    grade_leader_count = User.objects.filter(profile__role=UserProfile.ROLE_GRADE_LEADER).count()
    teacher_count = User.objects.filter(profile__role=UserProfile.ROLE_TEACHER).count()
    student_count = User.objects.filter(profile__role=UserProfile.ROLE_STUDENT).count()
    classroom_count = ClassRoom.objects.count()
    diary_count = DiaryEntry.objects.count()

    stats = {
        "admin_count": admin_count,
        "school_leader_count": school_leader_count,
        "grade_leader_count": grade_leader_count,
        "teacher_count": teacher_count,
        "student_count": student_count,
        "classroom_count": classroom_count,
        "diary_count": diary_count,
    }

    # セッションをクリア
    if "test_data_config" in request.session:
        del request.session["test_data_config"]

    return render(request, "diary/admin/test_data_complete.html", {"stats": stats})
