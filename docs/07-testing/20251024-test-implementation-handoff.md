# テスト実装引き継ぎドキュメント

> **作成日**: 2025-10-24
> **作成者**: AI (Claude Code)
> **目的**: 次のセッションでテスト実装を完了させるための引き継ぎ
> **対象**: 全機能テスト追加（残り17機能）

---

## 📊 現状サマリー

### 完了済み（Phase 1: Critical Path）
- ✅ テスト基盤構築完了
- ✅ 28テスト実装済み（12機能カバー）
- ✅ CI/CD更新完了
- ✅ README.md、conftest.py完備

### 今回のゴール（Phase 2: Full Coverage）
- 🎯 残り17機能のテスト実装
- 🎯 合計48テスト（カバー率100%）
- 🎯 所要時間: 2-3時間

---

## 📁 ディレクトリ構造（現状）

```
school_diary/diary/tests/
├── README.md                     ✅ 完成
├── conftest.py                   ✅ 完成（Fixture Pyramid）
└── features/
    ├── test_auth_features.py     ✅ 8テスト（AUTH-001, SYS-002）
    ├── test_student_features.py  ✅ 8テスト（STU-001〜004）
    ├── test_teacher_features.py  ✅ 8テスト（TEA-001〜003）
    └── test_teacher_actions.py   ✅ 4テスト（TEA-ACT-001, 008, 009）
```

---

## 🎯 実装タスクリスト（優先順位付き）

### Priority 1: システム共通・認証（8テスト、30分）

#### 1. test_auth_features.py に追加（6テスト）
```python
class TestAUTH002Logout:
    """AUTH-002: ログアウト機能のテスト"""

    def test_auth002_logout_success(self, authenticated_student_client):
        """
        Given: ログイン済みユーザー
        When: ログアウト処理
        Then: ログアウト成功、ログインページにリダイレクト
        """
        # Implementation hint:
        # response = authenticated_student_client.post(reverse("account_logout"))
        # assert response.status_code == 302
        # assert "/accounts/login/" in response.url


class TestAUTH003PasswordChange:
    """AUTH-003: パスワード変更機能のテスト"""

    def test_auth003_password_change_success(self, authenticated_student_client):
        """
        Given: ログイン済みユーザー
        When: パスワード変更
        Then: 変更成功
        """
        # Implementation hint:
        # data = {
        #     "oldpassword": "testpass123",
        #     "password1": "newpass456",
        #     "password2": "newpass456",
        # }
        # response = authenticated_student_client.post(
        #     reverse("account_change_password"), data
        # )


class TestAUTH004To007PasswordReset:
    """AUTH-004〜007: パスワードリセット機能のテスト"""

    def test_auth004_password_reset_request_success(self, client):
        """
        Given: 未認証ユーザー
        When: パスワードリセット要求
        Then: リセットメール送信完了ページ表示
        """
        # Implementation hint:
        # data = {"email": "student@test.com"}
        # response = client.post(reverse("account_reset_password"), data)

    def test_auth005_password_reset_done_display(self, client):
        """AUTH-005: リセットメール送信完了ページ表示"""
        pass

    def test_auth007_password_reset_complete_display(self, client):
        """AUTH-007: パスワード変更完了ページ表示"""
        pass


#### 2. 新規ファイル: test_system_features.py（2テスト）
```python
"""
03-features.md System Features Tests

このモジュールは以下の機能をテストします:
- SYS-001: ヘルスチェック
- SYS-003: About

Traceability Matrix:
| Test Method | Feature ID | Scenario | Priority |
|-------------|------------|----------|----------|
| test_sys001_health_check_success | SYS-001 | 死活監視 | P2 |
| test_sys003_about_display_success | SYS-003 | About表示 | P2 |
"""

import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestSYS001HealthCheck:
    """SYS-001: ヘルスチェックのテスト"""

    def test_sys001_health_check_success(self, client):
        """
        Given: システム稼働中
        When: /health/ にアクセス
        Then: 200 OK、ステータス情報返却
        """
        # Implementation hint:
        # response = client.get(reverse("health_check"))
        # assert response.status_code == 200


@pytest.mark.django_db
class TestSYS003About:
    """SYS-003: Aboutページのテスト"""

    def test_sys003_about_display_success(self, client):
        """
        Given: 任意のユーザー
        When: /about/ にアクセス
        Then: システム概要が表示される
        """
        # Implementation hint:
        # response = client.get(reverse("about"))
        # assert response.status_code == 200
