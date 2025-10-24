# 機能テスト計画書（Functional Test Plan）

> **対象システム**: 連絡帳管理システム（school_diary）
> **バージョン**: v0.3.0-map
> **作成日**: 2025-10-23
> **テストレベル**: System Test（システムテスト）
> **テスト種類**: Functional Test（機能テスト）

---

## 目的

本ドキュメントは、連絡帳管理システムの機能単位での動作確認計画を定義する。
Risk-Based Testing手法により、Critical 10機能（20ケース）+ High 10機能（10ケース）= 30ケースを実施する。

---

## スコープ

### テスト対象（In Scope）

- ✅ Critical 10機能の正常系・異常系
- ✅ High 10機能の正常系
- ✅ ブラウザでの実際の動作確認
- ✅ ロールベースアクセス制御の確認

### テスト対象外（Out of Scope）

- ❌ Medium/Low優先度の機能（時間制約により省略）
- ❌ パフォーマンステスト（別途実施）
- ❌ セキュリティテスト（別途実施）
- ❌ スマホ/タブレット対応（Phase 2で対応）

---

## テストケース一覧（30ケース）

### Critical（10機能、20ケース）

| TC ID | 機能ID | 機能名 | テストケース | Priority | 想定時間 | 詳細 |
|-------|--------|--------|-------------|----------|---------|------|
| TC-AUTH-001-01 | AUTH-001 | ログイン | 正しい認証情報でログイン成功 | Critical | 5分 | [critical-test-cases.md](../cases/critical-test-cases.md#tc-auth-001-01) |
| TC-AUTH-001-02 | AUTH-001 | ログイン | 間違ったパスワードでログイン失敗 | Critical | 5分 | [critical-test-cases.md](../cases/critical-test-cases.md#tc-auth-001-02) |
| TC-SYS-002-01 | SYS-002 | ロールベースリダイレクト | 生徒ログイン→生徒ダッシュボード | Critical | 5分 | [critical-test-cases.md](../cases/critical-test-cases.md#tc-sys-002-01) |
| TC-SYS-002-02 | SYS-002 | ロールベースリダイレクト | 管理者ログイン→管理画面 | Critical | 5分 | [critical-test-cases.md](../cases/critical-test-cases.md#tc-sys-002-02) |
| TC-STU-002-01 | STU-002 | 連絡帳作成 | 連絡帳新規作成成功 | Critical | 10分 | [critical-test-cases.md](../cases/critical-test-cases.md#tc-stu-002-01) |
| TC-STU-002-02 | STU-002 | 連絡帳作成 | 1日2件目の作成失敗（unique制約） | Critical | 5分 | [critical-test-cases.md](../cases/critical-test-cases.md#tc-stu-002-02) |
| TC-TEA-001-01 | TEA-001 | 担任ダッシュボード | Inbox Pattern表示確認（6カテゴリ） | Critical | 10分 | [critical-test-cases.md](../cases/critical-test-cases.md#tc-tea-001-01) |
| TC-TEA-001-02 | TEA-001 | 担任ダッシュボード | P0アラート表示確認（3日連続低下） | Critical | 10分 | [critical-test-cases.md](../cases/critical-test-cases.md#tc-tea-001-02) |
| TC-TEA-ACT-001-01 | TEA-ACT-001 | 既読処理 | 既読処理成功、反応追加 | Critical | 10分 | [critical-test-cases.md](../cases/critical-test-cases.md#tc-tea-act-001-01) |
| TC-TEA-ACT-001-02 | TEA-ACT-001 | 既読処理 | 他クラスの連絡帳は既読不可 | Critical | 5分 | [critical-test-cases.md](../cases/critical-test-cases.md#tc-tea-act-001-02) |
| TC-ADM-001-01 | ADM-001 | 管理画面 | ユーザー新規作成 | Critical | 10分 | [critical-test-cases.md](../cases/critical-test-cases.md#tc-adm-001-01) |
| TC-ADM-001-02 | ADM-001 | 管理画面 | クラス作成・生徒配置 | Critical | 10分 | [critical-test-cases.md](../cases/critical-test-cases.md#tc-adm-001-02) |
| TC-STU-001-01 | STU-001 | 生徒ダッシュボード | 過去7日分表示確認 | Critical | 5分 | [critical-test-cases.md](../cases/critical-test-cases.md#tc-stu-001-01) |
| TC-STU-001-02 | STU-001 | 生徒ダッシュボード | 未提出リマインダー表示 | Critical | 5分 | [critical-test-cases.md](../cases/critical-test-cases.md#tc-stu-001-02) |
| TC-TEA-003-01 | TEA-003 | 生徒詳細 | 生徒の連絡帳履歴表示 | Critical | 10分 | [critical-test-cases.md](../cases/critical-test-cases.md#tc-tea-003-01) |
| TC-TEA-003-02 | TEA-003 | 生徒詳細 | 担任メモ表示 | Critical | 5分 | [critical-test-cases.md](../cases/critical-test-cases.md#tc-tea-003-02) |
| TC-GRD-001-01 | GRD-001 | 学年統計 | クラス比較表示 | Critical | 10分 | [critical-test-cases.md](../cases/critical-test-cases.md#tc-grd-001-01) |
| TC-GRD-001-02 | GRD-001 | 学年統計 | 学年共有アラート表示 | Critical | 10分 | [critical-test-cases.md](../cases/critical-test-cases.md#tc-grd-001-02) |
| TC-SCH-001-01 | SCH-001 | 学校統計 | 学校全体統計表示 | Critical | 10分 | [critical-test-cases.md](../cases/critical-test-cases.md#tc-sch-001-01) |
| TC-SCH-001-02 | SCH-001 | 学校統計 | 学級閉鎖判断データ表示 | Critical | 10分 | [critical-test-cases.md](../cases/critical-test-cases.md#tc-sch-001-02) |

**Critical小計**: 20ケース、合計155分（約2.6時間）

### High（10機能、10ケース）

| TC ID | 機能ID | 機能名 | テストケース | Priority | 想定時間 | 詳細 |
|-------|--------|--------|-------------|----------|---------|------|
| TC-TEA-ACT-003-01 | TEA-ACT-003 | 担任メモ追加 | 学年共有メモ作成成功 | High | 10分 | [high-test-cases.md](../cases/high-test-cases.md#tc-tea-act-003-01) |
| TC-TEA-002-01 | TEA-002 | クラス健康ダッシュボード | 7日/14日ヒートマップ表示 | High | 10分 | [high-test-cases.md](../cases/high-test-cases.md#tc-tea-002-01) |
| TC-STU-003-01 | STU-003 | 連絡帳編集 | 既読前に編集成功 | High | 10分 | [high-test-cases.md](../cases/high-test-cases.md#tc-stu-003-01) |
| TC-TEA-ACT-002-01 | TEA-ACT-002 | 対応完了処理 | 対応完了処理成功 | High | 10分 | [high-test-cases.md](../cases/high-test-cases.md#tc-tea-act-002-01) |
| TC-TEA-ACT-007-01 | TEA-ACT-007 | 出席記録保存 | 欠席記録保存成功 | High | 10分 | [high-test-cases.md](../cases/high-test-cases.md#tc-tea-act-007-01) |
| TC-STU-004-01 | STU-004 | 連絡帳履歴 | 過去30日分表示 | High | 5分 | [high-test-cases.md](../cases/high-test-cases.md#tc-stu-004-01) |
| TC-TEA-ACT-004-01 | TEA-ACT-004 | メモ編集 | 担任メモ編集成功 | High | 10分 | [high-test-cases.md](../cases/high-test-cases.md#tc-tea-act-004-01) |
| TC-TEA-ACT-005-01 | TEA-ACT-005 | メモ削除 | 担任メモ削除成功 | High | 10分 | [high-test-cases.md](../cases/high-test-cases.md#tc-tea-act-005-01) |
| TC-TEA-ACT-006-01 | TEA-ACT-006 | 共有メモ既読 | 学年共有メモ既読処理 | High | 10分 | [high-test-cases.md](../cases/high-test-cases.md#tc-tea-act-006-01) |
| TC-AUTH-003-01 | AUTH-003 | パスワード変更 | 初回ログイン時強制変更 | High | 10分 | [high-test-cases.md](../cases/high-test-cases.md#tc-auth-003-01) |

**High小計**: 10ケース、合計95分（約1.6時間）

---

## 合計

- **総ケース数**: 30ケース
- **想定テスト時間**: 4.2時間（Critical 2.6h + High 1.6h）
- **記録・バグ修正時間**: 2時間
- **合計**: 6.2時間

---

## テスト環境

### 本番環境

- **URL**: https://d2wk3j2pacp33b.cloudfront.net
- **用途**: 機能テスト実施
- **ブラウザ**: Chrome最新版（推奨）

### ローカル環境

- **URL**: http://localhost:8000
- **用途**: バグ修正後の再テスト
- **起動**: `dc up -d`

### テストアカウント

詳細: [09-test-accounts.md](../../09-test-accounts.md)

| ロール | メールアドレス | パスワード |
|--------|--------------|-----------|
| 管理者 | admin@example.com | password123 |
| 学年主任 | grade_leader@example.com | password123 |
| 担任 | teacher_1_a@example.com | password123 |
| 生徒 | student_1_a_01@example.com | password123 |

---

## テスト実行手順

### 1. 事前準備

```bash
# Docker環境起動（ローカルテストの場合）
dc up -d

# 本番環境確認
curl -I https://d2wk3j2pacp33b.cloudfront.net/health/
```

### 2. テスト実施

1. テストケースドキュメントを開く（critical-test-cases.md or high-test-cases.md）
2. TC IDに従って順番に実行
3. 各ステップの結果を記録（Pass/Fail/Blocked）
4. スクリーンショットを取得（証跡）
5. バグ発見時はKnown Issueとして記録

### 3. 結果記録

テスト完了後、`results/functional-test-result-YYYYMMDD.md`に記録:

```markdown
| TC ID | Status | Actual Result | Evidence |
|-------|--------|---------------|----------|
| TC-AUTH-001-01 | ✅ Pass | ログイン成功 | ss-001.png |
| TC-AUTH-001-02 | ❌ Fail | エラーメッセージ表示されず | ss-002.png |
```

---

## 完了基準（Definition of Done）

- [ ] Critical 20ケース実行完了
- [ ] High 10ケース実行完了
- [ ] 各ケースのPass/Fail記録済み
- [ ] スクリーンショット30枚取得済み
- [ ] Known Issues記録済み（3-5件想定）
- [ ] functional-test-result.md作成完了

---

## スケジュール

### Day 2（8時間）

- 09:00-12:00: Critical 10ケース実行（3時間）
- 13:00-15:00: Critical 10ケース実行（2時間）
- 15:00-17:00: High 10ケース実行（2時間）
- 17:00-18:00: 記録整理

### Day 3（4時間）

- 09:00-11:00: バグ修正・再テスト
- 11:00-13:00: 記録完成、スクリーンショット整理

---

## リスクと対応策

| リスク | 確率 | 影響 | 対応策 |
|-------|------|------|--------|
| バグ多数発見 | High | テスト時間延長 | Known Issuesとして記録。Critical以外は修正せず |
| 本番環境ダウン | Low | テスト実施不可 | ローカル環境に切り替え |
| 時間オーバー | Medium | High未完了 | Critical完了を優先 |

---

## 関連ドキュメント

- [test-strategy.md](../test-strategy.md) - テスト戦略
- [critical-test-cases.md](../cases/critical-test-cases.md) - Criticalテストケース詳細
- [high-test-cases.md](../cases/high-test-cases.md) - Highテストケース詳細
- [03-features.md](../../03-features.md) - 機能一覧

---

**作成日**: 2025-10-23
**最終更新**: 2025-10-23
**作成者**: hirok
**バージョン**: 1.0
