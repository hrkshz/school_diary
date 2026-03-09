# コスト異常検知 → ServiceNow 起票

ステータス: 予定
優先度: 中

---

## なぜやるか

- 予算超過を自動検知し、ServiceNow にインシデントとして起票する
- ITOM の Event Management → Incident Management フローの実例になる
- Phase 2 Lambda + Phase 6 ServiceNow 連携と組み合わせてデモできる

## 何をするか

- AWS Budgets で月額予算を設定（例: $15）
- 80%/100% 超過時に SNS 通知
- Lambda で正規化 → ServiceNow Table API で起票

## Terraform で追加するリソース

- `aws_budgets_budget`
- `aws_sns_topic_subscription`（Budgets → Lambda）

## コスト

無料（AWS Budgets は無料、Lambda 無料枠内）

## 備考

- Phase 2 / Phase 6 の完了後に実装するのが効率的
- 既存の Lambda 正規化パターンを再利用できる