```

---

### Priority 2: 担任アクション（6テスト、45分）

#### test_teacher_actions.py に追加（6テスト）

```python
class TestTEAACT002MarkActionCompleted:
    """TEA-ACT-002: 対応完了処理のテスト"""

    def test_teaact002_mark_action_completed_success(
        self,
        authenticated_teacher_client,
        unread_diary_entry,
    ):
        """
        Given: internal_action設定済みのエントリー
        When: 対応完了処理を実行
        Then: action_status=COMPLETED
        """
        # Implementation hint:
        # unread_diary_entry.internal_action = "parent_contact"
        # unread_diary_entry.action_status = ActionStatus.IN_PROGRESS
        # unread_diary_entry.save()
        #
        # response = authenticated_teacher_client.post(
        #     reverse("diary:teacher_mark_action_completed",
        #             kwargs={"diary_id": unread_diary_entry.id})
        # )
        #
        # unread_diary_entry.refresh_from_db()
        # assert unread_diary_entry.action_status == ActionStatus.COMPLETED


class TestTEAACT003To006TeacherNotes:
    """TEA-ACT-003〜006: 担任メモのテスト"""

    def test_teaact003_add_note_success(
        self,
        authenticated_teacher_client,
        student_user,
    ):
        """TEA-ACT-003: メモ追加"""
        # Implementation hint:
        # data = {
        #     "content": "テストメモ",
        #     "is_shared": False,  # 個人メモ
        # }
        # response = authenticated_teacher_client.post(
        #     reverse("diary:teacher_add_note",
        #             kwargs={"student_id": student_user.id}),
        #     data,
        # )

    def test_teaact004_edit_note_success(self):
        """TEA-ACT-004: メモ編集"""
        pass

    def test_teaact005_delete_note_success(self):
        """TEA-ACT-005: メモ削除"""
        pass

    def test_teaact006_mark_shared_note_read_success(self):
        """TEA-ACT-006: 共有メモ既読"""
        pass


class TestTEAACT007AttendanceSave:
    """TEA-ACT-007: 出席保存のテスト"""

    def test_teaact007_save_attendance_success(
        self,
        authenticated_teacher_client,
        student_user,
        today,
    ):
        """
        Given: 担任ユーザー
        When: 出席記録を保存
        Then: DailyAttendance作成成功
        """
        # Implementation hint:
        # data = {
        #     "student_id": student_user.id,
        #     "date": today,
        #     "status": "present",
        # }
        # response = authenticated_teacher_client.post(
        #     reverse("diary:teacher_save_attendance"),
        #     data,
        #     HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        # )
```

---

### Priority 3: 学年主任・校長・管理者（6テスト、45分）

#### 新規ファイル: test_grade_school_leader_features.py（6テスト）

```python
"""
03-features.md Grade/School Leader Features Tests

このモジュールは以下の機能をテストします:
- GRD-001: 学年統計
- SCH-001: 学校統計
- ADM-001: Django管理画面

Traceability Matrix:
| Test Method | Feature ID | Scenario | Priority |
|-------------|------------|----------|----------|
| test_grd001_grade_overview_display_success | GRD-001 | 学年統計表示 | P2 |
| test_grd001_grade_overview_other_grade_forbidden | GRD-001 | 他学年禁止 | P2 |
| test_sch001_school_overview_display_success | SCH-001 | 学校統計表示 | P2 |
| test_sch001_school_overview_forbidden_for_non_leaders | SCH-001 | 権限なし禁止 | P2 |
| test_adm001_admin_access_success | ADM-001 | 管理画面アクセス | P2 |
| test_adm001_admin_access_forbidden_for_non_superuser | ADM-001 | 非管理者禁止 | P2 |
"""

import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestGRD001GradeOverview:
    """GRD-001: 学年統計のテスト"""

    def test_grd001_grade_overview_display_success(
        self,
        authenticated_grade_leader_client,
    ):
        """
        Given: 学年主任ユーザー
        When: 学年統計ページにアクセス
        Then: 学年統計、クラス比較、メンタル推移が表示される
        """
        # Implementation hint:
        # response = authenticated_grade_leader_client.get(
        #     reverse("diary:grade_overview")
        # )
        # assert response.status_code == 200
        # assert "diary/grade_overview.html" in [t.name for t in response.templates]

    def test_grd001_grade_overview_other_grade_forbidden(
        self,
        client,
        classroom,
    ):
        """
        Given: 2年の学年主任
        When: 1年の学年統計にアクセス試行
        Then: 自分の学年のみ表示される
        """
        pass


