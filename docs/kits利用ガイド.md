# Kits 使い方ガイド - 30 分で動くアプリを実現する「型」

このドキュメントは、`kits/` 配下の共通部品を**実際のインターン課題にコピペで適用する**ための実践ガイドです。

---

## 🎯 前提知識

### kits とは？

**再利用可能な業務アプリの共通部品**です。インターン課題が来たら、以下の流れで適用します：

```bash
# 1. 新しいアプリを作成（例：経費申請システム）
mkdir -p school_diary/expense_app
dj startapp expense_app school_diary/expense_app

# 2. kitsの「型」をコピーして、ビジネスロジックを追加
# 3. 30分で動くアプリが完成！
```

---

## 📦 kits.demos - 承認フロー付きモデルの「型」

### 使用場面

- 「〇〇申請システムを作ってください」系の課題
- 承認フロー（申請 → 承認/否認）が必要な業務アプリ

### 実装パターン（コピペ可）

#### ステップ 1: モデルを作る

```python
# school_diary/expense_app/models.py
from django.conf import settings
from django.db import models, transaction
from django_fsm import FSMField, transition
from simple_history.models import HistoricalRecords

class ExpenseRequest(models.Model):
    """経費申請モデル（DemoRequestの型を流用）"""

    # ビジネス固有のフィールド
    title = models.CharField("タイトル", max_length=200)
    amount = models.DecimalField("金額", max_digits=10, decimal_places=2)

    # 状態管理（型そのまま）
    status = FSMField("ステータス", default="draft", max_length=50)

    # 承認フロー用フィールド（型そのまま）
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="作成者",
        related_name="expense_requests",
    )
    created_at = models.DateTimeField("作成日時", auto_now_add=True)
    updated_at = models.DateTimeField("更新日時", auto_now=True)

    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="requested_expenses",
        verbose_name="申請者",
    )
    approver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_expenses",
        verbose_name="承認者",
    )

    # 変更履歴の自動記録（型そのまま）
    history = HistoricalRecords()

    class Meta:
        verbose_name = "経費申請"
        verbose_name_plural = "経費申請"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} - {self.amount}円"

    def save(self, *args, **kwargs):
        """新規作成時の履歴メタデータを自動設定（型そのまま）"""
        is_new = not self.pk

        if is_new:
            if not hasattr(self, "_history_user") and self.created_by:
                self._history_user = self.created_by
            if not hasattr(self, "_change_reason"):
                self._change_reason = "新規作成"

        super().save(*args, **kwargs)

    # --- 状態遷移メソッド（型そのまま、docstringだけ書き換え） ---

    def submit(self, by=None, reason=None):
        """申請する (下書き -> 申請中)"""
        with transaction.atomic():
            self.requester = by
            if by:
                self._history_user = by
            self._change_reason = reason if reason is not None else "申請されました。"
            self._perform_submit()
            self.save(update_fields=["requester", "status", "updated_at"])

    def approve(self, by=None, reason=None):
        """承認する (申請中 -> 承認済み)"""
        with transaction.atomic():
            self.approver = by
            if by:
                self._history_user = by
            self._change_reason = reason if reason is not None else "承認されました。"
            self._perform_approve()
            self.save(update_fields=["approver", "status", "updated_at"])

    def deny(self, by=None, reason=None):
        """否認する (申請中 -> 否認)"""
        with transaction.atomic():
            self.approver = by
            if by:
                self._history_user = by
            self._change_reason = reason if reason is not None else "否認されました。"
            self._perform_deny()
            self.save(update_fields=["approver", "status", "updated_at"])

    def return_to_draft(self, by=None, reason=None):
        """差戻しする (申請中/承認済み -> 下書き)"""
        with transaction.atomic():
            if by:
                self._history_user = by
            self._change_reason = reason if reason is not None else "差戻しされました。"
            self._perform_return_to_draft()
            self.save(update_fields=["status", "updated_at"])

    # --- 状態遷移の内部実装（型そのまま） ---

    @transition(field=status, source="draft", target="submitted")
    def _perform_submit(self):
        """内部用: django-fsmによる状態遷移の実装(draft -> submitted)"""

    @transition(field=status, source="submitted", target="approved")
    def _perform_approve(self):
        """内部用: django-fsmによる状態遷移の実装(submitted -> approved)"""

    @transition(field=status, source="submitted", target="denied")
    def _perform_deny(self):
        """内部用: django-fsmによる状態遷移の実装(submitted -> denied)"""

    @transition(field=status, source=["submitted", "approved"], target="draft")
    def _perform_return_to_draft(self):
        """内部用: django-fsmによる状態遷移の実装(submitted/approved -> draft)"""
```

