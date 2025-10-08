"""
kits.approvals使用例。

承認フローシステムの具体的な使い方を示します。
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from kits.approvals.models import ApprovalRequest
from kits.approvals.models import ApprovalWorkflow
from kits.approvals.services import ApprovalService

User = get_user_model()


def example_1_create_2step_workflow():
    """
    例1: 2段階承認ワークフローの作成。

    課長承認 → 部長承認の2段階承認フローを作成します。
    """
    # グループ（ロール）の作成
    manager_group, _ = Group.objects.get_or_create(name="Manager")  # 課長
    director_group, _ = Group.objects.get_or_create(name="Director")  # 部長

    # ワークフローの作成
    workflow = ApprovalWorkflow.objects.create(
        name="2段階承認（課長→部長）",
        description="課長による一次承認、部長による最終承認の2段階承認フロー",
        is_active=True,
        default_deadline_hours=48,  # デフォルト期限: 48時間
    )

    # ステップ1: 課長承認
    workflow.steps.create(
        order=1,
        name="課長承認",
        description="課長による一次承認",
        approver_role=manager_group,
        is_parallel=False,
        required_approvals=1,
    )

    # ステップ2: 部長承認
    workflow.steps.create(
        order=2,
        name="部長承認",
        description="部長による最終承認",
        approver_role=director_group,
        is_parallel=False,
        required_approvals=1,
    )

    print(f"✓ Created workflow: {workflow.name}")
    print(f"  Steps: {workflow.steps.count()}")

    return workflow


def example_2_create_parallel_approval_workflow():
    """
    例2: 並列承認ワークフローの作成。

    3人の承認者のうち2人の承認が必要なワークフローを作成します。
    """
    # グループの作成
    reviewer_group, _ = Group.objects.get_or_create(name="Reviewer")  # レビュアー

    # ワークフローの作成
    workflow = ApprovalWorkflow.objects.create(
        name="並列承認（3人中2人）",
        description="3人のレビュアーのうち2人の承認が必要なフロー",
        is_active=True,
        default_deadline_hours=72,
    )

    # 並列承認ステップ
    workflow.steps.create(
        order=1,
        name="レビュアー承認",
        description="3人のレビュアーのうち2人の承認が必要",
        approver_role=reviewer_group,
        is_parallel=True,  # 並列承認
        required_approvals=2,  # 2人の承認が必要
    )

    print(f"✓ Created workflow: {workflow.name}")
    print(f"  Parallel approval: {workflow.steps.first().required_approvals} of 3")

    return workflow


def example_3_submit_and_approve_request(workflow, content_object, requester, approver):
    """
    例3: 承認依頼の提出と承認。

    Args:
        workflow: 使用する承認ワークフロー
        content_object: 承認対象のオブジェクト（例: DemoRequest）
        requester: 申請者
        approver: 承認者

    Returns:
        ApprovalRequest: 承認依頼
    """
    service = ApprovalService()

    # 承認依頼を作成
    request = service.create_request(
        workflow=workflow,
        content_object=content_object,
        requester=requester,
        metadata={"priority": "high", "category": "urgent"},
    )
    print(f"✓ Created request: {request.id}")

    # 承認依頼を提出
    request = service.submit_request(request)
    print(f"✓ Submitted request: {request.id}")
    print(f"  Status: {request.status}")
    print(f"  Current step: {request.current_step}")

    # 第1ステップを承認
    if request.current_step:
        request = service.approve_step(
            request=request,
            step=request.current_step,
            approver=approver,
            comment="内容を確認しました。承認します。",
        )
        print(f"✓ Approved step 1")
        print(f"  Status: {request.status}")
        print(f"  Current step: {request.current_step}")

    return request


def example_4_reject_request(workflow, content_object, requester, approver):
    """
    例4: 承認依頼の否認。

    Args:
        workflow: 使用する承認ワークフロー
        content_object: 承認対象のオブジェクト
        requester: 申請者
        approver: 承認者（否認する人）

    Returns:
        ApprovalRequest: 否認された承認依頼
    """
    service = ApprovalService()

    # 承認依頼を作成・提出
    request = service.create_request(
        workflow=workflow,
        content_object=content_object,
        requester=requester,
    )
    request = service.submit_request(request)
    print(f"✓ Created and submitted request: {request.id}")

    # 第1ステップを否認
    if request.current_step:
        request = service.reject_step(
            request=request,
            step=request.current_step,
            approver=approver,
            comment="要件を満たしていないため、否認します。",
        )
        print(f"✓ Rejected request")
        print(f"  Status: {request.status}")
        print(f"  Completed at: {request.completed_at}")

    return request


def example_5_return_to_requester(workflow, content_object, requester, approver):
    """
    例5: 承認依頼の差戻し。

    Args:
        workflow: 使用する承認ワークフロー
        content_object: 承認対象のオブジェクト
        requester: 申請者
        approver: 承認者（差戻す人）

    Returns:
        ApprovalRequest: 差戻された承認依頼
    """
    service = ApprovalService()

    # 承認依頼を作成・提出
    request = service.create_request(
        workflow=workflow,
        content_object=content_object,
        requester=requester,
    )
    request = service.submit_request(request)
    print(f"✓ Created and submitted request: {request.id}")

    # 第1ステップを差戻し
    if request.current_step:
        request = service.return_to_requester(
            request=request,
            step=request.current_step,
            approver=approver,
            comment="記載内容に不足があるため、修正して再提出してください。",
        )
        print(f"✓ Returned to requester")
        print(f"  Status: {request.status}")
        print(f"  Current step: {request.current_step}")

    return request


def example_6_get_pending_requests_for_user(user):
    """
    例6: ユーザーが承認可能な保留中のリクエスト取得。

    Args:
        user: ユーザー

    Returns:
        QuerySet: 承認可能な承認依頼
    """
    service = ApprovalService()

    pending_requests = service.get_pending_requests_for_user(user)

    print(f"✓ Pending requests for {user.username}:")
    for request in pending_requests:
        print(f"  - Request #{request.id}: {request.workflow.name}")
        print(f"    Current step: {request.current_step}")
        print(f"    Requester: {request.requester}")
        print(f"    Deadline: {request.deadline}")

    return pending_requests


def example_7_check_overdue_requests():
    """
    例7: 期限切れのリクエストをチェック。

    Returns:
        QuerySet: 期限切れの承認依頼
    """
    service = ApprovalService()

    overdue_requests = service.get_overdue_requests()

    print(f"✓ Overdue requests: {overdue_requests.count()}")
    for request in overdue_requests:
        print(f"  - Request #{request.id}: {request.workflow.name}")
        print(f"    Deadline: {request.deadline}")
        print(f"    Current step: {request.current_step}")

    return overdue_requests


def example_8_auto_approve_workflow():
    """
    例8: 自動承認機能付きワークフローの作成。

    申請者が承認者ロールに属している場合、自動的に承認されるワークフローを作成します。
    """
    # グループの作成
    manager_group, _ = Group.objects.get_or_create(name="Manager")

    # ワークフローの作成
    workflow = ApprovalWorkflow.objects.create(
        name="自動承認付き承認フロー",
        description="申請者が課長の場合、自動的に課長承認ステップを通過",
        is_active=True,
        default_deadline_hours=48,
    )

    # 自動承認ステップ
    workflow.steps.create(
        order=1,
        name="課長承認",
        description="課長による承認（申請者が課長の場合は自動承認）",
        approver_role=manager_group,
        is_parallel=False,
        required_approvals=1,
        auto_approve_if_requester_in_role=True,  # 自動承認を有効化
    )

    print(f"✓ Created workflow: {workflow.name}")
    print(f"  Auto-approve enabled: {workflow.steps.first().auto_approve_if_requester_in_role}")

    return workflow


# 実行例
if __name__ == "__main__":
    print("=" * 60)
    print("kits.approvals 使用例")
    print("=" * 60)

    # 例1: 2段階承認ワークフローの作成
    print("\n[例1] 2段階承認ワークフローの作成")
    print("-" * 60)
    workflow_2step = example_1_create_2step_workflow()

    # 例2: 並列承認ワークフローの作成
    print("\n[例2] 並列承認ワークフローの作成")
    print("-" * 60)
    workflow_parallel = example_2_create_parallel_approval_workflow()

    # 例8: 自動承認ワークフローの作成
    print("\n[例8] 自動承認ワークフローの作成")
    print("-" * 60)
    workflow_auto = example_8_auto_approve_workflow()

    print("\n" + "=" * 60)
    print("✓ All workflows created successfully!")
    print("=" * 60)
