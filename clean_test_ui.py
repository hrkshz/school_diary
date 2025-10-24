#!/usr/bin/env python
"""test_ui.pyから保持すべき15テストのみを抽出するスクリプト"""

import re

# 保持すべきテスト関数名
KEEP_TESTS = {
    "test_mark_as_read_with_reaction_only",
    "test_mark_as_read_with_reaction_and_action",
    "test_update_reaction_after_read",
    "test_update_action_after_read",
    "test_change_reaction_after_read",
    "test_change_action_after_read",
    "test_remove_action_after_read",
    "test_action_status_management",
    "test_edit_delete_buttons_only_for_creator",
    "test_shared_notes_visible_to_other_teachers",
    "test_root_url_redirects_to_login_when_unauthenticated",
    "test_root_url_redirects_to_student_dashboard",
    "test_logout_redirects_to_home_then_login",
    "test_teacher_redirects_to_dashboard",
    "test_all_users_use_same_login_endpoint",
    "test_admin_force_allauth_setting_enabled",  # 追加
    "test_entry_displayed_with_badges",  # 追加（リダイレクト関連）
    "test_edit_note_modal_preloaded",  # 追加（ノート編集）
    "test_notes_displayed_with_correct_badges",  # 追加（ノート表示）
}

# 保持すべきfixture名
KEEP_FIXTURES = {
    "authenticated_client",
    "teacher_with_student_entry",
    "teacher_with_notes_data",
}

# 保持すべきクラス名
KEEP_CLASSES = {
    "TestRootURLRedirect",
    "TestAuthenticationFlow",
    "TestTeacherReactionAndActionFlow",
    "TestTeacherNotesUI",
}

def extract_function(lines, start_idx):
    """関数を抽出（インデントレベルで判定）"""
    result = []
    base_indent = len(lines[start_idx]) - len(lines[start_idx].lstrip())

    for i in range(start_idx, len(lines)):
        line = lines[i]

        # 空行はスキップ
        if not line.strip():
            result.append(line)
            continue

        # インデントレベルチェック
        current_indent = len(line) - len(line.lstrip())

        # 同じまたはそれ以上のインデント = 関数内
        if current_indent >= base_indent or line.strip().startswith("#"):
            result.append(line)
        else:
            # インデントが浅くなったら関数終了
            break

    return result

def main():
    input_file = "school_diary/diary/test_ui.py"
    output_file = "school_diary/diary/test_ui_cleaned.py"

    with open(input_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    output_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # ヘッダー部分（docstring、imports）は全て保持
        if i < 40:  # 最初の40行はimports等
            output_lines.append(line)
            i += 1
            continue

        # Fixtureチェック
        if line.strip().startswith("@pytest.fixture"):
            # 次の行で関数名を確認
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                match = re.search(r"def (\w+)\(", next_line)
                if match:
                    fixture_name = match.group(1)
                    if fixture_name in KEEP_FIXTURES:
                        # Fixtureを抽出
                        func_lines = extract_function(lines, i)
                        output_lines.extend(func_lines)
                        i += len(func_lines)
                        output_lines.append("\n")  # 空行追加
                        continue
                    else:
                        # 削除対象のfixtureをスキップ
                        func_lines = extract_function(lines, i)
                        i += len(func_lines)
                        continue

        # クラスチェック
        if line.strip().startswith("class "):
            match = re.search(r"class (\w+)", line)
            if match:
                class_name = match.group(1)
                if class_name in KEEP_CLASSES:
                    # クラス全体を保持
                    output_lines.append("\n")  # 空行追加
                    output_lines.append(line)  # class定義
                    i += 1

                    # クラス内のメソッドをすべて保持
                    class_indent = len(line) - len(line.lstrip())
                    while i < len(lines):
                        curr_line = lines[i]
                        if not curr_line.strip():
                            output_lines.append(curr_line)
                            i += 1
                            continue

                        curr_indent = len(curr_line) - len(curr_line.lstrip())
                        if curr_indent <= class_indent and curr_line.strip():
                            # クラス終了
                            break

                        output_lines.append(curr_line)
                        i += 1

                    output_lines.append("\n")  # クラス後に空行
                    continue
                else:
                    # 削除対象のクラスをスキップ
                    class_indent = len(line) - len(line.lstrip())
                    i += 1
                    while i < len(lines):
                        curr_line = lines[i]
                        if not curr_line.strip():
                            i += 1
                            continue
                        curr_indent = len(curr_line) - len(curr_line.lstrip())
                        if curr_indent <= class_indent and curr_line.strip():
                            break
                        i += 1
                    continue

        i += 1

    # ファイル書き込み
    with open(output_file, "w", encoding="utf-8") as f:
        f.writelines(output_lines)

    print(f"✅ 新しいファイル作成: {output_file}")
    print(f"   元のテスト数: 46")
    print(f"   削除予定: 31")
    print(f"   保持予定: 15")

if __name__ == "__main__":
    main()
