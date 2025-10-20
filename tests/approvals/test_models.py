"""
kits.approvals モデルのテスト。
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.utils import timezone

from kits.approvals.models import ApprovalRequest
from kits.approvals.models import ApprovalStep
from kits.approvals.models import ApprovalWorkflow
from kits.demos.models import DemoRequest

User = get_user_model()


class ApprovalWorkflowModelTest(TestCase):
    """ApprovalWorkflow モデルのテスト。"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="password",
        )

    def test_create_workflow(self):
        """ワークフローを作成できる。"""
        workflow = ApprovalWorkflow.objects.create(
            name="Test Workflow",
            description="Test Description",
            is_active=True,
            default_deadline_hours=48,
            created_by=self.user,
        )

        self.assertEqual(workflow.name, "Test Workflow")
        self.assertEqual(workflow.default_deadline_hours, 48)
        self.assertTrue(workflow.is_active)
        self.assertEqual(workflow.created_by, self.user)

    def test_get_steps(self):
        """ワークフローのステップを取得できる。"""
        workflow = ApprovalWorkflow.objects.create(name="Test Workflow")
        group = Group.objects.create(name="Approvers")

        step1 = ApprovalStep.objects.create(
            workflow=workflow,
            order=1,
            name="Step 1",
            approver_role=group,
        )
        step2 = ApprovalStep.objects.create(
            workflow=workflow,
            order=2,
            name="Step 2",
            approver_role=group,
        )

        steps = workflow.get_steps()
        self.assertEqual(steps.count(), 2)
        self.assertEqual(list(steps), [step1, step2])

    def test_get_first_step(self):
        """最初のステップを取得できる。"""
        workflow = ApprovalWorkflow.objects.create(name="Test Workflow")
        group = Group.objects.create(name="Approvers")

        step1 = ApprovalStep.objects.create(
            workflow=workflow,
            order=1,
            name="Step 1",
            approver_role=group,
        )
        ApprovalStep.objects.create(
            workflow=workflow,
            order=2,
            name="Step 2",
            approver_role=group,
        )

        first_step = workflow.get_first_step()
        self.assertEqual(first_step, step1)


class ApprovalStepModelTest(TestCase):
    """ApprovalStep モデルのテスト。"""

    def setUp(self):
        self.workflow = ApprovalWorkflow.objects.create(name="Test Workflow")
        self.group = Group.objects.create(name="Approvers")
        self.user = User.objects.create_user(
            email="approver@example.com",
            password="password",
        )
        self.user.groups.add(self.group)

    def test_create_step(self):
        """ステップを作成できる。"""
        step = ApprovalStep.objects.create(
            workflow=self.workflow,
            order=1,
            name="Test Step",
            approver_role=self.group,
        )

        self.assertEqual(step.workflow, self.workflow)
        self.assertEqual(step.order, 1)
        self.assertEqual(step.name, "Test Step")
        self.assertEqual(step.approver_role, self.group)

    def test_get_next_step(self):
        """次のステップを取得できる。"""
        step1 = ApprovalStep.objects.create(
            workflow=self.workflow,
            order=1,
            name="Step 1",
            approver_role=self.group,
        )
        step2 = ApprovalStep.objects.create(
            workflow=self.workflow,
            order=2,
            name="Step 2",
            approver_role=self.group,
        )

        next_step = step1.get_next_step()
        self.assertEqual(next_step, step2)

        # 最後のステップの次はNone
        self.assertIsNone(step2.get_next_step())

    def test_can_approve(self):
        """ユーザーが承認できるかを判定できる。"""
        step = ApprovalStep.objects.create(
            workflow=self.workflow,
            order=1,
            name="Step 1",
            approver_role=self.group,
        )

        # グループに所属しているユーザーは承認できる
        self.assertTrue(step.can_approve(self.user))

        # グループに所属していないユーザーは承認できない
        other_user = User.objects.create_user(
            email="other@example.com",
            password="password",
        )
        self.assertFalse(step.can_approve(other_user))


class ApprovalRequestModelTest(TestCase):
    """ApprovalRequest モデルのテスト。"""

    def setUp(self):
        self.workflow = ApprovalWorkflow.objects.create(
            name="Test Workflow",
            default_deadline_hours=48,
        )
        self.group = Group.objects.create(name="Approvers")
        self.step = ApprovalStep.objects.create(
            workflow=self.workflow,
            order=1,
            name="Step 1",
            approver_role=self.group,
        )
        self.user = User.objects.create_user(
            email="requester@example.com",
            password="password",
        )
        self.demo = DemoRequest.objects.create(
            title="Test Demo",
            created_by=self.user,
        )

    def test_create_request(self):
        """承認依頼を作成できる。"""
        request = ApprovalRequest.objects.create(
            workflow=self.workflow,
            content_object=self.demo,
            requester=self.user,
            status="draft",
        )

        self.assertEqual(request.workflow, self.workflow)
        self.assertEqual(request.content_object, self.demo)
        self.assertEqual(request.requester, self.user)
        self.assertEqual(request.status, "draft")

    def test_submit_request(self):
        """承認依頼を提出できる。"""
        request = ApprovalRequest.objects.create(
            workflow=self.workflow,
            content_object=self.demo,
            requester=self.user,
            status="draft",
        )

        request.submit()

        self.assertEqual(request.status, "pending")
        self.assertIsNotNone(request.requested_at)
        self.assertEqual(request.current_step, self.step)
        self.assertIsNotNone(request.deadline)

    def test_cancel_request(self):
        """承認依頼をキャンセルできる。"""
        request = ApprovalRequest.objects.create(
            workflow=self.workflow,
            content_object=self.demo,
            requester=self.user,
            status="draft",
        )

        request.cancel(self.user)

        self.assertEqual(request.status, "cancelled")
        self.assertIsNotNone(request.completed_at)

    def test_is_overdue(self):
        """期限切れの判定ができる。"""
        request = ApprovalRequest.objects.create(
            workflow=self.workflow,
            content_object=self.demo,
            requester=self.user,
            status="pending",
            deadline=timezone.now() - timezone.timedelta(hours=1),
        )

        self.assertTrue(request.is_overdue())

        # 期限前は期限切れではない
        request.deadline = timezone.now() + timezone.timedelta(hours=1)
        request.save()
        self.assertFalse(request.is_overdue())

    def test_get_pending_approvers(self):
        """承認可能なユーザーを取得できる。"""
        approver = User.objects.create_user(
            email="approver@example.com",
            password="password",
        )
        approver.groups.add(self.group)

        request = ApprovalRequest.objects.create(
            workflow=self.workflow,
            content_object=self.demo,
            requester=self.user,
            status="pending",
            current_step=self.step,
        )

        approvers = request.get_pending_approvers()
        self.assertIn(approver, approvers)
