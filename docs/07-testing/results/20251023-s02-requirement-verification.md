# S-02要件検証レポート

> **実施日**: 2025-10-23
> **担当**: QA Lead
> **目的**: Critical Gap（S-02要件: 既読後編集不可）の実装状況確認
> **結果**: ✅ 実装済み、テスト追加完了

---

## エグゼクティブサマリー

**結論**: S-02要件は既に実装済み。test_views.py追加でテストカバレッジ達成。

| 項目 | 状態 | 判定 |
|-----|------|------|
| **S-02要件実装** | ✅ 実装済み（views.py:408-436） | 確認完了 |
| **S-02テスト** | ✅ 2テスト追加、全PASS | カバー済み |
| **views.pyカバレッジ** | 40% → 43%（+3%） | ⚠️ まだ低い |
| **総テスト数** | 150 → 160（+10） | ✅ |
| **総合カバレッジ** | 56% → 57%（+1%） | ⚠️ まだ低い |

---

## S-02要件の実装確認

### 要件定義

**S-02**: 連絡帳編集（既読前のみ）

- 既読処理前のエントリーは編集可能
- 既読処理後のエントリーは編集不可

### 実装箇所

**ファイル**: `school_diary/diary/views.py` (DiaryUpdateView)

**コード**:
```python
class DiaryUpdateView(LoginRequiredMixin, UpdateView):
    """連絡帳編集ページ（S-02: 既読前のみ編集可）

    生徒が既読前の連絡帳を編集するページ。
    既読後は過去記録化されるため編集不可。

    セキュリティ:
    - LoginRequiredMixin: 未認証ユーザーをブロック
    - get_queryset(): 自分のエントリーで、かつ未既読のもののみ取得
    """

    model = DiaryEntry
    form_class = DiaryEntryForm
    template_name = "diary/diary_update.html"
    success_url = reverse_lazy("diary:student_dashboard")

    def get_queryset(self):
        """セキュリティ: 自分の未既読エントリーのみ編集可能

        フィルタ条件:
        - student=self.request.user: 自分のエントリーのみ
        - is_read=False: 既読前のみ（is_editable=True）

        既読後または他人のエントリーにアクセスした場合は404エラー。
        """
        return DiaryEntry.objects.filter(
            student=self.request.user,
            is_read=False,  # is_editable = True
        )
```

### セキュリティ制約

**3層防御**:

1. **LoginRequiredMixin**: 未認証ユーザーを/accounts/login/へリダイレクト
2. **student=self.request.user**: 他人のエントリーは取得不可（404）
3. **is_read=False**: 既読後のエントリーは取得不可（404）

**動作**:
- 既読前 + 自分のエントリー → 編集可能（200 OK）
- 既読後 + 自分のエントリー → **404 Not Found**（取得できない）
- 既読前 + 他人のエントリー → **404 Not Found**（取得できない）

**注**: 実装は403 Forbiddenではなく、404 Not Foundを返す設計（Django UpdateViewの仕様）。

---

## テスト追加内容

### test_views.py（10テスト追加）

**ファイル**: `school_diary/diary/tests/test_views.py`

**テスト内訳**:

#### 1. DiaryEntryCreateView（4テスト）

| テスト名 | 目的 | 結果 |
|---------|------|------|
| test_create_entry_success | 正常系: 連絡帳作成成功 | ✅ PASS |
| test_create_entry_validation_error_invalid_health | 異常系: 不正なhealth_condition | ✅ PASS |
| test_create_entry_duplicate_date_error | 異常系: UNIQUE制約エラー | ✅ PASS |
| test_create_entry_unauthenticated_redirect | セキュリティ: 未認証リダイレクト | ✅ PASS |

#### 2. DiaryEntryUpdateView（3テスト）- S-02要件

| テスト名 | 目的 | 結果 |
|---------|------|------|
| test_update_entry_before_read_success | S-02: 既読前は編集可能 | ✅ PASS |
| **test_update_entry_after_read_forbidden** | **S-02: 既読後は編集不可（404）** | ✅ PASS |
| test_update_other_student_entry_forbidden | セキュリティ: 他人のエントリー編集不可 | ✅ PASS |

#### 3. 権限チェック（3テスト）

| テスト名 | 目的 | 結果 |
|---------|------|------|
| test_teacher_can_view_assigned_class_only | 担任は担当クラスのみ閲覧可能 | ✅ PASS |
| test_teacher_cannot_view_other_class | 他クラスの生徒は閲覧不可 | ✅ PASS |
| test_student_can_view_own_entries_only | 生徒は自分のデータのみ閲覧可能 | ✅ PASS |

---

## 重要な学び

### 「前登校日」の正しい扱い

**問題**: 初回テストで全て失敗

**原因**: 連絡帳の`entry_date`は「前登校日」（土日を除く前の学校があった日）だが、テストでは`timezone.now().date()`（今日）を使用していた。

**エラーメッセージ**:
```
記載日は前登校日（2025年10月22日）にしてください。
```

**修正**:
```python
# ❌ 間違い
entry_date = timezone.now().date()

# ✅ 正しい
from school_diary.diary.utils import get_previous_school_day

entry_date = get_previous_school_day(timezone.now().date())
```