@pytest.mark.django_db
class TestSCH001SchoolOverview:
    """SCH-001: 学校統計のテスト"""

    def test_sch001_school_overview_display_success(
        self,
        client,
        school_leader_user,
    ):
        """
        Given: 校長/教頭ユーザー
        When: 学校統計ページにアクセス
        Then: 学校全体統計、学級閉鎖判断支援が表示される
        """
        # Implementation hint:
        # client.force_login(school_leader_user)
        # response = client.get(reverse("diary:school_overview"))
        # assert response.status_code == 200

    def test_sch001_school_overview_forbidden_for_non_leaders(
        self,
        authenticated_student_client,
    ):
        """
        Given: 生徒ユーザー
        When: 学校統計ページにアクセス試行
        Then: 403 Forbidden
        """
        pass


@pytest.mark.django_db
class TestADM001AdminAccess:
    """ADM-001: Django管理画面のテスト"""

    def test_adm001_admin_access_success(self, client, superuser):
        """
        Given: システム管理者（is_superuser=True）
        When: /admin/ にアクセス
        Then: 管理画面が表示される
        """
        # Implementation hint:
        # client.force_login(superuser)
        # response = client.get("/admin/")
        # assert response.status_code == 200

    def test_adm001_admin_access_forbidden_for_non_superuser(
        self,
        authenticated_student_client,
    ):
        """
        Given: 一般ユーザー
        When: /admin/ にアクセス試行
        Then: 302 → ログインページにリダイレクト
        """
        # Implementation hint:
        # response = authenticated_student_client.get("/admin/")
        # assert response.status_code == 302
```

---

## 🔧 実装手順（ステップバイステップ）

### Step 1: conftest.py に追加Fixture（必要に応じて）

```python
@pytest.fixture
def teacher_note(db, teacher_user, student_user):
    """担任メモ（TEA-ACT-003〜006用）"""
    from school_diary.diary.models import TeacherNote

    return TeacherNote.objects.create(
        author=teacher_user,
        student=student_user,
        content="テストメモ",
        is_shared=False,
    )


@pytest.fixture
def daily_attendance(db, student_user, today):
    """出席記録（TEA-ACT-007用）"""
    from school_diary.diary.models import DailyAttendance

    return DailyAttendance.objects.create(
        student=student_user,
        date=today,
        status="present",
    )
```

### Step 2: テスト実装パターン（既存を参考）

#### パターンA: POSTリクエスト
```python
def test_xxx_action_success(self, authenticated_client, fixture):
    """
    Given: 前提条件
    When: アクション実行
    Then: 期待結果
    """
    # Arrange
    data = {"key": "value"}

    # Act
    response = authenticated_client.post(reverse("url_name"), data)

    # Assert
    assert response.status_code == 302  # or 200
    fixture.refresh_from_db()
    assert fixture.field == "expected_value"
```

#### パターンB: GETリクエスト（表示確認）
```python
def test_xxx_display_success(self, authenticated_client):
    """
    Given: 前提条件
    When: ページアクセス
    Then: 正しく表示される
    """
    # Act
    response = authenticated_client.get(reverse("url_name"))

    # Assert
    assert response.status_code == 200
    assert "template.html" in [t.name for t in response.templates]
```

#### パターンC: 権限チェック
```python
def test_xxx_forbidden(self, authenticated_client):
    """
    Given: 権限なしユーザー
    When: アクセス試行
    Then: 403 Forbidden
    """
    # Act
    response = authenticated_client.get(reverse("url_name"))

    # Assert
    assert response.status_code == 403
```

### Step 3: テスト実行コマンド

```bash
# 個別ファイル実行
DATABASE_URL="sqlite:///test.db" uv run pytest school_diary/diary/tests/features/test_system_features.py -v

# 全テスト実行
DATABASE_URL="sqlite:///test.db" uv run pytest school_diary/diary/tests/features/ -v

