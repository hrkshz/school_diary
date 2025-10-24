# Test Strategy - 連絡帳管理システム

> **Based on**: 03-features.md
> **Approach**: Specification by Example (Feature-based Testing)
> **Last Updated**: 2025-10-24

---

## 🎯 Test Philosophy

このプロジェクトは**機能ベーステスト**を採用しています。

**原則**:
1. **Traceability（追跡可能性）**: 各テストは03-features.mdの機能IDに対応
2. **Clarity（明確性）**: テスト名から機能とシナリオが分かる
3. **Maintainability（保守性）**: 機能追加時はテストファイルに追記

---

## 📁 Directory Structure

```
school_diary/diary/tests/
├── README.md                     # このファイル
├── conftest.py                   # 共通フィクスチャ
└── features/                     # 機能テスト
    ├── test_auth_features.py     # AUTH-001〜007
    ├── test_student_features.py  # STU-001〜004
    ├── test_teacher_features.py  # TEA-001〜003
    └── test_teacher_actions.py   # TEA-ACT-001〜009
```

---

## 🔍 Traceability Matrix

| Test File | Feature IDs | Test Count | Priority |
|-----------|-------------|------------|----------|
| test_auth_features.py | AUTH-001, SYS-002 | 8 | P0 (Critical) |
| test_student_features.py | STU-001〜004 | 10 | P0 (Critical) |
| test_teacher_features.py | TEA-001〜003 | 12 | P0 (Critical) |
| test_teacher_actions.py | TEA-ACT-001〜009 | 10 | P1 (High) |

**合計**: 約40テスト（Critical Pathのみ）

---

## 📝 Naming Convention

### ファイル名
```
test_{role}_{category}.py
```

### クラス名
```python
class Test{FeatureID}{Description}:
    """STU-002: 連絡帳作成機能のテスト"""
```

### メソッド名
```python
def test_{feature_id}_{scenario}_{expected}(self):
    """
    Given: 前提条件
    When: 実行アクション
    Then: 期待結果
    """
```

### 例
```python
class TestSTU002DiaryCreation:
    def test_stu002_create_valid_entry_success(self):
        """正常系: 連絡帳作成成功"""

    def test_stu002_create_duplicate_date_rejected(self):
        """異常系: 一日一件制約違反"""
```

---

## 🧪 Test Pattern (Given-When-Then)

```python
def test_stu002_create_valid_entry_success(self, student_user, classroom, client):
    """
    Given: ログイン済み生徒ユーザー
    When: 有効な連絡帳データを送信
    Then: 連絡帳が作成され、ダッシュボードにリダイレクト
    """
    # Arrange (Given)
    client.force_login(student_user)

    # Act (When)
    response = client.post(reverse("diary:create"), {
        "health_condition": 4,
        "mental_condition": 4,
        "reflection": "今日は楽しかった",
    })

    # Assert (Then)
    assert response.status_code == 302
    assert DiaryEntry.objects.filter(student=student_user).count() == 1
```

---

## 🚀 Running Tests

### CI/CD
```bash
# GitLab CI/CD (自動実行)
pytest school_diary/diary/tests/features/ --cov=school_diary
```

### ローカル開発
```bash
# 全テスト実行
pytest school_diary/diary/tests/ -v

# 特定機能のみ
pytest school_diary/diary/tests/features/test_student_features.py -v

# 特定テストのみ
pytest school_diary/diary/tests/features/test_student_features.py::TestSTU002DiaryCreation -v
```

---

## 📊 Coverage Target

| Layer | Target |
|-------|--------|
| Critical Path | 100% |
| Main Features | 80% |
| Edge Cases | 60% |

---

## 🔄 Test Maintenance

### 新機能追加時
1. 03-features.mdに機能ID追加
2. 対応するtest_*.pyに テストケース追加
3. Traceability Matrix更新

### バグ修正時
1. バグを再現するテストを追加（Red）
2. バグ修正（Green）
3. リファクタリング（Refactor）

---

**Last Updated**: 2025-10-24
**Test Framework**: pytest + pytest-django
**Design Pattern**: Specification by Example