**get_previous_school_day()の仕様**:
- 月曜日 → 金曜日（3日前）
- 火〜金曜日 → 前日
- 土曜日 → 金曜日（1日前）
- 日曜日 → 金曜日（2日前）
- 祝日は考慮しない（要件に明記あり）

---

## テスト実行結果

### test_views.py単体

```bash
$ pytest school_diary/diary/tests/test_views.py -v

============================= test session starts ==============================
collected 10 items

school_diary/diary/tests/test_views.py::TestDiaryEntryCreateView::test_create_entry_success PASSED
school_diary/diary/tests/test_views.py::TestDiaryEntryCreateView::test_create_entry_validation_error_invalid_health PASSED
school_diary/diary/tests/test_views.py::TestDiaryEntryCreateView::test_create_entry_duplicate_date_error PASSED
school_diary/diary/tests/test_views.py::TestDiaryEntryCreateView::test_create_entry_unauthenticated_redirect PASSED
school_diary/diary/tests/test_views.py::TestDiaryEntryUpdateView::test_update_entry_before_read_success PASSED
school_diary/diary/tests/test_views.py::TestDiaryEntryUpdateView::test_update_entry_after_read_forbidden PASSED
school_diary/diary/tests/test_views.py::TestDiaryEntryUpdateView::test_update_other_student_entry_forbidden PASSED
school_diary/diary/tests/test_views.py::TestTeacherDashboardPermissions::test_teacher_can_view_assigned_class_only PASSED
school_diary/diary/tests/test_views.py::TestTeacherDashboardPermissions::test_teacher_cannot_view_other_class PASSED
school_diary/diary/tests/test_views.py::TestStudentDashboardPermissions::test_student_can_view_own_entries_only PASSED

======================== 10 passed in 1.06s ==========================
```

### 全体テスト + カバレッジ

```bash
$ pytest --cov=school_diary/diary --cov-report=term-missing:skip-covered

======================== 160 passed in 9.99s ==========================

_______________ coverage: platform linux, python 3.12.11-final-0 _______________

Name                                                                    Stmts   Miss  Cover
-----------------------------------------------------------------------------------------------------
school_diary/diary/views.py                                               527    301    43%
school_diary/diary/forms.py                                               137     73    47%
school_diary/diary/models.py                                              255     12    95%
school_diary/diary/alert_service.py                                        68      2    97%
school_diary/diary/services/teacher_dashboard_service.py                   52      2    96%
-----------------------------------------------------------------------------------------------------
TOTAL                                                                    3015   1299    57%
```

**カバレッジ変化**:
- 総合: 56% → 57%（+1%）
- views.py: 40% → 43%（+3%）

---

## 要件トレーサビリティマトリックス更新

### S-02要件

| 要件ID | 要件名 | テストファイル | テスト名 | カバレッジ | 状態 |
|--------|--------|--------------|---------|----------|------|
| **S-02** | **連絡帳編集（既読前のみ）** | test_views.py | test_update_entry_before_read_success | 既読前編集可能 | ✅ |
| | | test_views.py | test_update_entry_after_read_forbidden | 既読後編集不可（404） | ✅ |
| | | test_views.py | test_update_other_student_entry_forbidden | 他人エントリー編集不可 | ✅ |

**前回状態**: ❌ Critical Gap（テスト不足）
**今回状態**: ✅ 完全カバー（実装済み + テスト3件）

---

## 今後の課題

### views.pyカバレッジ向上

**現状**: 43%（527行中301行未カバー）

**未カバー主要箇所**:
- `get_students_with_consecutive_decline` (77-110行) - 3日連続低下検出
- `TeacherStudentDetailView` (499-565行) - 担任用個別生徒詳細
- `TeacherNoteListView` (690-727行) - 学年共有メモ一覧
- `PasswordChangeViewCustom` (799-1025行) - パスワード変更
- 多数のAJAX APIエンドポイント (1035-1345行)

**改善計画**（最終レポート Phase 3参照）:
1. ビジネスロジック分離（views.py → services/）
2. 分離したサービス層のテスト（100%カバー）
3. views.pyはビューロジックのみテスト（60%目標）

---

## 結論

### S-02要件について

**結論**: ✅ 実装済み、テスト済み

**実装品質**: 高い
- 3層セキュリティ防御（認証、所有者、既読状態）
- Djangoベストプラクティス準拠
- コメントによる仕様明記

**テスト品質**: 十分
- 正常系（既読前編集可能）
- 異常系（既読後編集不可、他人エントリー）
- セキュリティ確認（404エラー）

### 本日の成果

**定量的**:
- Critical Gap解決: 1件
- テスト追加: 10件（全PASS）
- カバレッジ: +1%（views.py +3%）

**定性的**:
- S-02要件実装済み証明
- セキュリティ3層防御の可視化
- 「前登校日」仕様の理解深化

### 次のステップ

Phase 1完了 ✅ → Phase 2へ移行

**Phase 2: テスト品質向上**（1週間、P1）
1. 低価値テスト削除（42件）
2. 重複テスト統合（21件→5件）
3. テスト数: 160 → 97（保守コスト39%削減）

---

**作成日**: 2025-10-23
**作成者**: QA Lead
**レビュー**: 不要（検証報告）
**次回アクション**: Phase 2開始（低価値テスト削除）