# カバレッジ付き
DATABASE_URL="sqlite:///test.db" uv run pytest school_diary/diary/tests/features/ --cov=school_diary --cov-report=term -v
```

### Step 4: Git コミット

```bash
git add school_diary/diary/tests/
git commit -m "feat: 全機能テスト実装完了（03-features.md完全カバー）

- 28テスト → 48テスト（20テスト追加）
- カバー率41% → 100%
- システム共通: 2テスト
- 認証関連: 6テスト
- 担任アクション: 6テスト
- 学年主任・校長・管理者: 6テスト"

git push origin main
```

---

## 📚 参考資料

### URL名の確認方法
```bash
# URLパターン一覧表示
uv run python manage.py show_urls | grep diary
```

### モデルインポート
```python
from school_diary.diary.models import (
    DiaryEntry,
    ClassRoom,
    TeacherNote,
    TeacherNoteReadStatus,
    DailyAttendance,
    ActionStatus,
)
```

### リバースURL例
```python
reverse("account_logout")                           # ログアウト
reverse("account_change_password")                  # パスワード変更
reverse("account_reset_password")                   # パスワードリセット
reverse("health_check")                             # ヘルスチェック
reverse("about")                                    # About
reverse("diary:teacher_mark_action_completed", kwargs={"diary_id": 1})
reverse("diary:teacher_add_note", kwargs={"student_id": 1})
reverse("diary:teacher_edit_note", kwargs={"note_id": 1})
reverse("diary:teacher_delete_note", kwargs={"note_id": 1})
reverse("diary:mark_shared_note_read", kwargs={"note_id": 1})
reverse("diary:teacher_save_attendance")
reverse("diary:grade_overview")
reverse("diary:school_overview")
```

---

## ⚠️ 既知の問題

### SQLite互換性エラー
**症状**: `sqlite3.OperationalError: near "[]": syntax error`

**原因**: PostgreSQL専用のArrayFieldがSQLiteで動作しない

**解決策**: CI/CDではPostgreSQLを使用（.gitlab-ci.ymlで設定済み）

**ローカルテスト**:
```bash
# SQLiteで動作確認（一部機能制限）
DATABASE_URL="sqlite:///test.db" uv run pytest ...

# PostgreSQLで完全テスト（Docker使用）
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=test postgres:16-alpine
DATABASE_URL="postgres://postgres:test@localhost:5432/test_db" uv run pytest ...
```

---

## 📊 進捗確認チェックリスト

### Phase 2: Full Coverage（目標48テスト）

- [ ] test_system_features.py 作成（2テスト）
  - [ ] SYS-001: ヘルスチェック
  - [ ] SYS-003: About

- [ ] test_auth_features.py 追加（6テスト）
  - [ ] AUTH-002: ログアウト
  - [ ] AUTH-003: パスワード変更
  - [ ] AUTH-004: パスワードリセット要求
  - [ ] AUTH-005: リセットメール送信完了
  - [ ] AUTH-007: パスワード変更完了

- [ ] test_teacher_actions.py 追加（6テスト）
  - [ ] TEA-ACT-002: 対応完了処理
  - [ ] TEA-ACT-003: メモ追加
  - [ ] TEA-ACT-004: メモ編集
  - [ ] TEA-ACT-005: メモ削除
  - [ ] TEA-ACT-006: 共有メモ既読
  - [ ] TEA-ACT-007: 出席保存

- [ ] test_grade_school_leader_features.py 作成（6テスト）
  - [ ] GRD-001: 学年統計（2テスト）
  - [ ] SCH-001: 学校統計（2テスト）
  - [ ] ADM-001: 管理画面（2テスト）

- [ ] conftest.py に追加Fixture（必要に応じて）
  - [ ] teacher_note
  - [ ] daily_attendance

- [ ] 全テスト実行・検証
  - [ ] `pytest --collect-only` でテスト数確認（48件）
  - [ ] ローカルテスト実行
  - [ ] Git コミット & Push
  - [ ] GitLab CI/CD 成功確認

---

## 🎯 完了条件

1. ✅ 48テスト実装完了
2. ✅ 03-features.md 全29機能カバー（100%）
3. ✅ GitLab CI/CD 成功（PostgreSQL環境）
4. ✅ カバレッジレポート生成

---

**作成日**: 2025-10-24
**推定所要時間**: 2-3時間
**次のセッションでの開始手順**: このファイルを読む → Step 1から順次実装