#### ステップ 2: 管理画面を作る

```python
# school_diary/expense_app/admin.py
from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from .models import ExpenseRequest

@admin.register(ExpenseRequest)
class ExpenseRequestAdmin(SimpleHistoryAdmin):
    """経費申請の管理画面"""

    list_display = ["title", "amount", "status", "requester", "approver", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["title", "requester__email", "approver__email"]
    readonly_fields = ["created_at", "updated_at", "created_by", "requester", "approver"]

    # 履歴表示を有効化（SimpleHistoryAdminの機能）
    history_list_display = ["status", "history_user", "history_change_reason"]
```

#### ステップ 3: 設定に追加

```python
# config/settings/base.py
LOCAL_APPS = [
    # ...
    "school_diary.expense_app.apps.ExpenseAppConfig",  # 追加
]
```

#### ステップ 4: マイグレーション

```bash
dj makemigrations
dj migrate
```

#### ステップ 5: 動作確認

```python
# Djangoシェルで確認
dj shell

>>> from school_diary.expense_app.models import ExpenseRequest
>>> from school_diary.users.models import User
>>> user = User.objects.get(email="user@example.com")
>>> approver = User.objects.get(email="approver@example.com")

# 申請を作成
>>> req = ExpenseRequest.objects.create(
...     title="交通費申請",
...     amount=5000,
...     created_by=user
... )

# 状態遷移
>>> req.submit(by=user)
>>> req.status
'submitted'

>>> req.approve(by=approver)
>>> req.status
'approved'

# 履歴を確認
>>> req.history.all()
<QuerySet [<HistoricalExpenseRequest: 交通費申請>, ...]>
```

**所要時間**: **10 分で完成**（ほぼコピペ）

---

## 👥 kits.accounts - ユーザー・グループ・権限管理

### 使用場面

- インターン課題で「管理者だけが承認できる」などの権限制御が必要な場合
- テストユーザーを素早く作成したい場合

### 実装パターン（コマンド実行のみ）

#### 開発環境の初期セットアップ

```bash
# グループ・テストユーザーをまとめて作成
dj setup_dev

# 作成されるグループ：
# - General Users（一般ユーザー）
# - Approvers（承認者）
# - Administrators（管理者）
# - Auditors（監査者）
# - Editors（編集者）

# 作成されるテストユーザー（全員パスワード: password123）：
# - admin@example.com (管理者)
# - approver@example.com (承認者)
# - user@example.com (一般)
# - auditor@example.com (監査者)
# - editor@example.com (編集者)
```

#### 既存のユーザーにグループを割り当て

```python
# Djangoシェルで実行
dj shell

>>> from school_diary.users.models import User
>>> from django.contrib.auth.models import Group

>>> user = User.objects.get(email="newuser@example.com")
>>> approvers_group = Group.objects.get(name="Approvers")
>>> user.groups.add(approvers_group)
>>> user.save()
```

#### ビューで権限をチェック

```python
# school_diary/expense_app/views.py
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponseForbidden

@login_required
def approve_expense(request, pk):
    """承認者のみが実行できるビュー"""
    # 方法1: グループで判定
    if not request.user.groups.filter(name="Approvers").exists():
        return HttpResponseForbidden("承認権限がありません")

    # 方法2: パーミッションで判定（Django標準）
    if not request.user.has_perm("expense_app.change_expenserequest"):
        return HttpResponseForbidden("承認権限がありません")

    # 承認処理
    expense = ExpenseRequest.objects.get(pk=pk)
    expense.approve(by=request.user)

    return redirect("expense_list")
```

