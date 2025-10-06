# kits.approvals - 承認フローシステム

**汎用的な承認ワークフローを提供する再利用可能なDjangoアプリケーション**

## 📚 ドキュメント一覧

### 初心者向けガイド（推奨順）

1. **[01_概要と目的.md](01_概要と目的.md)** (読了時間: 7分)
   - 承認フローシステムとは何か？
   - なぜ必要なのか？
   - 何ができるのか？

2. **[05_使い方ガイド.md](05_使い方ガイド.md)** (読了時間: 20分)
   - コピペで動く実例
   - 9つの実践的な使用例
   - 実際の業務への適用方法

3. **[02_設計思想.md](02_設計思想.md)** (読了時間: 12分)
   - なぜこう設計したのか？
   - 代替案とトレードオフ
   - 設計判断の理由

4. **[03_実装の全体像.md](03_実装の全体像.md)** (読了時間: 10分)
   - ファイル構成と各ファイルの役割
   - データフロー図
   - アーキテクチャ概要

5. **[04_コード解説.md](04_コード解説.md)** (読了時間: 35分)
   - コードを1行ずつ丁寧に解説
   - 実装の意図と設計判断
   - 重要なパターンと技法

6. **[06_よくある質問.md](06_よくある質問.md)** (読了時間: 随時参照)
   - よくあるエラーと対処法
   - FAQ 12件
   - トラブルシューティング

### 実装者向け

7. **[00_実装ログ.md](00_実装ログ.md)**
   - 実装の詳細な記録
   - 技術的な判断の履歴
   - バージョン履歴

## 🚀 クイックスタート

```python
from kits.approvals.models import ApprovalWorkflow
from kits.approvals.services import ApprovalService
from django.contrib.auth.models import Group

# 1. 承認ワークフローを作成
workflow = ApprovalWorkflow.objects.create(
    name="2段階承認",
    default_deadline_hours=48,
)

# 2. 承認ステップを定義
manager_group = Group.objects.get(name="Manager")
workflow.steps.create(
    order=1,
    name="課長承認",
    approver_role=manager_group,
)

# 3. 承認依頼を作成・提出
service = ApprovalService()
request = service.create_request(
    workflow=workflow,
    content_object=your_object,  # 任意のモデルオブジェクト
    requester=user,
)
request = service.submit_request(request)

# 4. 承認する
service.approve_step(
    request=request,
    step=request.current_step,
    approver=manager,
)
```

## ✨ 主な機能

### 1. 汎用的な承認システム
- **GenericForeignKey**: どんなモデルにも承認フローを追加可能
- **再利用性**: 1つのワークフローを複数のモデルで共有

### 2. 柔軟な承認フロー
- **直列承認**: Step1 → Step2 → Step3
- **並列承認**: 3人の承認者のうち2人の承認が必要
- **自動承認**: 申請者が承認者ロールに属している場合は自動承認

### 3. 充実した管理機能
- **期限管理**: デフォルト期限、期限切れチェック
- **リマインダー**: 期限前の自動通知
- **エスカレーション**: 長期間放置された承認の上位者への通知
- **履歴管理**: django-simple-historyによる完全な変更履歴

### 4. 他kitsとの統合
- **kits.notifications**: 承認依頼・完了・リマインダーの通知
- **kits.audit**: 承認アクションの完全な履歴記録

## 📦 実装済みファイル

| ファイル | 行数 | 説明 |
|---------|------|------|
| **models.py** | 371行 | 4つのモデル（Workflow, Step, Request, Action） |
| **services.py** | 440行 | ApprovalService（承認制御ロジック） |
| **tasks.py** | 267行 | Celeryタスク（期限チェック、リマインダー） |
| **admin.py** | 331行 | Django管理画面（4つの管理クラス） |
| **examples.py** | 331行 | 使用例8パターン |
| **signals.py** | 70行 | FSM状態遷移の自動ログ記録 |
| **tests/** | 206行 | ユニットテスト18個（全成功） |
| **合計** | **1,946行** | プロダクション品質の実装 |

## 🎯 使用例

### 例1: 残業申請の2段階承認

```python
# 課長承認 → 部長承認
workflow = ApprovalWorkflow.objects.create(name="残業申請承認フロー")
workflow.steps.create(order=1, name="課長承認", approver_role=manager_group)
workflow.steps.create(order=2, name="部長承認", approver_role=director_group)

# 残業申請オブジェクトに承認フローを追加
overtime_request = OvertimeRequest.objects.create(...)
approval = service.create_request(
    workflow=workflow,
    content_object=overtime_request,
    requester=employee,
)
```

### 例2: 3人中2人の並列承認

```python
# レビュアー3人のうち2人の承認が必要
workflow.steps.create(
    order=1,
    name="レビュアー承認",
    approver_role=reviewer_group,
    is_parallel=True,
    required_approvals=2,  # 3人中2人
)
```

### 例3: 自動承認（申請者が承認者の場合）

```python
# 課長が自分で申請した場合は課長承認ステップを自動で通過
workflow.steps.create(
    order=1,
    name="課長承認",
    approver_role=manager_group,
    auto_approve_if_requester_in_role=True,  # 自動承認を有効化
)
```

## 🧪 テスト結果

```bash
$ docker-compose run --rm django python manage.py test tests.approvals
Ran 18 tests in 4.394s
OK ✅
```

全18テスト成功（モデル11テスト + サービス7テスト）

## 📊 コード品質

- **Pylance**: 0エラー
- **Ruff**: All checks passed
- **テストカバレッジ**: モデル、サービス、承認フロー全体をカバー
- **型ヒント**: TYPE_CHECKINGパターンで循環importを回避
- **ドキュメント**: 品質基準v2.0準拠（設計判断の理由を記載）

## 🔗 関連ドキュメント

- [kits全体のREADME](../README.md)
- [kits.notifications](../notifications/README.md) - 通知機能との連携
- [kits.audit](../../../docs/kits機能概要.md) - 履歴管理との連携
- [DemoRequest](../../../kits/demos/models.py) - FSMを使った承認フロー実装例

## 💡 次のステップ

1. **[05_使い方ガイド.md](05_使い方ガイド.md)** で実例を確認
2. **管理画面で実際に操作**: `/admin/approvals/`
3. **examples.py** を実行して動作確認
4. **実際の業務に適用**: 既存のモデルに承認フローを追加

## 🆘 困ったときは

- **[06_よくある質問.md](06_よくある質問.md)** を確認
- **テストコード** (`tests/approvals/`) を参考にする
- **examples.py** の実例を確認する

---

**kits.approvals v1.0.0** - 2025-10-05 実装完了
