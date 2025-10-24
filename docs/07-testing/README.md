# テストドキュメント

このディレクトリには、連絡帳管理システムの品質保証に関するドキュメントが含まれています。

---

## 現在の品質スコア（2025-10-25）

| 指標 | 値 |
|-----|---|
| 総合評価 | A (90/100) |
| テスト合格率 | 100% (53/53) |
| 機能カバレッジ | 92% (24/26) |
| セキュリティテスト | 96% (40/42) |
| OWASP Top 10 | 80% (7/10) |
| 判定 | デプロイ可能 |

詳細: [test-summary.md](test-summary.md)

---

## 📁 ディレクトリ構成

```
testing/
├── README.md                              # このファイル（テストドキュメント索引）
├── test-summary.md                        # ⭐ テスト実行サマリー（一枚紙ダッシュボード）
├── traceability-matrix-feature-tests.md   # ⭐ 機能テストトレーサビリティマトリックス
├── traceability-matrix.md                 # 単体テストトレーサビリティマトリックス
├── plans/                                 # テスト計画書
│   └── smoke-test-plan.md
├── results/                               # テスト結果レポート
│   ├── 20251025-qa-test-fix-report.md     # ⭐ QA修正レポート（21件失敗→53件合格）
│   ├── 20251025-quality-metrics.md        # ⭐ 品質メトリクス（A評価: 90/100）
│   ├── 20251023-*.md                      # 単体テスト結果
│   └── 20251022-smoke-test-result.md
└── screenshots/                           # テスト実施時のスクリーンショット
    └── YYYYMMDD/
```

**⭐ = 2025-10-25 QA Phase完了時に作成/更新**

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

### ⭐ 必読ドキュメント（QA Phase完了時）

| ドキュメント | 目的 | 対象読者 |
|-----------|------|---------|
| [test-summary.md](test-summary.md) | **一枚紙ダッシュボード**（総合評価、リリース判定） | PM、評価者、経営層 |
| [results/20251025-qa-test-fix-report.md](results/20251025-qa-test-fix-report.md) | **QA修正レポート**（21件失敗→53件合格の詳細） | QA、開発者 |
| [results/20251025-quality-metrics.md](results/20251025-quality-metrics.md) | **品質メトリクス**（A評価: 90/100、OWASP Top 10） | PM、セキュリティ担当 |
| [traceability-matrix-feature-tests.md](traceability-matrix-feature-tests.md) | **機能テストトレーサビリティ**（要件→テストのマッピング） | QA、開発者 |

### トレーサビリティマトリックス

| ドキュメント | 対象テスト | カバレッジ | 状態 |
|-----------|----------|----------|------|
| [traceability-matrix-feature-tests.md](traceability-matrix-feature-tests.md) | 機能テスト（Feature Tests） | 92% (24/26機能、53テスト) | ✅ 100%合格 |
| [traceability-matrix.md](traceability-matrix.md) | 単体テスト（Unit Tests） | 76% (13/17要件) | ✅ 合格 |

### テスト計画書

| ドキュメント | 目的 | 対象 |
|-----------|------|------|
| [plans/smoke-test-plan.md](plans/smoke-test-plan.md) | バグ修正後の基本動作確認 | 全ロールのログイン・リダイレクト |

### テスト結果（時系列）

| 実施日 | ドキュメント | 結果 |
|-------|------------|------|
| **2025-10-25** | **[20251025-qa-test-fix-report.md](results/20251025-qa-test-fix-report.md)** | **✅ 53/53合格（100%）、CI/CD修正完了** |
| **2025-10-25** | **[20251025-quality-metrics.md](results/20251025-quality-metrics.md)** | **✅ A評価（90/100）、Release Ready** |
| 2025-10-23 | [20251023-s02-requirement-verification.md](results/20251023-s02-requirement-verification.md) | ✅ S-02要件実装済み証明、10テスト全PASS |
| 2025-10-23 | [20251023-test-improvement-final-report.md](results/20251023-test-improvement-final-report.md) | ⚠️ 57%カバレッジ、S-02 Gap解決、改善計画策定 |
| 2025-10-23 | [20251023-unit-test-quality-review.md](results/20251023-unit-test-quality-review.md) | ⚠️ C+ (56%カバレッジ、要改善) |
| 2025-10-23 | [20251023-unit-test-result.md](results/20251023-unit-test-result.md) | ✅ 150 passed |
| 2025-10-22 | [20251022-smoke-test-result.md](results/20251022-smoke-test-result.md) | ✅ Smoke Test完了 |

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

## 📊 テストカバレッジ（2025-10-25）

### Feature Test カバレッジ（機能テスト）

```
┌─────────────────────────────────────────────────────────┐
│ 生徒機能（STU）          ████████████████  8/8   (100%) │
│ 担任アクション（TEA-ACT）  ███████████████ 23/23 (100%) │
│ 学年主任（GRD）          ████████████████  2/2   (100%) │
│ 校長/教頭（SCH）         ████████████████  2/2   (100%) │
│ 認証（AUTH）             ████████████████  9/9   (100%) │
│ ホームリダイレクト（SYS-002）████████████  6/6   (100%) │
│ 管理画面（ADM）          ████████████████  2/2   (100%) │
│                                                         │
│ 担任ダッシュボード（TEA） ░░░░░░░░░░░░░░  0/2   (0%)   │
└─────────────────────────────────────────────────────────┘

凡例: █ 合格  ░ 未テスト
```

**総合**: 92% (24/26機能)、テスト合格率: 100% (53/53)

**詳細**: [traceability-matrix-feature-tests.md](traceability-matrix-feature-tests.md)

### Unit Test カバレッジ（単体テスト）

```bash
# カバレッジ測定
dj coverage run -m pytest
dj coverage report
```

**総合**: 76% (13/17要件)、テスト合格率: 100% (150/150)

**詳細**: [traceability-matrix.md](traceability-matrix.md)

### System Test カバレッジ（システムテスト）

| 機能カテゴリ | テスト済み | 未テスト |
|------------|----------|---------|
| 認証・ログイン | ✅ 100% | - |
| 連絡帳管理 | ✅ 100% | TEA-001/002（表示のみ） |
| ユーザー管理 | ✅ 100% | - |
| 担任アクション | ✅ 100% | - |
| 学年主任・校長/教頭 | ✅ 100% | - |

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

## 📞 Contact

**QA Team**: QA Lead
**承認者**: QA Manager
**問い合わせ**: QAチーム

---

**作成日**: 2025-10-22
**最終更新**: 2025-10-25（QA Phase完了、総合評価A）
**管理者**: QAチーム
**ステータス**: デプロイ可能
