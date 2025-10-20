"""
kits.approvals サービスのテスト。
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase

from kits.approvals.models import ApprovalAction
from kits.approvals.models import ApprovalStep
from kits.approvals.models import ApprovalWorkflow
from kits.approvals.services import ApprovalService
from kits.demos.models import DemoRequest

User = get_user_model()


class ApprovalServiceTest(TestCase):
    """ApprovalService のテスト。"""

    def setUp(self):
        self.service = ApprovalService()

        # ワークフロー作成
        self.workflow = ApprovalWorkflow.objects.create(
            name="2 Step Workflow", default_deadline_hours=48,
        )

        # グループ作成
        self.manager_group = Group.objects.create(name="Manager")
        self.director_group = Group.objects.create(name="Director")

        # ステップ作成
        self.step1 = ApprovalStep.objects.create(
            workflow=self.workflow,
            order=1,
            name="Manager Approval",
            approver_role=self.manager_group,
        )
        self.step2 = ApprovalStep.objects.create(
            workflow=self.workflow,
            order=2,
            name="Director Approval",
            approver_role=self.director_group,
        )

        # ユーザー作成
        self.requester = User.objects.create_user(
            email="requester@example.com", password="password",
        )
        self.manager = User.objects.create_user(
            email="manager@example.com", password="password",
        )
        self.manager.groups.add(self.manager_group)

        self.director = User.objects.create_user(
            email="director@example.com", password="password",
        )
        self.director.groups.add(self.director_group)

        # 承認対象
        self.demo = DemoRequest.objects.create(
            title="Test Demo", created_by=self.requester,
        )

    def test_create_request(self):
        """承認依頼を作成できる。"""
        request = self.service.create_request(
            workflow=self.workflow,
            content_object=self.demo,
            requester=self.requester,
            metadata={"priority": "high"},
        )

        self.assertEqual(request.workflow, self.workflow)
        self.assertEqual(request.content_object, self.demo)
        self.assertEqual(request.requester, self.requester)
        self.assertEqual(request.metadata["priority"], "high")
        self.assertEqual(request.status, "draft")

    def test_submit_request(self):
        """承認依頼を提出できる。"""
        request = self.service.create_request(
            workflow=self.workflow,
            content_object=self.demo,
            requester=self.requester,
        )

        request = self.service.submit_request(request)

        self.assertEqual(request.status, "pending")
        self.assertEqual(request.current_step, self.step1)
        self.assertIsNotNone(request.requested_at)
        self.assertIsNotNone(request.deadline)

    def test_approve_step(self):
        """ステップを承認できる。"""
        request = self.service.create_request(
            workflow=self.workflow,
            content_object=self.demo,
            requester=self.requester,
        )
        request = self.service.submit_request(request)

        # 第1ステップを承認
        request = self.service.approve_step(
            request=request,
            step=self.step1,
            approver=self.manager,
            comment="Approved",
        )

        self.assertEqual(request.current_step, self.step2)
        self.assertEqual(request.status, "pending")

        # アクションが記録されている
        actions = ApprovalAction.objects.filter(request=request, step=self.step1)
        self.assertEqual(actions.count(), 1)
        self.assertEqual(actions.first().action, "approve")

    def test_full_approval_flow(self):
        """完全な承認フローをテストできる。"""
        request = self.service.create_request(
            workflow=self.workflow,
            content_object=self.demo,
            requester=self.requester,
        )
        request = self.service.submit_request(request)

        # 第1ステップを承認
        request = self.service.approve_step(
            request=request, step=self.step1, approver=self.manager,
        )
        self.assertEqual(request.current_step, self.step2)

        # 第2ステップを承認
        request = self.service.approve_step(
            request=request, step=self.step2, approver=self.director,
        )

        self.assertEqual(request.status, "approved")
        self.assertIsNone(request.current_step)
        self.assertIsNotNone(request.completed_at)

    def test_reject_step(self):
        """ステップを否認できる。"""
        request = self.service.create_request(
            workflow=self.workflow,
            content_object=self.demo,
            requester=self.requester,
        )
        request = self.service.submit_request(request)

        # 第1ステップを否認
        request = self.service.reject_step(
            request=request,
            step=self.step1,
            approver=self.manager,
            comment="Rejected",
        )

        self.assertEqual(request.status, "rejected")
        self.assertIsNone(request.current_step)
        self.assertIsNotNone(request.completed_at)

        # アクションが記録されている
        actions = ApprovalAction.objects.filter(request=request, step=self.step1)
        self.assertEqual(actions.count(), 1)
        self.assertEqual(actions.first().action, "reject")

    def test_return_to_requester(self):
        """申請者に差戻せる。"""
        request = self.service.create_request(
            workflow=self.workflow,
            content_object=self.demo,
            requester=self.requester,
        )
        request = self.service.submit_request(request)

        # 第1ステップを差戻し
        request = self.service.return_to_requester(
            request=request,
            step=self.step1,
            approver=self.manager,
            comment="Please revise",
        )

        self.assertEqual(request.status, "draft")
        self.assertIsNone(request.current_step)
        self.assertIsNone(request.requested_at)

        # アクションが記録されている
        actions = ApprovalAction.objects.filter(request=request, step=self.step1)
        self.assertEqual(actions.count(), 1)
        self.assertEqual(actions.first().action, "return")

    def test_get_pending_requests_for_user(self):
        """ユーザーが承認可能な依頼を取得できる。"""
        request = self.service.create_request(
            workflow=self.workflow,
            content_object=self.demo,
            requester=self.requester,
        )
        request = self.service.submit_request(request)

        # managerが承認可能
        pending = self.service.get_pending_requests_for_user(self.manager)
        self.assertIn(request, pending)

        # directorはまだ承認できない（step1なので）
        pending = self.service.get_pending_requests_for_user(self.director)
        self.assertNotIn(request, pending)