**所要時間**: **5 分で完成**（コマンド 1 つ）

---

## 📝 kits.audit - 変更履歴の自動記録

### 使用場面

- 「誰が、いつ、何を変更したか」を記録する必要がある業務アプリ
- 監査ログが必要なシステム

### 実装パターン（1 行追加するだけ）

#### モデルに履歴管理を追加

```python
# school_diary/expense_app/models.py
from simple_history.models import HistoricalRecords

class ExpenseRequest(models.Model):
    # ...フィールド定義...

    # この1行を追加するだけで履歴管理が有効化される
    history = HistoricalRecords()
```

#### 履歴を確認

```python
# Djangoシェルで確認
dj shell

>>> from school_diary.expense_app.models import ExpenseRequest
>>> req = ExpenseRequest.objects.get(pk=1)

# 全ての変更履歴を取得
>>> req.history.all()
<QuerySet [
    <HistoricalExpenseRequest: 交通費申請 (approved)>,
    <HistoricalExpenseRequest: 交通費申請 (submitted)>,
    <HistoricalExpenseRequest: 交通費申請 (draft)>
]>

# 最新の変更を確認
>>> latest = req.history.first()
>>> latest.history_user
<User: approver@example.com>
>>> latest.history_change_reason
'承認されました。'
>>> latest.history_date
datetime.datetime(2025, 10, 2, 10, 30, 0)
```

#### 管理画面で履歴を表示

```python
# school_diary/expense_app/admin.py
from simple_history.admin import SimpleHistoryAdmin

@admin.register(ExpenseRequest)
class ExpenseRequestAdmin(SimpleHistoryAdmin):  # ← SimpleHistoryAdminを継承
    """これだけで管理画面に「履歴」タブが追加される"""
    history_list_display = ["status", "history_user", "history_change_reason"]
```

**所要時間**: **3 分で完成**（1 行追加するだけ）

---

## ✅ kits.approvals - 状態遷移の自動ログ記録

### 使用場面

- FSM の状態遷移を自動的に履歴に記録したい場合
- 「誰が承認したか」を確実に記録したい場合

### 実装パターン（自動適用）

#### 前提条件

1. モデルに `FSMField` がある
2. モデルに `history = HistoricalRecords()` がある
3. `kits.approvals` が `INSTALLED_APPS` に登録されている

```python
# config/settings/base.py
LOCAL_APPS = [
    # ...
    "kits.approvals.apps.ApprovalsConfig",  # ← これが登録されていればOK
]
```

#### 動作確認

```python
# Djangoシェルで確認
dj shell

>>> from school_diary.expense_app.models import ExpenseRequest
>>> from school_diary.users.models import User
>>> user = User.objects.get(email="user@example.com")
>>> approver = User.objects.get(email="approver@example.com")

# 申請を作成
>>> req = ExpenseRequest.objects.create(title="交通費", amount=5000, created_by=user)

# 状態遷移を実行
>>> req.submit(by=user)

# 履歴レコードを確認
>>> history = req.history.first()
>>> history.history_user  # ← 自動的に設定されている
<User: user@example.com>
>>> history.history_change_reason  # ← 自動的に設定されている
"State transitioned via '_perform_submit' from 'draft' to 'submitted'."
```

**仕組み**:

- `kits.approvals.signals.log_state_transition` が、FSM の `post_transition` シグナルを受信
- 履歴レコードに `history_user` と `history_change_reason` を自動設定
- トランザクション保護により、状態遷移と履歴記録の一貫性を保証

**所要時間**: **0 分**（自動適用）

---

## 🚀 インターン課題への適用フロー（全体像）

### 想定課題: 「書籍貸出管理システムを作ってください」

#### 1. アプリを作成（3 分）

```bash
mkdir -p school_diary/library_app
dj startapp library_app school_diary/library_app
```

#### 2. モデルを作成（7 分）

