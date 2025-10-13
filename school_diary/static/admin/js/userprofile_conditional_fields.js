/**
 * UserProfile管理画面: 役割に応じてmanaged_gradeフィールドを動的に表示/非表示
 *
 * 目的: 認知負荷の軽減（学年主任以外のユーザーには「管理学年」フィールドを表示しない）
 * UI/UXベストプラクティス: Progressive Disclosure (段階的開示)
 *
 * 【注意】このファイルは現在未使用です（2025-10-14）
 * 理由: 現在のラベル・help_text・バリデーションによる改善で実用上十分と判断
 * 将来、より高度なUI/UXが必要になった場合に、admin.pyに以下を追加してください:
 *
 *   class Media:
 *       js = ('admin/js/userprofile_conditional_fields.js',)
 */
(function($) {
    'use strict';

    $(document).ready(function() {
        // UserProfileのroleフィールドを探す
        // InlineフォームのIDパターン: id_profile-0-role
        const $roleField = $('#id_profile-0-role');

        if ($roleField.length === 0) {
            // フィールドが見つからない場合は何もしない
            return;
        }

        // managed_gradeフィールドの親要素（.form-row）を取得
        const $managedGradeRow = $('#id_profile-0-managed_grade').closest('.form-row');

        /**
         * roleの値に応じてmanaged_gradeフィールドの表示/非表示を切り替える
         */
        function toggleManagedGradeField() {
            const selectedRole = $roleField.val();

            if (selectedRole === 'grade_leader') {
                // 学年主任の場合: フィールドを表示
                $managedGradeRow.show();
            } else {
                // それ以外の場合: フィールドを非表示＆値をクリア
                $managedGradeRow.hide();
                $('#id_profile-0-managed_grade').val('');
            }
        }

        // 初回実行（ページロード時 - 既存ユーザーの編集時に対応）
        toggleManagedGradeField();

        // role選択変更時に実行（新規ユーザー作成時の動的切り替え）
        $roleField.on('change', toggleManagedGradeField);
    });
})(django.jQuery);
