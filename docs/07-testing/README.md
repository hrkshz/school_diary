# テストドキュメント

このディレクトリには、連絡帳管理システムの品質保証に関するドキュメントが含まれています。

## 📁 ディレクトリ構成

```
testing/
├── README.md              # このファイル
├── plans/                 # テスト計画書
│   └── smoke-test-plan.md
├── results/              # テスト結果レポート
│   └── YYYYMMDD-*.md
└── screenshots/          # テスト実施時のスクリーンショット
    └── YYYYMMDD/
```

## 🎯 テスト戦略

### テストレベル

1. **Unit Test（単体テスト）**
   - ツール: pytest
   - 対象: 個別の関数・メソッド
   - 自動化: ✅ 完了
   - 実行: `dj pytest`

2. **Integration Test（統合テスト）**
   - ツール: pytest + Django TestCase
   - 対象: 複数コンポーネントの連携
   - 自動化: ✅ 完了
   - 実行: `dj pytest`

3. **System Test（システムテスト）**
   - ツール: 手動テスト（将来的にPlaywright自動化）
   - 対象: ブラウザでの実際の動作確認
   - 自動化: ⏳ 計画中
   - 実行: 手動実施

4. **Acceptance Test（受け入れテスト）**
   - ツール: 手動テスト
   - 対象: ビジネス要件の充足確認
   - 実行: ステークホルダーと実施

### テスト種類

- **Smoke Test（スモークテスト）**: 基本機能の動作確認（10-15分）
- **Regression Test（回帰テスト）**: 既存機能が壊れていないか確認
- **Critical Path Test**: 最重要ビジネスフローの検証

## 📝 テストドキュメント一覧

### テスト計画書

| ドキュメント | 目的 | 対象 |
|-----------|------|------|
| [smoke-test-plan.md](plans/smoke-test-plan.md) | バグ修正後の基本動作確認 | 全ロールのログイン・リダイレクト |

### テスト結果

| 実施日 | ドキュメント | 結果 |
|-------|------------|------|
| 2025-10-23 | [20251023-s02-requirement-verification.md](results/20251023-s02-requirement-verification.md) | ✅ S-02要件実装済み証明、10テスト全PASS |
| 2025-10-23 | [20251023-test-improvement-final-report.md](results/20251023-test-improvement-final-report.md) | ⚠️ 57%カバレッジ、S-02 Gap解決、改善計画策定 |
| 2025-10-23 | [20251023-unit-test-quality-review.md](results/20251023-unit-test-quality-review.md) | ⚠️ C+ (56%カバレッジ、要改善) |
| 2025-10-23 | [20251023-unit-test-result.md](results/20251023-unit-test-result.md) | ✅ 150 passed |
| 2025-10-22 | [20251022-smoke-test-result.md](results/20251022-smoke-test-result.md) | - |

## 🚀 テスト実施手順

### 1. テスト計画確認

```bash
# テスト計画書を確認
cat docs/testing/plans/smoke-test-plan.md
```

### 2. テスト環境準備

```bash
# Docker環境起動
dc up -d

# テストユーザー作成（未実施の場合）
dj setup_dev
```

### 3. テスト実施

- テスト計画書に従って手動テストを実施
- 各テストケースの結果をチェック
- スクリーンショットを`screenshots/YYYYMMDD/`に保存

### 4. テスト結果記録

- `results/YYYYMMDD-*-result.md`に結果を記録
- Pass/Fail/Blockedを明記
- バグ発見時はGitHub/GitLab Issueに登録

## 📊 テストカバレッジ

### Unit Test カバレッジ

```bash
# カバレッジ測定
dj coverage run -m pytest
dj coverage report
```

現在のカバレッジ: データなし（要測定）

### System Test カバレッジ

| 機能カテゴリ | テスト済み | 未テスト |
|------------|----------|---------|
| 認証・ログイン | ✅ | - |
| 連絡帳管理 | ⏳ | - |
| ユーザー管理 | ⏳ | - |

## 🐛 バグレポート

バグ発見時は以下の情報を記録：

1. **再現手順**: 1, 2, 3...
2. **期待結果**: 〇〇が表示される
3. **実際の結果**: ××が表示された
4. **スクリーンショット**: `screenshots/YYYYMMDD/bug-NNN.png`
5. **環境情報**: ブラウザ、OS、バージョン
6. **重要度**: Critical/High/Medium/Low

## 📚 参考資料

- [pytest公式ドキュメント](https://docs.pytest.org/)
- [Django Testing](https://docs.djangoproject.com/en/5.0/topics/testing/)
- [Playwright](https://playwright.dev/) - 将来の自動化用

---

**作成日**: 2025-10-22
**最終更新**: 2025-10-22
**管理者**: QAチーム