```python
# school_diary/library_app/models.py
# kits.demosのDemoRequestをコピー＆カスタマイズ

class BookLoanRequest(models.Model):
    """書籍貸出申請モデル"""

    # ビジネス固有フィールド
    book_title = models.CharField("書籍名", max_length=200)
    isbn = models.CharField("ISBN", max_length=13, blank=True)

    # 以下、DemoRequestから全てコピペ
    status = FSMField(...)
    created_by = models.ForeignKey(...)
    # ...（残りの型をそのまま流用）
```

#### 3. 管理画面を作成（2 分）

```python
# school_diary/library_app/admin.py
# kits.demos.adminをコピー＆カスタマイズ
```

#### 4. 設定に追加（1 分）

```python
# config/settings/base.py
LOCAL_APPS += ["school_diary.library_app.apps.LibraryAppConfig"]
```

#### 5. マイグレーション（2 分）

```bash
dj makemigrations
dj migrate
```

#### 6. テストデータ作成（5 分）

```bash
dj setup_dev  # テストユーザー作成
dj shell  # シェルで貸出データを作成
```

#### 7. 動作確認（10 分）

- 管理画面にログイン
- 申請 → 承認フローを実行
- 履歴を確認

**合計: 30 分で完成** ✅

---

## 💡 よくある質問

### Q1: 状態遷移のパターンを変更したい（例：承認を 2 段階にする）

```python
class ExpenseRequest(models.Model):
    # ...

    @transition(field=status, source="submitted", target="first_approved")
    def _perform_first_approve(self):
        """1次承認"""

    @transition(field=status, source="first_approved", target="final_approved")
    def _perform_final_approve(self):
        """最終承認"""

    def first_approve(self, by=None, reason=None):
        """1次承認メソッド（公開API）"""
        with transaction.atomic():
            self.first_approver = by
            if by:
                self._history_user = by
            self._change_reason = reason or "1次承認されました。"
            self._perform_first_approve()
            self.save(update_fields=["first_approver", "status", "updated_at"])
```

### Q2: 管理画面で状態遷移ボタンを追加したい

```python
# school_diary/expense_app/admin.py
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

@admin.register(ExpenseRequest)
class ExpenseRequestAdmin(SimpleHistoryAdmin):
    list_display = ["title", "status", "action_buttons"]

    def action_buttons(self, obj):
        """状態に応じたアクションボタンを表示"""
        if obj.status == "submitted":
            approve_url = reverse("admin:expense_approve", args=[obj.pk])
            deny_url = reverse("admin:expense_deny", args=[obj.pk])
            return format_html(
                '<a class="button" href="{}">承認</a>'
                '<a class="button" href="{}">否認</a>',
                approve_url,
                deny_url,
            )
        return "-"
    action_buttons.short_description = "アクション"
```

### Q3: API エンドポイントを追加したい（Django REST framework）

```python
# school_diary/expense_app/serializers.py
from rest_framework import serializers
from .models import ExpenseRequest

class ExpenseRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseRequest
        fields = "__all__"

# school_diary/expense_app/views.py
from rest_framework import viewsets
from .models import ExpenseRequest
from .serializers import ExpenseRequestSerializer

class ExpenseRequestViewSet(viewsets.ModelViewSet):
    """経費申請のREST API"""
    queryset = ExpenseRequest.objects.all()
    serializer_class = ExpenseRequestSerializer

    # 状態遷移用カスタムアクション
    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        expense = self.get_object()
        expense.submit(by=request.user)
        return Response({"status": "submitted"})
```

---

## 🎯 まとめ

### kits の「型」を使えば、30 分で動くアプリが完成する理由

1. **モデルの型**（`kits.demos`） → **7 分**でコピペ完了
2. **管理画面の型**（`SimpleHistoryAdmin`） → **2 分**でコピペ完了
3. **権限管理**（`kits.accounts`） → **1 コマンド**で完了
4. **履歴管理**（`kits.audit`） → **1 行追加**で完了
5. **状態遷移ログ**（`kits.approvals`） → **自動適用**

**合計**: 実装時間 10 分 + 動作確認・調整 20 分 = **30 分**

---

**次のステップ**: このドキュメントを読み終えたら、実際に「仮想インターン課題」を 1 つ実装してみましょう！
