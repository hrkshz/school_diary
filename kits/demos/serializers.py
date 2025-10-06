"""
DemoRequestのREST APIシリアライザー (サンプル実装)

このファイルは、インターン課題でAPI実装が必要になったときの
「型」として使用できます。
"""

from rest_framework import serializers

from .models import DemoRequest


class DemoRequestSerializer(serializers.ModelSerializer):
    """
    DemoRequestのシリアライザー。

    使い方の例:
    ============

    1. ViewSetの作成
    ----------------
    # kits/demos/views.py
    from rest_framework import viewsets
    from .models import DemoRequest
    from .serializers import DemoRequestSerializer

    class DemoRequestViewSet(viewsets.ModelViewSet):
        queryset = DemoRequest.objects.all()
        serializer_class = DemoRequestSerializer

    2. URLの設定
    ------------
    # config/urls.py
    from rest_framework.routers import DefaultRouter
    from kits.demos.views import DemoRequestViewSet

    router = DefaultRouter()
    router.register(r'demo-requests', DemoRequestViewSet)

    urlpatterns = [
        # ...
        path('api/', include(router.urls)),
    ]

    3. APIエンドポイント
    -------------------
    GET    /api/demo-requests/          # 一覧取得
    POST   /api/demo-requests/          # 新規作成
    GET    /api/demo-requests/{id}/     # 詳細取得
    PUT    /api/demo-requests/{id}/     # 更新
    DELETE /api/demo-requests/{id}/     # 削除
    """

    # 読み取り専用フィールド (自動設定されるもの)
    created_by_email = serializers.EmailField(
        source="created_by.email",
        read_only=True,
    )
    requester_email = serializers.EmailField(
        source="requester.email",
        read_only=True,
        allow_null=True,
    )
    approver_email = serializers.EmailField(
        source="approver.email",
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = DemoRequest
        fields = [
            "id",
            "title",
            "description",
            "status",
            "created_by",
            "created_by_email",
            "created_at",
            "updated_at",
            "requester",
            "requester_email",
            "approver",
            "approver_email",
        ]
        read_only_fields = [
            "id",
            "status",  # 状態遷移はカスタムアクションで実行
            "created_by",
            "created_at",
            "updated_at",
            "requester",
            "approver",
        ]

    def create(self, validated_data):
        """
        新規作成時に、created_byを自動設定する。
        """
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)


class DemoRequestActionSerializer(serializers.Serializer):
    """
    状態遷移アクション用のシリアライザー。

    使い方の例:
    ============

    # kits/demos/views.py
    from rest_framework.decorators import action
    from rest_framework.response import Response

    class DemoRequestViewSet(viewsets.ModelViewSet):
        # ...

        @action(detail=True, methods=["post"])
        def submit(self, request, pk=None):
            demo_request = self.get_object()
            serializer = DemoRequestActionSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            demo_request.submit(
                by=request.user,
                reason=serializer.validated_data.get("reason"),
            )

            return Response({
                "status": demo_request.status,
                "message": "申請されました",
            })

    APIエンドポイント:
    POST /api/demo-requests/{id}/submit/
    POST /api/demo-requests/{id}/approve/
    POST /api/demo-requests/{id}/deny/
    POST /api/demo-requests/{id}/return_to_draft/

    リクエストボディ:
    {
        "reason": "承認理由 (任意)"
    }
    """

    reason = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="変更理由 (省略可)",
    )
